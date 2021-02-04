import six

import logging
import sys
from fastapi import FastAPI, Request
from starlette.requests import Request
from starlette.responses import Response
from google.rpc import code_pb2

# from opencensus.common import configuration
from opencensus.trace import (
    attributes_helper,
    execution_context,
    print_exporter,
    samplers,
)
from opencensus.trace import span as span_module
from opencensus.trace import stack_trace, status
from opencensus.trace import tracer as tracer_module
from opencensus.trace import utils
from opencensus.trace.propagation import trace_context_http_header_format

HTTP_HOST = attributes_helper.COMMON_ATTRIBUTES['HTTP_HOST']
HTTP_METHOD = attributes_helper.COMMON_ATTRIBUTES['HTTP_METHOD']
HTTP_PATH = attributes_helper.COMMON_ATTRIBUTES['HTTP_PATH']
HTTP_ROUTE = attributes_helper.COMMON_ATTRIBUTES['HTTP_ROUTE']
HTTP_URL = attributes_helper.COMMON_ATTRIBUTES['HTTP_URL']
HTTP_STATUS_CODE = attributes_helper.COMMON_ATTRIBUTES['HTTP_STATUS_CODE']

BLACKLIST_PATHS = 'BLACKLIST_PATHS'
BLACKLIST_HOSTNAMES = 'BLACKLIST_HOSTNAMES'

log = logging.getLogger(__name__)


class FastAPIMiddleware(object):
    """FastAPI middleware to automatically trace requests.
    :type app: :class: `~fastAPI.FastAPI`
    :param app: A fastAPI application.
    :type blacklist_paths: list
    :param blacklist_paths: Paths that do not trace.
    :type sampler: :class:`~opencensus.trace.samplers.base.Sampler`
    :param sampler: A sampler. It should extend from the base
                    :class:`.Sampler` type and implement
                    :meth:`.Sampler.should_sample`. Defaults to
                    :class:`.ProbabilitySampler`. Other options include
                    :class:`.AlwaysOnSampler` and :class:`.AlwaysOffSampler`.
    :type exporter: :class:`~opencensus.trace.base_exporter.exporter`
    :param exporter: An exporter. Default to
                     :class:`.PrintExporter`. The rest options are
                     :class:`.FileExporter`, :class:`.LoggingExporter` and
                     trace exporter extensions.
    :type propagator: :class: 'object'
    :param propagator: A propagator. Default to
                       :class:`.TraceContextPropagator`. The rest options
                       are :class:`.BinaryFormatPropagator`,
                       :class:`.GoogleCloudFormatPropagator` and
                       :class:`.TextFormatPropagator`.
    """

    def __init__(self, app=None, blacklist_paths=None, sampler=None,
                 exporter=None, propagator=None):
        self.app = app
        self.blacklist_paths = blacklist_paths
        self.sampler = sampler
        self.exporter = exporter
        self.propagator = propagator

        if self.app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.app = app

        # get settings from app config
        # settings = self.app.config.get('OPENCENSUS', {})
        # settings = settings.get('TRACE', {})

        if self.sampler is None:
            self.sampler = (samplers.ProbabilitySampler())
            if isinstance(self.sampler, six.string_types):
                self.sampler = configuration.load(self.sampler)

        if self.exporter is None:
            self.exporter = print_exporter.PrintExporter()
            if isinstance(self.exporter, six.string_types):
                self.exporter = configuration.load(self.exporter)

        if self.propagator is None:
            self.propagator = trace_context_http_header_format.TraceContextPropagator()
            if isinstance(self.propagator, six.string_types):
                self.propagator = configuration.load(self.propagator)

        self.blacklist_paths = self.blacklist_paths

        self.blacklist_hostnames = None
        self.setup_trace()

    def setup_trace(self):
        # Not expected to work as not attached to the app.
        self._before_request
        self._after_request

    def _before_request(self, request:Request):
        """A function to be run before each request.
        """
        # Do not trace if the url is blacklisted
        if utils.disable_tracing_url(request.host, self.blacklist_paths):
            return

        try:
            span_context = self.propagator.from_headers(request.headers)

            tracer = tracer_module.Tracer(
                span_context=span_context,
                sampler=self.sampler,
                exporter=self.exporter,
                propagator=self.propagator)

            span = tracer.start_span()
            span.span_kind = span_module.SpanKind.SERVER
            # Set the span name as the name of the current module name
            span.name = '[{}]{}'.format(
                request.method,
                request.url)



            tracer.add_attribute_to_current_span(
                attribute_key=HTTP_HOST,
                attribute_value=request.url.hostname)
            tracer.add_attribute_to_current_span(
                attribute_key=HTTP_METHOD,
                attribute_value=request.method)

            tracer.add_attribute_to_current_span(
                attribute_key=HTTP_PATH,
                attribute_value=str(request.url.path))
            tracer.add_attribute_to_current_span(
                attribute_key=HTTP_URL,
                attribute_value=str(request.url))

            # ctx_correlation_id = get_or_create_ctx().correlation_id
            # correlation_id = ctx_correlation_id if ctx_correlation_id is not None \
            #     else request.headers.get(conf.CORRELATION_ID_HEADER_NAME)
            # tracer.add_attribute_to_current_span(
            #     attribute_key=conf.CORRELATION_ID_HEADER_NAME,
            #     attribute_value=correlation_id)

            # execution_context.set_opencensus_attr(
            #     'blacklist_hostnames',
            #     self.blacklist_hostnames
            # )
        except Exception:  # pragma: NO COVER
            log.error('Failed to trace request', exc_info=True)

    def _after_request(self, response, request: Request):
        """A function to be run after each request.
        """
        # Do not trace if the url is blacklisted
        if utils.disable_tracing_url(request.url, self.blacklist_paths):
            return response

        try:
            tracer = execution_context.get_opencensus_tracer()
            url_rule = request.url_rule
            if url_rule is not None:
                tracer.add_attribute_to_current_span(
                    HTTP_ROUTE, url_rule.rule
                )
            tracer.add_attribute_to_current_span(
                HTTP_STATUS_CODE,
                response.status_code
            )
        except Exception:  # pragma: NO COVER
            log.error('Failed to trace request', exc_info=True)
        finally:
            return response

    def _teardown_request(self, exception, request: Request):
        # Do not trace if the url is blacklisted
        if utils.disable_tracing_url(request.url, self.blacklist_paths):
            return

        try:
            tracer = execution_context.get_opencensus_tracer()

            if exception is not None:
                span = execution_context.get_current_span()
                if span is not None:
                    span.status = status.Status(
                        code=code_pb2.UNKNOWN,
                        message=str(exception)
                    )
                    # try attaching the stack trace to the span, only populated
                    # if the app has 'PROPAGATE_EXCEPTIONS', 'DEBUG', or
                    # 'TESTING' enabled
                    exc_type, _, exc_traceback = sys.exc_info()
                    if exc_traceback is not None:
                        span.stack_trace = (
                            stack_trace.StackTrace.from_traceback(
                                exc_traceback
                            )
                        )

            tracer.end_span()
            tracer.finish()
        except Exception:  # pragma: NO COVER
            log.error('Failed to trace request', exc_info=True)
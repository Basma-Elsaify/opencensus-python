import six
from opencensus.trace.propagation.trace_context_http_header_format import TraceContextPropagator
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer
from opencensus.trace.span import SpanKind
from opencensus.trace.attributes_helper import COMMON_ATTRIBUTES
from opencensus.trace import print_exporter
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from opencensus.common import configuration

HTTP_HOST = COMMON_ATTRIBUTES['HTTP_HOST']
HTTP_METHOD = COMMON_ATTRIBUTES['HTTP_METHOD']
HTTP_PATH = COMMON_ATTRIBUTES['HTTP_PATH']
HTTP_URL = COMMON_ATTRIBUTES['HTTP_URL']
HTTP_STATUS_CODE = COMMON_ATTRIBUTES['HTTP_STATUS_CODE']

class FastAPIMiddleware(BaseHTTPMiddleware):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sampler = ProbabilitySampler(1)
        self.exporter = print_exporter.PrintExporter()
        self.propagator = TraceContextPropagator()


    @staticmethod
    def _before_request(request: Request, tracer):
        tracer.add_attribute_to_current_span(
            attribute_key=HTTP_URL,
            attribute_value=str(request.url))
        tracer.add_attribute_to_current_span(
            attribute_key=HTTP_HOST,
            attribute_value=request.client.host)
        tracer.add_attribute_to_current_span(
            attribute_key=HTTP_METHOD,
            attribute_value=request.method)
        tracer.add_attribute_to_current_span(
            attribute_key=HTTP_PATH,
            attribute_value=str(request.url.path))

    @staticmethod
    def _after_request(response, tracer):
        tracer.add_attribute_to_current_span(
            attribute_key=HTTP_STATUS_CODE,
            attribute_value=response.status_code)
    
    def load_config(self, settings):
        if settings.get('TRACE', {}):
            settings = settings.get('TRACE', {})

            self.sampler = (settings.get('SAMPLER', None) or self.sampler)
            if isinstance(self.sampler, six.string_types):
                self.sampler = configuration.load(self.sampler)

            self.exporter = settings.get('EXPORTER', None) or self.exporter
            if isinstance(self.exporter, six.string_types):
                self.exporter = configuration.load(self.exporter)

            self.propagator = settings.get('PROPAGATOR', None) or self.propagator
            if isinstance(self.propagator, six.string_types):
                self.propagator = configuration.load(self.propagator)


    async def dispatch(self, request: Request, call_next):
        if (request.app.extra.get('extra', {}).get('open-census-settings', {})):
            settings = request.app.extra['extra']['open-census-settings']
            self.load_config(settings=settings)

        if hasattr(request.app, 'trace_exporter'):
            self.exporter = request.app.trace_exporter

        span_context = self.propagator.from_headers(request.headers)
        tracer = Tracer(span_context=span_context, sampler=self.sampler,
                                    propagator=self.propagator, exporter=self.exporter)
        with tracer.span("main") as span:
            span.span_kind = SpanKind.SERVER

            self._before_request(request, tracer)
            response = await call_next(request)
            self._after_request(response, tracer)

        return response


import logging
import uvicorn
from fastapi import FastAPI, Request
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.ext.fastapi.fastapi_middleware import FastAPIMiddleware
# to be removed
from opencensus.trace.attributes_helper import COMMON_ATTRIBUTES
from opencensus.trace.tracer import Tracer
from opencensus.trace.span import SpanKind

app = FastAPI()

key=''
HTTP_URL = COMMON_ATTRIBUTES['HTTP_URL']
HTTP_STATUS_CODE = COMMON_ATTRIBUTES['HTTP_STATUS_CODE']

logger = logging.getLogger(__name__)
logger.addHandler(AzureLogHandler(connection_string=f'InstrumentationKey={key}')
)

# to uncomment and replace the fastAPIMiddleware function
# middleware = FastAPIMiddleware(app, exporter=AzureExporter(connection_string=f'InstrumentationKey={key}'),sampler=ProbabilitySampler(rate=1.0))

# fastapi middleware for opencensus
@app.middleware("http")
async def fastAPIMiddleware(request: Request, call_next):
    tracer = Tracer(exporter=AzureExporter(connection_string=f'InstrumentationKey={key}'),sampler=ProbabilitySampler(1.0))
    with tracer.span("main") as span:
        span.span_kind = SpanKind.SERVER

        response = await call_next(request)

        tracer.add_attribute_to_current_span(
            attribute_key=HTTP_STATUS_CODE,
            attribute_value=response.status_code)
        tracer.add_attribute_to_current_span(
            attribute_key=HTTP_URL,
            attribute_value=str(request.url))

    return response


@app.get("/")
async def root(request:Request):
    return {"message": request.client.host}

@app.get("/testlog")
async def testlog(request:Request):
    logger.error("Test page")
    return {"message": request.url}

if __name__=="__main__":
    uvicorn.run("test:app", port=8081)









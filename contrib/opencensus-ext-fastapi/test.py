# Copyright 2017, OpenCensus Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from opencensus.ext.fastapi.fastapi_middleware import FastAPIMiddleware
import logging
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer
from opencensus.trace import config_integration
import uvicorn
from fastapi import FastAPI, Request


app = FastAPI()

key='instrumentationkeyvalue'

logger = logging.getLogger(__name__)
logger.addHandler(AzureLogHandler(
    connection_string=f'InstrumentationKey={key}')
)

middleware = FastAPIMiddleware(app, exporter=AzureExporter(connection_string=f'InstrumentationKey={key}'),sampler=ProbabilitySampler(rate=1.0))


@app.get("/")
async def root(request:Request):
    return {"message": request.client.host}

@app.get("/testlog")
async def testlog(request:Request):
    logger.error("Test page")
    return {"message": request.url}

if __name__=="__main__":
    uvicorn.run("test:app", port=8081)









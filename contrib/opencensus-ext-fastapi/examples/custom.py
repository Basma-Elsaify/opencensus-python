import os

from fastapi import FastAPI, Request
import grpc
import mysql.connector
import psycopg2
import requests
import uvicorn
import hello_world_pb2
import hello_world_pb2_grpc
from opencensus.ext.fastapi.fastapi_middleware import FastAPIMiddleware
from opencensus.ext.grpc import client_interceptor
from opencensus.ext.stackdriver import trace_exporter as stackdriver_exporter
from opencensus.trace import config_integration, samplers
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.samplers import ProbabilitySampler

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    app.trace_exporter = AzureExporter(connection_string=f'InstrumentationKey=<InstrumentationKey>')

app.add_middleware(FastAPIMiddleware)

@app.get("/")
async def root():
    return "Hello World!"

@app.get("/items/{item_id}")
async def read_root(item_id: str, request: Request):
    client_host = request.client.host
    return {"client_host": client_host, "item_id": item_id}

@app.post("/name/")
async def send_name(name: str):
    return {'name': name}

if __name__ == '__main__':
    uvicorn.run("custom:app", host="127.0.0.1", port=8888, log_level="info")

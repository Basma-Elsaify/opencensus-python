import logging
from opencensus.ext.fastapi.fastapi_middleware import FastAPIMiddleware
import uvicorn
from fastapi import FastAPI

app = FastAPI()

app.add_middleware(FastAPIMiddleware)

@app.get("/")
async def root():
    return "Hello World!"

if __name__ == '__main__':
    logger = logging.getLogger('werkzeug')
    logger.setLevel(logging.ERROR)
    uvicorn.run("simple:app", host="127.0.0.1", port=8888, log_level="info")
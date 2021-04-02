NOT TO USE YET:: OpenCensus FastAPI Integration || this is still in development, can't be used yet
==================================================================================================

|pypi|

.. |pypi| image:: https://pypi.org/project/pipprojectpkg/
   :target: https://pypi.org/project/pipprojectpkg/

Installation
------------

::

    pip install pipprojectpkg

Usage
-----

.. code:: python

   from opencensus.ext.azure.trace_exporter import AzureExporter
   from opencensus.trace.samplers import ProbabilitySampler
   from fastAPIMiddleware import FastAPIMiddleware
   import uvicorn
   from fastapi import FastAPI, Request

   app = FastAPI()

   @app.on_event("startup")
   async def startup_event():
        app.trace_exporter = AzureExporter(connection_string=f'instrumentation-key=<INSTRUMENTATION-KEY>')

   app.add_middleware(FastAPIMiddleware)

   @app.get("/")
   async def root(request:Request):
       return {"message": request.client.host}


   if __name__=="__main__":
       uvicorn.run("fastAPISample:app", port=8888, reload=True, debug=True, workers=3)


Additional configuration can be provided, please read
`Customization <https://github.com/census-instrumentation/opencensus-python#customization>`_
for a complete reference.

.. code:: python

    settings = {"open-census-settings":
        {
            'TRACE': {
                'SAMPLER': 'opencensus.trace.samplers.ProbabilitySampler(rate=1)',
                'EXPORTER': "opencensus.ext.azure.trace_exporter.AzureExporter(connection_string=f'InstrumentationKey=<INSTRUMENTATION-KEY>')"
            }
        }
    }
    
    app = FastAPI(extra=settings)

References
----------

* `OpenCensus Project <https://opencensus.io/>`_

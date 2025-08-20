
from fastapi import FastAPI
from routes.report_routes import report_router
from bullmq import Queue


app = FastAPI()

app.include_router(report_router)



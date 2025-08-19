from typing import Union
from fastapi import FastAPI
from contextlib import asynccontextmanager
from lib.prisma import PrismaClient
from lib.celery import Celery
from routes.report_routes import report_router


prisma=PrismaClient()




app = FastAPI()

app.include_router(report_router)

@app.get("/health")
async def read_root():
    return {"Hello": "World"}



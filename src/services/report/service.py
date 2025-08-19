from lib.prisma import PrismaClient
from lib.celery import celery
async def generate_report():
    prisma=PrismaClient()
    await prisma.connect()
    
    celery.send_task("generate_report_task", args=["data ot worker"])
    
    await prisma.disconnect()


    return {"message":"Task added to queue"}
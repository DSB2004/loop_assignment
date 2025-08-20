from lib.prisma import PrismaClient
from bullmq import Queue


async def generate_report(store_id: str):
    prisma = PrismaClient()
    queue = Queue("report")
    try:
        await prisma.connect()
        report=await prisma.db.reports.create(data={
            "storeId":store_id,
        })
        await queue.add("generate-report", { "store_id": store_id,"report_id":report.id })
        await queue.close()
        return {"message": f"Trigger report for {store_id}", "report_id": report.id, "status": 202}
    finally:
        if prisma._connected:
            await prisma.disconnect()

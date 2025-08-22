from lib.prisma import PrismaClient
from bullmq import Queue
from fastapi.responses import FileResponse


async def generate_report(store_id: str):
    prisma = PrismaClient()
    queue = Queue("report")
    try:
        await prisma.connect()
        report=await prisma.db.reports.create(data={
            "storeId":store_id,
        })
        await queue.add("generate-report", { "store_id": store_id,"report_id":report.id })
        return {"message": f"Trigger report for {store_id}", "report_id": report.id, "status": 202}
    except Exception:
        return {"message":"Internal Server Error","status":500}
    finally:
        await queue.close()
        if prisma._connected:
            await prisma.disconnect()


async def get_report(report_id:str):
    prisma=PrismaClient()
    try:
        await prisma.connect()
        report=await prisma.db.reports.find_unique(where={
            "id":report_id
        })
        if report is None:
            return {"message":f"Report {report_id} not found","status":404}
        if report.status=="PENDING":
            return {"message":f"Report {report_id} in progress","status":200}
        if report.status=="FAILED":
            return {"message":f"Report {report_id} failed to generate","status":200}
        
        filename=report.report
        return FileResponse(
            path=f"./reports/{filename}",
            filename=filename,  
            media_type="application/csv"
        )

    except Exception:
        return {"message":"Internal Server Error","status":500}
    finally:
        if prisma._connected:
            await prisma.disconnect()
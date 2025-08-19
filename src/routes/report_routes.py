from fastapi  import APIRouter
from services.report import service
from pydantic import BaseModel

report_router = APIRouter(prefix="/reports", tags=["Reports"])

class TriggerReportDto(BaseModel):
    store_id:str

class GetReportDto(BaseModel):
    report_id:str

@report_router.get("/health")
async def health():
    return await service.generate_report()
    

@report_router.post('/trigger_report')
async def trigger_report(dto:TriggerReportDto):
    store_id=dto.store_id
    return {"message":f"Trigger report for {store_id}","status":204}



@report_router.post('/get_report')
async def get_report(dto:GetReportDto):
    report_id=dto.report_id
    return {"message":f"Get report for {report_id}","status":204}


# celery -A src.lib.celery.celery worker --loglevel=info -P solo
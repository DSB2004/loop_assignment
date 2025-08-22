from fastapi  import APIRouter
from services.report import service
from pydantic import BaseModel

report_router = APIRouter(prefix="/reports", tags=["Reports"])

class TriggerReportDto(BaseModel):
    store_id:str

class GetReportDto(BaseModel):
    report_id:str

@report_router.get("/health")
def health():
    return {"message":"working fine"}
    

@report_router.post('/trigger_report')
async def trigger_report(dto:TriggerReportDto):
    store_id=dto.store_id
    return await service.generate_report(store_id)
   

@report_router.post('/get_report')
async def get_report(dto:GetReportDto):
    report_id=dto.report_id
    return await service.get_report(report_id)


# celery -A src.lib.celery.celery worker --loglevel=info -P solo
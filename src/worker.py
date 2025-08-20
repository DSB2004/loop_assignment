from bullmq import Worker
import asyncio
from prisma import Prisma
from config.config import redis_url
from tasks.generate_report import generate_report_task

db=Prisma()


async def process(job, job_token):
    print("job received",job.data)
    await generate_report_task(store_id=job.data['store_id'])
    
async def main():
    shutdown_event = asyncio.Event()
    worker = Worker("report", process, {"connection":redis_url})
    print("Worker is ready to process jobs...")
    await shutdown_event.wait()
    print("Cleaning up worker...")
    await worker.close()

if __name__ == "__main__":
    asyncio.run(main())
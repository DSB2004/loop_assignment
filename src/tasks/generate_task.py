from src.lib.celery import celery


@celery.task(name="generate_report_task")
def generate_task(store_id):
    print(store_id)
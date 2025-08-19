from celery import Celery


celery = Celery(
    "worker",
    broker="redis://localhost:6379/0",   # Redis as broker
    backend="redis://localhost:6379/1"   # Optional result backend
)



import src.tasks.generate_task 
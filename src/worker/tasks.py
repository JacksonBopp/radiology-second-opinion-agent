import os

from celery import Celery

from src.ingestion.pipeline import process_scan_bytes

BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", BROKER_URL)

celery_app = Celery("radiology_worker", broker=BROKER_URL, backend=RESULT_BACKEND)


@celery_app.task(name="process_scan")
def process_scan(filename: str, content: bytes) -> dict:
    return process_scan_bytes(filename, content)

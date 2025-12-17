"""Celery application configuration."""
from dotenv import load_dotenv
from celery import Celery

# Load environment variables from a local `.env` file (if present).
# This makes OPENAI_API_KEY available to the worker when started via:
#   celery -A app.celery_app worker --loglevel=info
load_dotenv()

# Create Celery instance
celery_app = Celery(
    "image_processor",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    # Ensure task modules are imported when the worker starts via:
    #   celery -A app.celery_app worker --loglevel=info
    include=["app.worker"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


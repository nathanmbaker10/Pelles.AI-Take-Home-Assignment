"""Celery worker tasks for image processing."""
import os
import uuid
import base64
import mimetypes
from typing import Optional
from PIL import Image
from openai import OpenAI
from app.celery_app import celery_app
from app.storage import storage
from app.models import JobStatus


def _generate_mock_description(image_path: str) -> str:
    """
    Generate a textual description of an image (fallback).
    
    This is a mock implementation. In production, this would call
    an external vision API (e.g., OpenAI Vision, Google Vision API, etc.)
    or use a trained model.
    """
    try:
        # Load image to get basic metadata
        img = Image.open(image_path)
        width, height = img.size
        format_name = img.format or "Unknown"
        mode = img.mode
        
        # Generate a mock description based on image properties
        # In a real system, this would be replaced with actual vision API calls
        description = f"""Image Description:
- Dimensions: {width}x{height} pixels
- Format: {format_name}
- Color Mode: {mode}
- Content: This appears to be a {format_name.lower()} image with dimensions {width}x{height}.
  The image uses {mode} color mode.

_generated_by: "vision-node-gpt"
"""
        return description
    except Exception as e:
        raise Exception(f"Failed to process image: {str(e)}")


def _describe_with_openai(image_path: str) -> Optional[str]:
    """
    Generate an AI image description using OpenAI Vision.

    Returns None if OPENAI_API_KEY is not set.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    model = os.getenv("OPENAI_VISION_MODEL", "gpt-4o-mini")

    mime_type, _ = mimetypes.guess_type(image_path)
    mime_type = mime_type or "image/jpeg"

    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    data_url = f"data:{mime_type};base64,{b64}"

    client = OpenAI(api_key=api_key)

    prompt = (
        "You are an image captioning system. "
        "Write a clear description of the image."
    )

    # Use Chat Completions API for broad SDK compatibility across OpenAI python 1.x.
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ],
    )

    text = (resp.choices[0].message.content or "").strip()
    return text or None


def generate_image_description(image_path: str) -> str:
    """
    Generate a textual description of an image using AI (preferred), with a fallback.
    """
    ai_text = _describe_with_openai(image_path)
    if ai_text:
        return ai_text
    return _generate_mock_description(image_path)


@celery_app.task(bind=True, name="process_image")
def process_image_task(self, job_id: str, image_path: str):
    """
    Celery task to process an image and generate description.
    
    Args:
        job_id: Unique identifier for the job
        image_path: Path to the uploaded image file
    """
    try:
        # Update status to processing
        storage.update_job_status(job_id, JobStatus.PROCESSING)
        
        # Generate description
        description = generate_image_description(image_path)
        
        # Update job with result
        storage.update_job_status(job_id, JobStatus.DONE, description=description)
        
        # Clean up temporary file
        if os.path.exists(image_path):
            os.remove(image_path)
        
        return {"status": "success", "job_id": job_id}
    except Exception as e:
        # Update job with error
        error_msg = str(e)
        storage.update_job_status(job_id, JobStatus.FAILED, error=error_msg)
        
        # Clean up temporary file even on error
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
            except:
                pass
        
        # Re-raise to mark task as failed
        raise


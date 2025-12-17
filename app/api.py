"""FastAPI application with image processing endpoints."""
import os
import uuid
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.storage import storage
from app.models import JobStatus
from app.worker import process_image_task

app = FastAPI(title="Image Processing API", version="1.0.0")

# Directory to store uploaded images temporarily
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Serve lightweight frontend UI (static HTML/JS/CSS).
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/ui")
async def ui():
    """Serve the web UI."""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    return FileResponse(index_path)


@app.post("/submit", response_model=dict)
async def submit_image(file: UploadFile = File(...)):
    """
    Submit an image for processing.
    
    Accepts PNG or JPG images and returns a job_id.
    """
    # Validate file type.
    #
    # Note: some HTTP clients (including `requests` when given a bare file object)
    # default to `application/octet-stream`, so we validate via both MIME type and
    # filename extension.
    allowed_content_types = {"image/png", "image/jpeg", "image/jpg"}
    allowed_extensions = {"png", "jpg", "jpeg"}

    filename = (file.filename or "").strip()
    file_extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    content_type_ok = bool(file.content_type) and file.content_type.lower() in allowed_content_types
    extension_ok = file_extension in allowed_extensions

    if not (content_type_ok or extension_ok):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only PNG and JPG/JPEG images are supported.",
        )
    
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # Save uploaded file temporarily
    if file_extension == "jpeg":
        file_extension = "jpg"
    if not file_extension:
        file_extension = "jpg"
    file_path = os.path.join(UPLOAD_DIR, f"{job_id}.{file_extension}")
    
    try:
        # Save file
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Create job record
        storage.create_job(job_id)
        
        # Queue the processing task
        process_image_task.delay(job_id, file_path)
        
        return {"job_id": job_id, "status": "queued"}
    except Exception as e:
        # Clean up file if job creation failed
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Failed to submit job: {str(e)}")


@app.get("/status/{job_id}", response_model=dict)
async def get_job_status(job_id: str):
    """
    Get the current status of a job.
    
    Returns: queued, processing, done, or failed
    """
    job = storage.get_job(job_id)
    
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    
    response = {
        "job_id": job.job_id,
        "status": job.status.value
    }
    
    if job.error:
        response["error"] = job.error
    
    return response


@app.get("/result/{job_id}", response_model=dict)
async def get_job_result(job_id: str):
    """
    Get the final image description once the job is complete.
    
    Returns the description text if job is done, otherwise returns an error.
    """
    job = storage.get_job(job_id)
    
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status == JobStatus.DONE:
        return {
            "job_id": job.job_id,
            "status": job.status.value,
            "description": job.description
        }
    elif job.status == JobStatus.FAILED:
        raise HTTPException(
            status_code=400,
            detail=f"Job failed: {job.error or 'Unknown error'}"
        )
    else:
        raise HTTPException(
            status_code=202,
            detail=f"Job is still {job.status.value}. Please check /status/{job_id} for updates."
        )


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Image Processing API",
        "version": "1.0.0",
        "endpoints": {
            "POST /submit": "Submit an image for processing",
            "GET /status/{job_id}": "Get job status",
            "GET /result/{job_id}": "Get job result"
        }
    }


# Image Processing API

A scalable and decoupled backend system for processing images and generating textual descriptions. The system uses FastAPI for the REST API, Celery for asynchronous task processing, and Redis as the message broker.

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────────┐
│   FastAPI API   │
│  (Port 8000)    │
└──────┬──────────┘
       │
       ├──► SQLite (Job Storage)
       │
       └──► Redis Queue
              │
              ▼
       ┌──────────────┐
       │ Celery Worker│
       │ (Image Proc) │
       └──────────────┘
```

### Components

1. **API Server (FastAPI)**: Handles HTTP requests, manages job submission and retrieval
2. **Job Storage (SQLite)**: Tracks job status, results, and errors
3. **Message Queue (Redis)**: Distributes tasks to workers
4. **Worker (Celery)**: Processes images asynchronously and generates descriptions

## Features

- ✅ Submit images via REST API
- ✅ Asynchronous job processing with Celery
- ✅ Job status tracking (queued, processing, done, failed)
- ✅ Result retrieval with image descriptions
- ✅ Docker support for easy deployment

## API Endpoints

### POST `/submit`
Submit an image for processing.

**Request:**
```bash
curl -X POST "http://localhost:8000/submit" \
  -F "file=@image.jpg"
```

**Response:**
```json
{
  "job_id": "uuid-here",
  "status": "queued"
}
```

### GET `/status/{job_id}`
Get the current status of a job.

**Response:**
```json
{
  "job_id": "uuid-here",
  "status": "processing"
}
```

### GET `/result/{job_id}`
Get the final image description (only when job is done).

**Response:**
```json
{
  "job_id": "uuid-here",
  "status": "done",
  "description": "Image Description:\n- Dimensions: 1920x1080 pixels\n..."
}
```

## Web UI

A lightweight frontend is included for manual testing:

- Open **`/ui`** in your browser (e.g. `http://localhost:8000/ui`)
- Upload an image to create a job, then the UI will poll status and display the result

## Setup Instructions

### Prerequisites
- Python 3.11+
- Redis (or use Docker Compose)

### Optional: Enable AI Image Descriptions (OpenAI Vision)

Set an OpenAI API key to enable AI-generated descriptions:

```bash
export OPENAI_API_KEY="your_key_here"
export OPENAI_VISION_MODEL="gpt-4o-mini"   # optional override
```

You can also set these via a project-level `.env` **file** in the repo root (auto-loaded on both API/worker startup via `python-dotenv`):

```bash
OPENAI_API_KEY="your_key_here"
OPENAI_VISION_MODEL="gpt-4o-mini"
```

Restart the API server and Celery worker after editing `.env`.

### Local Development

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Start Redis:**
```bash
# Using Docker Compose (recommended)
docker compose up -d

# Or install Redis locally and start it
redis-server
```

3. **Start the API server:**
```bash
python main.py
# Or: uvicorn app.api:app --reload
```

4. **Start the Celery worker (in a separate terminal):**
```bash
celery -A app.celery_app worker --loglevel=info
```

### Docker Setup

1. **Build and start services:**
```bash
docker compose up -d redis
docker build -t image-processor .
docker run -p 8000:8000 --network host image-processor
```

2. **Start worker in another container:**
```bash
docker run --network host image-processor celery -A app.celery_app worker --loglevel=info
```

## Testing

### Using the Test Client

```bash
python test_client.py path/to/image.jpg
```

### Using curl

1. **Submit an image:**
```bash
curl -X POST "http://localhost:8000/submit" \
  -F "file=@sample_image.jpg"
```

2. **Check status:**
```bash
curl "http://localhost:8000/status/{job_id}"
```

3. **Get result:**
```bash
curl "http://localhost:8000/result/{job_id}"
```

### Using Python requests

```python
import requests

# Submit
with open("image.jpg", "rb") as f:
    response = requests.post("http://localhost:8000/submit", files={"file": f})
    job_id = response.json()["job_id"]

# Check status
status = requests.get(f"http://localhost:8000/status/{job_id}").json()

# Get result
result = requests.get(f"http://localhost:8000/result/{job_id}").json()
```

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── api.py           # FastAPI endpoints
│   ├── worker.py        # Celery tasks
│   ├── celery_app.py    # Celery configuration
│   ├── models.py        # Data models
│   └── storage.py       # Job storage (SQLite)
├── main.py              # Application entry point
├── test_client.py       # Test client script
├── requirements.txt     # Python dependencies
├── docker-compose.yml   # Docker Compose config
├── Dockerfile          # Docker image definition
└── README.md           # This file
```

## Job Status Flow

1. **queued**: Job created and added to queue
2. **processing**: Worker is processing the image
3. **done**: Processing complete, description available
4. **failed**: Processing failed, error message available

## Image Processing

The implementation supports AI-generated descriptions via OpenAI Vision (when `OPENAI_API_KEY` is set). If not set, it falls back to a mock description generator that extracts basic metadata (dimensions, format, color mode). In production, this could be replaced with:

- OpenAI GPT-4 Vision API
- Google Cloud Vision API
- AWS Rekognition
- Custom trained models

The description includes a `_generated_by: "vision-node-gpt"` field as specified.

## Scaling Considerations

### Horizontal Scaling
- **API Servers**: Multiple FastAPI instances behind a load balancer
- **Workers**: Multiple Celery workers can process jobs in parallel
- **Redis**: Redis Cluster for high availability

### Production Enhancements
- Replace SQLite with PostgreSQL for better concurrency
- Add authentication/authorization
- Implement rate limiting
- Add monitoring and logging (e.g., Prometheus, Grafana)
- Use object storage (S3) for image persistence
- Add retry logic and dead letter queues
- Implement job expiration/cleanup

## License

This is a take-home assignment implementation.


# Quick Start Guide

## Prerequisites
- Python 3.11+
- Docker (for Redis) or Redis installed locally

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Start Redis

**Option A: Using Docker Compose (Recommended)**
```bash
# Make sure Docker Desktop is running first
docker compose up -d redis
```

**Option B: Local Redis**
```bash
# macOS
brew install redis
brew services start redis

# Linux
sudo apt-get install redis-server
sudo systemctl start redis
```

## Step 3: Start the API Server

In Terminal 1:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## Optional: Enable AI Image Descriptions (OpenAI Vision)

If you want AI-generated descriptions, set environment variables (either via your shell or a local `.env` **file**).
This project auto-loads a root `.env` file on both **API** and **worker** startup (via `python-dotenv`).

### Option A: `.env` file (recommended)

Create a file named `.env` in the project root:

```bash
OPENAI_API_KEY="your_key_here"
OPENAI_VISION_MODEL="gpt-4o-mini"
```

Then restart the API + worker so the new environment variables are picked up.

### Option B: Shell environment variables

Export in your terminal:

```bash
export OPENAI_API_KEY="your_key_here"
export OPENAI_VISION_MODEL="gpt-4o-mini"   # optional override
```

## Step 4: Start the Celery Worker

In Terminal 2:
```bash
celery -A app.celery_app worker --loglevel=info
```

You should see output like:
```
[tasks]
  . process_image
```

## Step 5: Test the System

### Option A: Web UI

Open `http://localhost:8000/ui` and upload an image. The UI will automatically poll status and show the final description.

### Using the Test Client

```bash
python test_client.py path/to/your/image.jpg
```

### Using curl

1. **Submit an image:**
```bash
curl -X POST "http://localhost:8000/submit" \
  -F "file=@your_image.jpg"
```

Response:
```json
{"job_id": "abc-123-def-456", "status": "queued"}
```

2. **Check status:**
```bash
curl "http://localhost:8000/status/abc-123-def-456"
```

3. **Get result (wait until status is "done"):**
```bash
curl "http://localhost:8000/result/abc-123-def-456"
```

### Using Python

```python
import requests
import time

# Submit image
with open("image.jpg", "rb") as f:
    response = requests.post("http://localhost:8000/submit", files={"file": f})
    job_id = response.json()["job_id"]
    print(f"Job ID: {job_id}")

# Poll for completion
while True:
    status_response = requests.get(f"http://localhost:8000/status/{job_id}")
    status = status_response.json()["status"]
    print(f"Status: {status}")
    
    if status == "done":
        result = requests.get(f"http://localhost:8000/result/{job_id}")
        print(result.json()["description"])
        break
    elif status == "failed":
        print("Job failed!")
        break
    
    time.sleep(1)
```

## Troubleshooting

### Redis Connection Error
- Make sure Docker Desktop is running (if using Docker)
- Make sure Redis is running: `redis-cli ping` should return `PONG`
- Check Redis is on port 6379: `redis-cli -p 6379 ping`

### Worker Not Processing Jobs
- Verify worker is connected to Redis
- Check worker logs for errors
- Ensure worker shows the `process_image` task in its task list

### API Not Starting
- Check port 8000 is not in use
- Verify all dependencies are installed: `pip list`

## Next Steps

- Replace the mock image description generator in `app/worker.py` with a real vision API
- Add authentication and rate limiting
- Scale horizontally by adding more workers
- Migrate from SQLite to PostgreSQL for production


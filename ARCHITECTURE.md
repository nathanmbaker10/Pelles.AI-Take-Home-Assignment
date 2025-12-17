# System Architecture

## High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         CLIENT                               │
│             (Web UI, curl, Postman, Python)                  │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    FASTAPI API SERVER                       │
│                      (Port 8000)                            │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ POST     │  │ GET      │  │ GET      │  │ GET      │    │
│  │ /submit  │  │ /status  │  │ /result  │  │ /ui      │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘    │
│       │             │            │             │            │
│       └─────────────┴────────────┴─────────────┘            │
│                         │                                    │
└─────────────────────────┼────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   SQLite     │  │    Redis     │  │  File System │
│   Database   │  │    Queue     │  │  (uploads/)  │
│              │  │              │  │              │
│  Job Storage │  │  Task Queue  │  │  Temp Images │
└──────────────┘  └──────┬───────┘  └──────────────┘
                         │
                         │ Task Distribution
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    CELERY WORKER                            │
│              (Separate Process/Container)                   │
│                                                              │
│  1. Retrieve image from file path                           │
│  2. Process image (generate description)                    │
│  3. Update job status in SQLite                             │
│  4. Store result with _generated_by field                   │
│  5. Clean up temporary files                                │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. API Layer (FastAPI)
- **Purpose**: HTTP interface for clients
- **Responsibilities**:
  - Accept image uploads
  - Generate unique job IDs
  - Queue tasks to Redis
  - Retrieve job status and results
  - Serve the lightweight web UI (`/ui`) and static assets (`/static/*`)
  - Validate file types (PNG/JPG/JPEG)

### 1a. Web UI (Static HTML/JS/CSS)
- **Purpose**: Simple manual testing interface (no build tooling)
- **How it works**:
  - Uploads images to `POST /submit`
  - Polls `GET /status/{job_id}` until done/failed
  - Fetches the final description from `GET /result/{job_id}`

### 2. Job Storage (SQLite)
- **Purpose**: Persistent job state tracking
- **Schema**:
  - `job_id` (PRIMARY KEY)
  - `status` (queued, processing, done, failed)
  - `description` (text result)
  - `error` (error message if failed)
  - `created_at`, `updated_at` (timestamps)

### 3. Message Queue (Redis)
- **Purpose**: Decouple API from processing
- **Benefits**:
  - Async processing
  - Horizontal scaling of workers
  - Fault tolerance
  - Task retry capability

### 4. Worker (Celery)
- **Purpose**: Process images asynchronously
- **Workflow**:
  1. Receive task with job_id and image path
  2. Update status to "processing"
  3. Generate image description (AI via OpenAI Vision when enabled; otherwise fallback)
  4. Update status to "done" with result
  5. Clean up temporary files

#### AI Description Generation (OpenAI Vision)
- **Configuration**:
  - `OPENAI_API_KEY`: enables AI-generated descriptions
  - `OPENAI_VISION_MODEL` (optional): defaults to `gpt-4o-mini`
- **Loading**: environment variables are auto-loaded from a project-root `.env` file via `python-dotenv` for both the API process and worker process.

## Data Flow

### Job Submission Flow
```
Client → API → Create Job (SQLite) → Queue Task (Redis) → Return job_id
```

### Processing Flow
```
Worker ← Redis Queue ← Task Available
Worker → Update Status (processing)
Worker → Process Image → Generate Description
Worker → Update Status (done) + Store Result
Worker → Cleanup Files
```

### Result Retrieval Flow
```
Client → API → Query SQLite → Return Status/Result
```

## Scaling Strategy

### Vertical Scaling
- Increase worker resources (CPU, memory)
- Use more powerful image processing models

### Horizontal Scaling
- **API Servers**: Multiple FastAPI instances behind load balancer
- **Workers**: Multiple Celery workers processing in parallel
- **Redis**: Redis Cluster for high availability
- **Database**: Migrate to PostgreSQL for better concurrency

### Production Enhancements
1. **Storage**: Move from SQLite to PostgreSQL
2. **File Storage**: Use S3/cloud storage instead of local filesystem
3. **Monitoring**: Add Prometheus metrics, logging
4. **Security**: Authentication, rate limiting, input validation
5. **Resilience**: Retry logic, dead letter queues, circuit breakers

## Technology Choices

- **FastAPI**: Modern, fast, async-capable Python web framework
- **Celery**: Mature, battle-tested distributed task queue
- **Redis**: Fast, in-memory data store perfect for queues
- **SQLite**: Simple, file-based database (easy to migrate to PostgreSQL)
- **Pillow**: Python imaging library for basic image operations
- **OpenAI SDK**: Vision-capable model for generating natural language image descriptions
- **python-dotenv**: Local `.env` support for configuration without exporting shell variables


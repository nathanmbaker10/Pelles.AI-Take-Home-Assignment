"""Main entry point for the FastAPI application."""
import uvicorn
from dotenv import load_dotenv

if __name__ == "__main__":
    # Load environment variables from a local `.env` file (if present).
    load_dotenv()
    uvicorn.run("app.api:app", host="0.0.0.0", port=8000, reload=True)


"""Test client script for the Image Processing API."""
import requests
import time
import sys

API_BASE_URL = "http://localhost:8000"


def submit_image(image_path: str):
    """Submit an image for processing."""
    print(f"\n📤 Submitting image: {image_path}")
    
    with open(image_path, "rb") as f:
        files = {"file": f}
        response = requests.post(f"{API_BASE_URL}/submit", files=files)
    
    if response.status_code == 200:
        data = response.json()
        job_id = data["job_id"]
        print(f"✅ Job submitted successfully!")
        print(f"   Job ID: {job_id}")
        return job_id
    else:
        print(f"❌ Error submitting job: {response.text}")
        return None


def check_status(job_id: str):
    """Check the status of a job."""
    response = requests.get(f"{API_BASE_URL}/status/{job_id}")
    
    if response.status_code == 200:
        data = response.json()
        return data["status"]
    else:
        print(f"❌ Error checking status: {response.text}")
        return None


def get_result(job_id: str):
    """Get the result of a completed job."""
    response = requests.get(f"{API_BASE_URL}/result/{job_id}")
    
    if response.status_code == 200:
        data = response.json()
        return data["description"]
    else:
        print(f"❌ Error getting result: {response.text}")
        return None


def main():
    """Main test function."""
    if len(sys.argv) < 2:
        print("Usage: python test_client.py <image_path>")
        print("Example: python test_client.py sample_image.jpg")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    # Submit image
    job_id = submit_image(image_path)
    if not job_id:
        sys.exit(1)
    
    # Poll for status
    print(f"\n⏳ Waiting for job to complete...")
    max_wait = 60  # Maximum wait time in seconds
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        status = check_status(job_id)
        
        if status == "done":
            print(f"✅ Job completed!")
            break
        elif status == "failed":
            print(f"❌ Job failed!")
            break
        elif status:
            print(f"   Status: {status}")
        
        time.sleep(1)
    else:
        print(f"⏱️  Timeout waiting for job to complete")
        sys.exit(1)
    
    # Get result
    if status == "done":
        print(f"\n📄 Fetching result...")
        description = get_result(job_id)
        if description:
            print(f"\n{'='*60}")
            print("IMAGE DESCRIPTION:")
            print(f"{'='*60}")
            print(description)
            print(f"{'='*60}\n")


if __name__ == "__main__":
    main()


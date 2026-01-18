from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Security
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
import uuid
import os
import asyncio
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app initialization
app = FastAPI(
    title="Zuke Video Shorts Creator API",
    description="AI-powered YouTube Shorts generator with Azure integration",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key authentication
API_KEY_NAME = os.getenv("API_KEY_HEADER", "X-API-Key")
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key: str = Security(api_key_header)):
    expected_key = os.getenv("API_KEY")
    if not expected_key:
        return True  # No API key configured, allow all requests
    if api_key == expected_key:
        return api_key
    raise HTTPException(status_code=401, detail="Invalid API key")

# Pydantic models
class VideoProcessingRequest(BaseModel):
    youtube_url: Optional[HttpUrl] = None
    video_file_url: Optional[HttpUrl] = None
    num_clips: int = 3
    output_types: List[str] = ["subtitled"]  # original, original-dimension, subtitled, original-subtitled
    auto_approve: bool = False
    webhook_url: Optional[HttpUrl] = None
    job_id: Optional[str] = None

class JobStatus(BaseModel):
    job_id: str
    status: str  # pending, processing, completed, failed
    progress: int  # 0-100
    message: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    output_urls: List[str] = []
    error_message: Optional[str] = None

class WebhookPayload(BaseModel):
    job_id: str
    status: str
    progress: int
    message: str
    output_urls: List[str] = []
    error_message: Optional[str] = None

# In-memory job storage (replace with database in production)
jobs: Dict[str, JobStatus] = {}

# Routes
@app.get("/")
async def root():
    return {
        "message": "Zuke Video Shorts Creator API",
        "version": "1.0.0",
        "endpoints": {
            "process": "/process",
            "status": "/status/{job_id}",
            "jobs": "/jobs",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "active_jobs": len([j for j in jobs.values() if j.status in ["pending", "processing"]])
    }

@app.post("/process")
async def process_video(
    request: VideoProcessingRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(get_api_key)
):
    """
    Process a video to generate YouTube Shorts
    """
    # Validate input
    if not request.youtube_url and not request.video_file_url:
        raise HTTPException(
            status_code=400,
            detail="Either youtube_url or video_file_url must be provided"
        )
    
    # Generate job ID
    job_id = request.job_id or str(uuid.uuid4())
    
    # Create job status
    job_status = JobStatus(
        job_id=job_id,
        status="pending",
        progress=0,
        message="Job queued for processing",
        created_at=datetime.utcnow()
    )
    jobs[job_id] = job_status
    
    # Add job to background processing queue
    background_tasks.add_task(
        process_video_background,
        job_id,
        request
    )
    
    logger.info(f"Job {job_id} queued for processing")
    
    return {
        "job_id": job_id,
        "status": "pending",
        "message": "Job queued successfully"
    }

@app.get("/status/{job_id}")
async def get_job_status(job_id: str, api_key: str = Depends(get_api_key)):
    """
    Get the status of a processing job
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return jobs[job_id]

@app.get("/jobs")
async def list_jobs(
    status: Optional[str] = None,
    limit: int = 100,
    api_key: str = Depends(get_api_key)
):
    """
    List all jobs with optional filtering
    """
    filtered_jobs = list(jobs.values())
    
    if status:
        filtered_jobs = [j for j in filtered_jobs if j.status == status]
    
    # Sort by creation time (newest first)
    filtered_jobs.sort(key=lambda x: x.created_at, reverse=True)
    
    return {
        "jobs": filtered_jobs[:limit],
        "total": len(filtered_jobs)
    }

@app.delete("/jobs/{job_id}")
async def cancel_job(job_id: str, api_key: str = Depends(get_api_key)):
    """
    Cancel a processing job
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    if job.status in ["completed", "failed"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel job with status: {job.status}"
        )
    
    job.status = "cancelled"
    job.message = "Job cancelled by user"
    
    return {"message": f"Job {job_id} cancelled successfully"}

# n8n webhook endpoint
@app.post("/webhook/n8n")
async def n8n_webhook(
    request: VideoProcessingRequest,
    background_tasks: BackgroundTasks
):
    """
    Special endpoint for n8n integration with simplified authentication
    """
    # Validate webhook secret if configured
    webhook_secret = os.getenv("WEBHOOK_SECRET")
    # In a real implementation, you'd validate the webhook secret from headers
    
    return await process_video(request, background_tasks, api_key=None)

async def process_video_background(job_id: str, request: VideoProcessingRequest):
    """
    Background task to process video
    """
    try:
        job = jobs[job_id]
        job.status = "processing"
        job.progress = 10
        job.message = "Starting video processing..."
        
        # Import processing functions
        from main import main as process_main
        
        # Update progress
        job.progress = 30
        job.message = "Downloading and analyzing video..."
        
        # Simulate processing (replace with actual processing logic)
        await asyncio.sleep(2)  # Placeholder for actual processing
        
        # Update progress
        job.progress = 60
        job.message = "Generating clips..."
        
        # Here you would call the actual video processing functions
        # For now, we'll simulate success
        await asyncio.sleep(3)
        
        # Complete job
        job.status = "completed"
        job.progress = 100
        job.message = "Video processing completed successfully"
        job.completed_at = datetime.utcnow()
        job.output_urls = [
            "https://your-blob-storage.com/output/clip1.mp4",
            "https://your-blob-storage.com/output/clip2.mp4",
            "https://your-blob-storage.com/output/clip3.mp4"
        ]
        
        # Send webhook notification if URL provided
        if request.webhook_url:
            await send_webhook_notification(request.webhook_url, job)
        
        logger.info(f"Job {job_id} completed successfully")
        
    except Exception as e:
        # Handle errors
        job = jobs[job_id]
        job.status = "failed"
        job.progress = 0
        job.message = "Processing failed"
        job.error_message = str(e)
        job.completed_at = datetime.utcnow()
        
        logger.error(f"Job {job_id} failed: {str(e)}")
        
        # Send webhook notification for failure
        if request.webhook_url:
            await send_webhook_notification(request.webhook_url, job)

async def send_webhook_notification(webhook_url: str, job: JobStatus):
    """
    Send webhook notification to external service (like n8n)
    """
    try:
        import aiohttp
        
        payload = WebhookPayload(
            job_id=job.job_id,
            status=job.status,
            progress=job.progress,
            message=job.message,
            output_urls=job.output_urls,
            error_message=job.error_message
        )
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                str(webhook_url),
                json=payload.dict(),
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    logger.info(f"Webhook notification sent successfully for job {job.job_id}")
                else:
                    logger.error(f"Failed to send webhook notification: {response.status}")
                    
    except Exception as e:
        logger.error(f"Error sending webhook notification: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("API_PORT", 8000))
    host = os.getenv("API_HOST", "0.0.0.0")
    
    uvicorn.run(app, host=host, port=port)
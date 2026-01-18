"""
Updated API Gateway
Routes requests to the standalone video processor service
"""

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
import aiohttp
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app initialization
app = FastAPI(
    title="Zuke Video Shorts Creator API Gateway",
    description="API gateway for video processing service with n8n integration",
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

# Configuration
PROCESSOR_URL = os.getenv("PROCESSOR_URL", "http://localhost:8001")
API_KEY_NAME = os.getenv("API_KEY_HEADER", "X-API-Key")
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Pydantic models
class VideoProcessingRequest(BaseModel):
    youtube_url: Optional[HttpUrl] = None
    video_file_url: Optional[HttpUrl] = None
    video_file_path: Optional[str] = None  # For local files
    num_clips: int = 3
    output_types: List[str] = ["subtitled"]
    auto_approve: bool = False
    webhook_url: Optional[HttpUrl] = None
    job_id: Optional[str] = None

class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: int
    message: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    output_files: List[Dict[str, Any]] = []
    error_message: Optional[str] = None

class ProcessorResponse(BaseModel):
    success: bool
    job_id: str
    message: str
    output_files: List[Dict[str, Any]] = []
    error_message: Optional[str] = None
    processing_time: Optional[float] = None

# In-memory job tracking
jobs: Dict[str, JobStatus] = {}

async def get_api_key(api_key: str = Security(api_key_header)):
    expected_key = os.getenv("API_KEY")
    if not expected_key:
        return True  # No API key configured, allow all requests
    if api_key == expected_key:
        return api_key
    raise HTTPException(status_code=401, detail="Invalid API key")

@app.get("/")
async def root():
    return {
        "message": "Zuke Video Shorts Creator API Gateway",
        "version": "1.0.0",
        "processor_url": PROCESSOR_URL,
        "endpoints": {
            "process": "/process",
            "status": "/status/{job_id}",
            "jobs": "/jobs",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    try:
        # Check processor health
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{PROCESSOR_URL}/health", timeout=5) as response:
                processor_healthy = response.status == 200
    except Exception:
        processor_healthy = False
    
    return {
        "status": "healthy" if processor_healthy else "degraded",
        "processor_healthy": processor_healthy,
        "processor_url": PROCESSOR_URL,
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
    Routes request to processor service and handles response
    """
    # Generate job ID
    job_id = request.job_id or str(uuid.uuid4())\n    \n    # Create job status\n    job_status = JobStatus(\n        job_id=job_id,\n        status=\"pending\",\n        progress=0,\n        message=\"Job queued for processing\",\n        created_at=datetime.utcnow()\n    )\n    jobs[job_id] = job_status\n    \n    logger.info(f\"Job {job_id} queued for processing\")\n    logger.info(f\"Request: {request}\")\n    \n    # Process in background\n    background_tasks.add_task(\n        process_video_background,\n        job_id,\n        request\n    )\n    \n    return {\n        \"job_id\": job_id,\n        \"status\": \"pending\",\n        \"message\": \"Job queued successfully\"\n    }\n\n@app.get(\"/status/{job_id}\")\nasync def get_job_status(job_id: str, api_key: str = Depends(get_api_key)):\n    \"\"\"\n    Get the status of a processing job\n    \"\"\"\n    if job_id not in jobs:\n        # Check if job exists in processor\n        try:\n            async with aiohttp.ClientSession() as session:\n                async with session.get(f\"{PROCESSOR_URL}/status/{job_id}\") as response:\n                    if response.status == 200:\n                        processor_status = await response.json()\n                        return {\n                            \"job_id\": job_id,\n                            \"status\": processor_status[\"status\"],\n                            \"progress\": processor_status[\"progress\"],\n                            \"message\": processor_status[\"message\"],\n                            \"output_files\": processor_status.get(\"output_files\", []),\n                            \"error_message\": processor_status.get(\"error_message\")\n                        }\n        except Exception as e:\n            logger.error(f\"Error checking processor status: {e}\")\n        \n        raise HTTPException(status_code=404, detail=\"Job not found\")\n    \n    return jobs[job_id]\n\n@app.get(\"/jobs\")\nasync def list_jobs(\n    status: Optional[str] = None,\n    limit: int = 100,\n    api_key: str = Depends(get_api_key)\n):\n    \"\"\"\n    List all jobs with optional filtering\n    \"\"\"\n    filtered_jobs = list(jobs.values())\n    \n    if status:\n        filtered_jobs = [j for j in filtered_jobs if j.status == status]\n    \n    # Sort by creation time (newest first)\n    filtered_jobs.sort(key=lambda x: x.created_at, reverse=True)\n    \n    return {\n        \"jobs\": filtered_jobs[:limit],\n        \"total\": len(filtered_jobs)\n    }\n\n# n8n webhook endpoint\n@app.post(\"/webhook/n8n\")\nasync def n8n_webhook(\n    request: VideoProcessingRequest,\n    background_tasks: BackgroundTasks\n):\n    \"\"\"\n    Special endpoint for n8n integration with simplified authentication\n    \"\"\"\n    logger.info(f\"n8n webhook received: {request}\")\n    return await process_video(request, background_tasks, api_key=None)\n\nasync def process_video_background(job_id: str, request: VideoProcessingRequest):\n    \"\"\"\n    Background task to communicate with processor service\n    \"\"\"\n    try:\n        job = jobs[job_id]\n        job.status = \"processing\"\n        job.progress = 5\n        job.message = \"Sending request to video processor...\"\n        \n        # Prepare request for processor\n        processor_request = {\n            \"youtube_url\": str(request.youtube_url) if request.youtube_url else None,\n            \"video_file_path\": request.video_file_path,\n            \"num_clips\": request.num_clips,\n            \"output_types\": request.output_types,\n            \"auto_approve\": request.auto_approve,\n            \"job_id\": job_id\n        }\n        \n        # Remove None values\n        processor_request = {k: v for k, v in processor_request.items() if v is not None}\n        \n        logger.info(f\"Sending to processor: {processor_request}\")\n        \n        # Send request to processor\n        async with aiohttp.ClientSession() as session:\n            async with session.post(\n                f\"{PROCESSOR_URL}/process/sync\",\n                json=processor_request,\n                timeout=aiohttp.ClientTimeout(total=1800)  # 30 minute timeout\n            ) as response:\n                \n                if response.status == 200:\n                    result = await response.json()\n                    logger.info(f\"Processor response: {result}\")\n                    \n                    if result[\"success\"]:\n                        # Update job with successful result\n                        job.status = \"completed\"\n                        job.progress = 100\n                        job.message = \"Processing completed successfully\"\n                        job.completed_at = datetime.utcnow()\n                        job.output_files = result.get(\"output_files\", [])\n                        \n                        # Send webhook notification if configured\n                        if request.webhook_url:\n                            await send_webhook_notification(request.webhook_url, job)\n                        \n                        logger.info(f\"Job {job_id} completed successfully\")\n                    else:\n                        # Handle processor error\n                        job.status = \"failed\"\n                        job.progress = 0\n                        job.message = \"Processing failed\"\n                        job.error_message = result.get(\"error_message\", \"Unknown error\")\n                        job.completed_at = datetime.utcnow()\n                        \n                        logger.error(f\"Processor failed for job {job_id}: {job.error_message}\")\n                else:\n                    # Handle HTTP error\n                    error_text = await response.text()\n                    job.status = \"failed\"\n                    job.progress = 0\n                    job.message = \"Processor service error\"\n                    job.error_message = f\"HTTP {response.status}: {error_text}\"\n                    job.completed_at = datetime.utcnow()\n                    \n                    logger.error(f\"Processor HTTP error for job {job_id}: {job.error_message}\")\n        \n    except asyncio.TimeoutError:\n        job = jobs[job_id]\n        job.status = \"failed\"\n        job.progress = 0\n        job.message = \"Processing timeout\"\n        job.error_message = \"Processing took too long and timed out\"\n        job.completed_at = datetime.utcnow()\n        \n        logger.error(f\"Job {job_id} timed out\")\n        \n    except Exception as e:\n        job = jobs[job_id]\n        job.status = \"failed\"\n        job.progress = 0\n        job.message = \"Processing failed\"\n        job.error_message = str(e)\n        job.completed_at = datetime.utcnow()\n        \n        logger.error(f\"Job {job_id} failed: {str(e)}\")\n        \n        # Send webhook notification for failure\n        if request.webhook_url:\n            await send_webhook_notification(request.webhook_url, job)\n\nasync def send_webhook_notification(webhook_url: str, job: JobStatus):\n    \"\"\"\n    Send webhook notification to external service (like n8n)\n    \"\"\"\n    try:\n        payload = {\n            \"job_id\": job.job_id,\n            \"status\": job.status,\n            \"progress\": job.progress,\n            \"message\": job.message,\n            \"output_files\": job.output_files,\n            \"error_message\": job.error_message\n        }\n        \n        async with aiohttp.ClientSession() as session:\n            async with session.post(\n                str(webhook_url),\n                json=payload,\n                headers={\"Content-Type\": \"application/json\"}\n            ) as response:\n                if response.status == 200:\n                    logger.info(f\"Webhook notification sent successfully for job {job.job_id}\")\n                else:\n                    logger.error(f\"Failed to send webhook notification: {response.status}\")\n                    \n    except Exception as e:\n        logger.error(f\"Error sending webhook notification: {str(e)}\")\n\n# Direct processor endpoints (for debugging)\n@app.get(\"/processor/health\")\nasync def processor_health():\n    \"\"\"Check processor service health\"\"\"\n    try:\n        async with aiohttp.ClientSession() as session:\n            async with session.get(f\"{PROCESSOR_URL}/health\") as response:\n                result = await response.json()\n                return result\n    except Exception as e:\n        raise HTTPException(status_code=503, detail=f\"Processor service unavailable: {str(e)}\")\n\nif __name__ == \"__main__\":\n    import uvicorn\n    \n    port = int(os.getenv(\"API_PORT\", 8000))\n    host = \"0.0.0.0\"\n    \n    logger.info(f\"Starting API Gateway on {host}:{port}\")\n    logger.info(f\"Processor URL: {PROCESSOR_URL}\")\n    \n    uvicorn.run(app, host=host, port=port)
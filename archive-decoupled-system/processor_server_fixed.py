#!/usr/bin/env python3
"""
Zuke Video Processor Server
Standalone service for processing YouTube videos into short clips
Returns JSON responses for integration with other services
"""

import os
import sys
import logging
import asyncio
import uuid
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
import json

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add current directory to path for component imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Components.YoutubeDownloader import download_youtube_video
from Components.Transcription import transcribe_video
from Components.LanguageTasks import extract_highlights
from Components.MultiClipProcessor import process_multiple_clips

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Zuke Video Processor",
    description="Standalone video processing service for YouTube shorts generation",
    version="1.0.0"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class ProcessingRequest(BaseModel):
    youtube_url: Optional[str] = None
    video_file_path: Optional[str] = None
    job_id: Optional[str] = None
    output_types: Optional[List[str]] = ["mp4"]
    max_clips: Optional[int] = 5

class ProcessingResponse(BaseModel):
    success: bool
    job_id: str
    message: str
    output_files: Optional[List[Dict]] = None
    processing_time: Optional[float] = None
    error_message: Optional[str] = None

class StatusResponse(BaseModel):
    job_id: str
    status: str  # "processing", "completed", "failed"
    progress: int  # 0-100
    message: str
    output_files: Optional[List[Dict]] = None
    error_message: Optional[str] = None

# In-memory job tracking (use Redis in production)
jobs_status: Dict[str, StatusResponse] = {}

def clean_filename(filename: str) -> str:
    """Clean filename for safe file system usage"""
    filename = re.sub(r'[^\w\-_\. ]', '_', filename)
    filename = filename.replace(' ', '_')
    return filename[:50]  # Limit length

async def process_video_sync(job_id: str, request: ProcessingRequest, start_time: datetime):
    """
    Process video synchronously and update job status
    """
    try:
        job_status = jobs_status[job_id]
        
        # Step 1: Get video file
        if request.youtube_url:
            job_status.progress = 10
            job_status.message = "Downloading video from YouTube..."
            logger.info(f"Downloading video: {request.youtube_url}")
            
            video_path, video_title = download_youtube_video(
                request.youtube_url, 
                output_dir="./videos"
            )
        elif request.video_file_path:
            video_path = request.video_file_path
            video_title = os.path.splitext(os.path.basename(video_path))[0]
        else:
            raise ValueError("Either youtube_url or video_file_path must be provided")
        
        logger.info(f"Processing video: {video_path}")
        
        # Step 2: Extract audio and transcribe
        job_status.progress = 30
        job_status.message = "Extracting audio and transcribing..."
        
        audio_path = video_path.replace('.mp4', '.wav')
        transcriptions = transcribe_video(video_path, audio_path)
        
        logger.info(f"Transcription completed: {len(transcriptions)} segments")
        
        # Step 3: Extract highlights
        job_status.progress = 50
        job_status.message = "Analyzing content for highlights..."
        
        highlights = extract_highlights(
            transcriptions, 
            max_clips=request.max_clips or 5
        )
        
        logger.info(f"Found {len(highlights)} highlights")
        
        # Step 4: Process clips
        job_status.progress = 70
        job_status.message = "Generating video clips..."
        
        clean_title = clean_filename(video_title) if video_title else f"output_{job_id}"
        all_outputs = process_multiple_clips(
            video_path, highlights, transcriptions, 
            job_id, clean_title, request.output_types
        )
        
        logger.info(f"Processing completed: {len(all_outputs)} clips generated")
        
        # Step 5: Prepare output response
        job_status.progress = 90
        job_status.message = "Preparing output files..."
        
        output_files = []
        for clip_num, clip_data in all_outputs.items():
            highlight = clip_data['highlight']
            files = clip_data['files']
            
            clip_info = {
                "clip_number": clip_num,
                "start_time": highlight['start'],
                "end_time": highlight['end'],
                "duration": highlight['end'] - highlight['start'],
                "content": highlight.get('content', ''),
                "files": []
            }
            
            for file_path in files:
                if os.path.exists(file_path):
                    # Generate public URL (in production, upload to blob storage)
                    file_url = f"file://{os.path.abspath(file_path)}"
                    file_info = {
                        "path": file_path,
                        "url": file_url,
                        "filename": os.path.basename(file_path),
                        "size": os.path.getsize(file_path),
                        "type": "video/mp4"
                    }
                    clip_info["files"].append(file_info)
            
            output_files.append(clip_info)
        
        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Complete job
        job_status.status = "completed"
        job_status.progress = 100
        job_status.message = "Processing completed successfully"
        job_status.output_files = output_files
        
        logger.info(f"Job {job_id} completed successfully in {processing_time:.2f}s")
        logger.info(f"Generated {len(output_files)} clips with {sum(len(clip['files']) for clip in output_files)} total files")
        
        # Cleanup temporary files
        try:
            if os.path.exists(audio_path):
                os.remove(audio_path)
            if request.youtube_url and os.path.exists(video_path):
                os.remove(video_path)  # Only remove if downloaded
        except Exception as cleanup_error:
            logger.warning(f"Cleanup error: {cleanup_error}")
        
    except Exception as e:
        logger.error(f"Processing failed for job {job_id}: {str(e)}")
        
        # Update job status with error
        jobs_status[job_id].status = "failed"
        jobs_status[job_id].progress = 0
        jobs_status[job_id].message = "Processing failed"
        jobs_status[job_id].error_message = str(e)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Zuke Video Processor",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/process")
async def process_video_async(request: ProcessingRequest):
    """
    Start video processing asynchronously
    Returns immediately with job_id for status polling
    """
    job_id = request.job_id or str(uuid.uuid4())[:8]
    
    logger.info(f"Starting async processing job {job_id}")
    
    # Initialize status
    jobs_status[job_id] = StatusResponse(
        job_id=job_id,
        status="processing",
        progress=0,
        message="Starting video processing..."
    )
    
    # Start processing in background
    start_time = datetime.utcnow()
    asyncio.create_task(process_video_sync(job_id, request, start_time))
    
    return {
        "success": True,
        "job_id": job_id,
        "message": "Processing started",
        "status_url": f"/status/{job_id}"
    }

@app.post("/process/sync")
async def process_video_sync_endpoint(request: ProcessingRequest):
    """
    Synchronous processing endpoint that waits for completion
    """
    start_time = datetime.utcnow()
    job_id = request.job_id or str(uuid.uuid4())[:8]
    
    logger.info(f"Starting synchronous processing job {job_id}")
    
    try:
        # Initialize status
        jobs_status[job_id] = StatusResponse(
            job_id=job_id,
            status="processing",
            progress=0,
            message="Starting video processing..."
        )
        
        # Process synchronously
        await process_video_sync(job_id, request, start_time)
        
        # Return final status
        final_status = jobs_status[job_id]
        
        if final_status.status == "completed":
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            return ProcessingResponse(
                success=True,
                job_id=job_id,
                message="Processing completed successfully",
                output_files=final_status.output_files,
                processing_time=processing_time
            )
        else:
            return ProcessingResponse(
                success=False,
                job_id=job_id,
                message="Processing failed",
                error_message=final_status.error_message
            )
            
    except Exception as e:
        logger.error(f"Sync processing failed: {str(e)}")
        return ProcessingResponse(
            success=False,
            job_id=job_id,
            message="Processing failed",
            error_message=str(e)
        )

@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """
    Get processing status for a specific job
    """
    if job_id not in jobs_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return jobs_status[job_id]

@app.get("/jobs")
async def list_jobs():
    """
    List all jobs and their status
    """
    return {
        "jobs": list(jobs_status.values()),
        "total": len(jobs_status)
    }

@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """
    Delete a job from tracking
    """
    if job_id in jobs_status:
        del jobs_status[job_id]
        return {"success": True, "message": f"Job {job_id} deleted"}
    else:
        raise HTTPException(status_code=404, detail="Job not found")

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PROCESSOR_PORT", 8001))
    host = "0.0.0.0"
    
    logger.info(f"Starting Zuke Video Processor on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
#!/usr/bin/env python3
"""
Standalone Video Processor Server
Decoupled video processing service that receives instructions and returns JSON responses
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
import os
import uuid
import json
import logging
from datetime import datetime
import asyncio

# Import video processing components
from Components.YoutubeDownloader import download_youtube_video
from Components.Edit import extractAudio, crop_video
from Components.Transcription import transcribeAudio
from Components.LanguageTasks import GetHighlight, GetMultipleHighlights
from Components.FaceCrop import crop_to_vertical, combine_videos
from Components.Subtitles import add_subtitles_to_video
from Components.MultiClipProcessor import process_multiple_clips

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app initialization
app = FastAPI(
    title="Zuke Video Processor",
    description="Standalone video processing service",
    version="1.0.0"
)

# Pydantic models for API
class ProcessingRequest(BaseModel):
    youtube_url: Optional[str] = None
    video_file_path: Optional[str] = None
    num_clips: int = 3
    output_types: List[str] = ["subtitled"]  # original, original-dimension, subtitled, original-subtitled
    auto_approve: bool = True
    job_id: Optional[str] = None

class ProcessingResponse(BaseModel):
    success: bool
    job_id: str
    message: str
    output_files: List[Dict[str, Any]] = []
    error_message: Optional[str] = None
    processing_time: Optional[float] = None

class StatusResponse(BaseModel):
    job_id: str
    status: str  # processing, completed, failed
    progress: int  # 0-100
    message: str
    output_files: List[Dict[str, Any]] = []
    error_message: Optional[str] = None

# In-memory job storage
jobs_status: Dict[str, StatusResponse] = {}

def clean_filename(filename):
    """Clean filename for safe file operations"""
    import re
    filename = re.sub(r'[^\w\-_\. ]', '_', filename)
    filename = re.sub(r'_+', '_', filename)
    return filename.strip()

@app.get("/")
async def root():
    return {
        "service": "Zuke Video Processor",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "process": "/process",
            "status": "/status/{job_id}",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "active_jobs": len([j for j in jobs_status.values() if j.status == "processing"])
    }

@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """Get processing job status"""
    if job_id not in jobs_status:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs_status[job_id]

@app.post("/process")
async def process_video(request: ProcessingRequest, background_tasks: BackgroundTasks):
    """
    Process video and return JSON response with output file URLs
    """
    start_time = datetime.utcnow()
    
    # Generate job ID
    job_id = request.job_id or str(uuid.uuid4())[:8]
    
    logger.info(f"Starting processing job {job_id}")
    logger.info(f"Request: {request}")
    
    # Validate input
    if not request.youtube_url and not request.video_file_path:
        raise HTTPException(
            status_code=400, 
            detail="Either youtube_url or video_file_path must be provided"
        )
    
    # Initialize job status
    jobs_status[job_id] = StatusResponse(
        job_id=job_id,
        status="processing",
        progress=0,
        message="Starting video processing..."
    )
    
    # Process in background for async response
    background_tasks.add_task(process_video_task, job_id, request, start_time)
    
    return ProcessingResponse(
        success=True,
        job_id=job_id,
        message="Processing started successfully"
    )

async def process_video_task(job_id: str, request: ProcessingRequest, start_time: datetime):
    """
    Background video processing function
    """
    try:
        job_status = jobs_status[job_id]
        
        # Step 1: Download or validate video file
        job_status.progress = 10
        job_status.message = "Downloading video..."
        
        if request.youtube_url:
            logger.info(f"Downloading YouTube video: {request.youtube_url}")
            video_title, video_path = download_youtube_video(request.youtube_url)
        else:
            logger.info(f"Using local video file: {request.video_file_path}")
            video_path = request.video_file_path
            video_title = os.path.splitext(os.path.basename(video_path))[0]
        
        if not os.path.exists(video_path):
            raise Exception(f"Video file not found: {video_path}")
        
        logger.info(f"Video file: {video_path}")
        logger.info(f"Video title: {video_title}")
        
        # Step 2: Extract audio
        job_status.progress = 20
        job_status.message = "Extracting audio..."
        
        audio_path = extractAudio(video_path, session_id=job_id)
        logger.info(f"Audio extracted: {audio_path}")
        
        # Step 3: Transcribe audio
        job_status.progress = 30
        job_status.message = "Transcribing audio..."
        
        transcriptions_result = transcribeAudio(audio_path)
        
        # Handle new dict format from faster-whisper
        if isinstance(transcriptions_result, dict):
            transcriptions = [[seg['text'], seg['start'], seg['end']] 
                            for seg in transcriptions_result['segments']]
        else:
            # Backwards compatibility with old format
            transcriptions = transcriptions_result
            
        logger.info(f"Transcription completed: {len(transcriptions)} segments")
        
        # Step 4: Get highlights
        job_status.progress = 50
        job_status.message = "Analyzing content for highlights..."
        
        if request.num_clips == 1:
            highlight = GetHighlight(transcriptions)
            highlights = [highlight]
        else:
            highlights = GetMultipleHighlights(transcriptions, request.num_clips)
        
        logger.info(f"Found {len(highlights)} highlights")
        
        # Step 5: Process clips
        job_status.progress = 70
        job_status.message = "Generating video clips..."
        
        clean_title = clean_filename(video_title) if video_title else f"output_{job_id}"
        all_outputs = process_multiple_clips(
            video_path, highlights, transcriptions, 
            job_id, clean_title, request.output_types
        )
        
        logger.info(f"Processing completed: {len(all_outputs)} clips generated")
        
        # Step 6: Prepare output response
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
        await process_video_task(job_id, request, start_time)
        
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


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PROCESSOR_PORT", 8001))
    host = "0.0.0.0"
    
    logger.info(f"Starting Zuke Video Processor on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
#!/usr/bin/env python3
"""
Azure-compatible API endpoint for video processing
Receives JSON from n8n and returns processed video URLs
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
import os
import uuid
import subprocess
import json
import tempfile
from datetime import datetime

# Import Azure Blob Storage
try:
    from Components.storage import get_storage_manager
    AZURE_STORAGE_AVAILABLE = True
except ImportError:
    print("⚠️ Azure Blob Storage not available - files will only be stored locally")
    AZURE_STORAGE_AVAILABLE = False

app = FastAPI(
    title="Zuke Video Processor - Azure API",
    description="Azure-deployed video processing for n8n integration",
    version="1.0.0"
)

# CORS for n8n integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoProcessingRequest(BaseModel):
    job_id: str
    timestamp: str
    input_type: str
    youtube_url: Optional[str] = None
    video_file_path: Optional[str] = None
    processing_options: Dict[str, Any]
    workflow_config: Dict[str, Any]

class VideoProcessingResponse(BaseModel):
    success: bool
    job_id: str
    message: str
    processing_time: float
    output_files: List[Dict[str, Any]] = []
    error_message: Optional[str] = None

@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {
        "service": "Zuke Video Processor - Azure",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.post("/process", response_model=VideoProcessingResponse)
async def process_video(request: VideoProcessingRequest):
    """
    Process video from n8n request
    """
    start_time = datetime.utcnow()
    
    try:
        # Build command for original main.py
        cmd = ["python3", "main.py"]
        
        # Add clips argument
        num_clips = request.processing_options.get("num_clips", 3)
        cmd.extend(["--clips", str(num_clips)])
        
        # Add output types
        output_types = request.processing_options.get("output_types", ["subtitled"])
        cmd.extend(["--output-types"] + output_types)
        
        # Add auto-approve if specified
        if request.processing_options.get("auto_approve", False):
            cmd.append("--auto-approve")
        
        # Add video URL or path
        if request.input_type == "youtube" and request.youtube_url:
            cmd.append(request.youtube_url)
        elif request.input_type == "local" and request.video_file_path:
            cmd.append(request.video_file_path)
        else:
            raise ValueError("Invalid input: must provide youtube_url or video_file_path")
        
        # Execute processing
        print(f"Executing command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            cwd="/app",
            capture_output=True,
            text=True,
            timeout=1800  # 30 minutes timeout
        )
        
        if result.returncode != 0:
            raise Exception(f"Processing failed: {result.stderr}")
        
        # Scan output directory for generated files
        output_files = []
        output_dir = "/app/output"
        
        if os.path.exists(output_dir):
            # Initialize Azure Blob Storage if available
            storage_manager = None
            if AZURE_STORAGE_AVAILABLE:
                try:
                    storage_manager = get_storage_manager()
                    print("✅ Azure Blob Storage initialized")
                except Exception as e:
                    print(f"⚠️ Failed to initialize Azure Blob Storage: {e}")
                    storage_manager = None
            
            for filename in os.listdir(output_dir):
                if filename.endswith(".mp4"):
                    file_path = os.path.join(output_dir, filename)
                    file_size = os.path.getsize(file_path)
                    
                    # Upload to Azure Blob Storage if available
                    if storage_manager:
                        try:
                            print(f"📤 Uploading {filename} to Azure Blob Storage...")
                            blob_info = storage_manager.upload_file(
                                file_path=file_path,
                                blob_name=f"videos/{request.job_id}/{filename}",
                                content_type="video/mp4"
                            )
                            file_url = blob_info["url"]
                            print(f"✅ Upload successful: {file_url}")
                        except Exception as upload_error:
                            print(f"❌ Upload failed: {upload_error}")
                            # Fallback to local path
                            file_url = f"/app/output/{filename}"
                    else:
                        # No storage available - return local path
                        file_url = f"/app/output/{filename}"
                        print(f"⚠️ No cloud storage - file saved locally: {file_url}")
                    
                    output_files.append({
                        "filename": filename,
                        "size": file_size,
                        "url": file_url,
                        "type": "video/mp4",
                        "created_at": datetime.utcnow().isoformat(),
                        "storage": "azure_blob" if storage_manager else "local"
                    })
        
        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        return VideoProcessingResponse(
            success=True,
            job_id=request.job_id,
            message=f"Successfully processed {len(output_files)} video clips",
            processing_time=processing_time,
            output_files=output_files
        )
        
    except subprocess.TimeoutExpired:
        return VideoProcessingResponse(
            success=False,
            job_id=request.job_id,
            message="Processing timed out",
            processing_time=1800,
            error_message="Video processing took longer than 30 minutes"
        )
    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        return VideoProcessingResponse(
            success=False,
            job_id=request.job_id,
            message="Processing failed",
            processing_time=processing_time,
            error_message=str(e)
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
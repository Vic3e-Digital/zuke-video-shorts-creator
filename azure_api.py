#!/usr/bin/env python3
"""
Azure-compatible API endpoint for video processing
Receives JSON from n8n and returns processed video URLs
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
import os
import uuid
import subprocess
import json
import tempfile
import time
import sys
import threading
from pathlib import Path
from datetime import datetime

# Import Azure Blob Storage
try:
    from Components.storage import get_storage_manager
    AZURE_STORAGE_AVAILABLE = True
except ImportError:
    print("⚠️ Azure Blob Storage not available - files will only be stored locally")
    AZURE_STORAGE_AVAILABLE = False

# Base URL for local file access (fallback when Azure Storage unavailable)
# Set via environment variable or default to container URL
BASE_URL = os.getenv('API_BASE_URL', 'http://zuke-video-4563.southafricanorth.azurecontainer.io:8000')

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

# In-memory job status storage (use Redis/DB for production)
job_status_store = {}
job_status_lock = threading.Lock()

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
    processing_time: Optional[float] = None
    output_files: List[Dict[str, Any]] = []
    error_message: Optional[str] = None

class JobStatusResponse(BaseModel):
    job_id: str
    status: str  # "queued", "processing", "completed", "failed"
    message: str
    progress: Optional[float] = None  # 0-100
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    processing_time: Optional[float] = None
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

@app.get("/app/output/{filename}")
async def download_file(filename: str):
    """Serve processed video files from /app/output directory"""
    file_path = Path("/app/output") / filename
    
    # Security: prevent directory traversal
    if not file_path.resolve().is_relative_to(Path("/app/output").resolve()):
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")
    
    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="Not a file")
    
    return FileResponse(
        path=str(file_path),
        media_type="video/mp4",
        filename=filename
    )

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a video file to Azure Blob Storage
    Returns the public URL of the uploaded file
    """
    if not AZURE_STORAGE_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="Azure Blob Storage is not configured. Set AZURE_STORAGE_ACCOUNT_NAME and AZURE_STORAGE_ACCOUNT_KEY environment variables."
        )
    
    try:
        # Get storage manager
        storage_manager = get_storage_manager()
        
        # Generate unique filename
        timestamp = int(time.time() * 1000)
        original_filename = file.filename or "video.mp4"
        safe_filename = original_filename.replace(" ", "_").replace("/", "_")
        blob_name = f"{timestamp}_{safe_filename}"
        
        # Save to temp file first
        temp_path = Path(tempfile.gettempdir()) / blob_name
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Upload to Azure Blob Storage
        file_url = storage_manager.upload_file(
            file_path=str(temp_path),
            blob_name=blob_name,
            folder="videos"
        )
        
        # Clean up temp file
        temp_path.unlink()
        
        return {
            "success": True,
            "url": file_url,
            "filename": blob_name,
            "size": len(content)
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )

def update_job_status(job_id: str, status: str, message: str = "", **kwargs):
    """Update job status in store (thread-safe)"""
    with job_status_lock:
        if job_id not in job_status_store:
            job_status_store[job_id] = {
                "job_id": job_id,
                "status": status,
                "message": message,
                "started_at": datetime.utcnow().isoformat(),
                "progress": 0,
                "output_files": [],
                "error_message": None
            }
        else:
            job_status_store[job_id]["status"] = status
            job_status_store[job_id]["message"] = message
        
        # Update additional fields
        for key, value in kwargs.items():
            job_status_store[job_id][key] = value
        
        print(f"📊 Job {job_id}: {status} - {message}", flush=True)

def process_video_background(request: VideoProcessingRequest):
    """Background task to process video"""
    start_time = time.time()
    job_id = request.job_id
    
    try:
        update_job_status(job_id, "processing", "Starting video processing...", progress=5)
        
        # Build command
        cmd = ["python3", "main.py"]
        
        # Add number of clips
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
        
        update_job_status(job_id, "processing", "Downloading and transcribing video...", progress=20)
        
        # Execute processing
        print(f"🚀 Executing command: {' '.join(cmd)}", flush=True)
        
        result = subprocess.run(
            cmd,
            cwd="/app",
            capture_output=True,
            text=True,
            timeout=7200,  # 2 hours timeout
            env={**os.environ}
        )
        
        # Log the output
        print(f"\n{'='*50}", flush=True)
        print(f"=== SUBPROCESS OUTPUT ===", flush=True)
        print(f"{'='*50}", flush=True)
        print(f"STDOUT:\n{result.stdout}", flush=True)
        print(f"STDERR:\n{result.stderr}", flush=True)
        
        update_job_status(job_id, "processing", "Uploading output files...", progress=90)
        
        # Check for output files
        output_files = []
        output_dir = Path("/app/output")
        
        if output_dir.exists():
            # Initialize Azure Blob Storage if available
            storage_manager = None
            if AZURE_STORAGE_AVAILABLE:
                try:
                    storage_manager = get_storage_manager()
                    print("✅ Azure Blob Storage initialized", flush=True)
                except Exception as e:
                    print(f"⚠️ Failed to initialize Azure Blob Storage: {e}", flush=True)
                    storage_manager = None
            
            for mp4_file in output_dir.glob("**/*.mp4"):
                file_size = mp4_file.stat().st_size
                
                # Upload to Azure Blob Storage if available
                if storage_manager:
                    try:
                        print(f"📤 Uploading {mp4_file.name} to Azure Blob Storage...", flush=True)
                        file_url = storage_manager.upload_file(
                            file_path=str(mp4_file),
                            blob_name=f"{request.job_id}/{mp4_file.name}",
                            folder="videos"
                        )
                        print(f"✅ Upload successful: {file_url}", flush=True)
                        storage_type = "azure_blob"
                    except Exception as upload_error:
                        print(f"❌ Upload failed: {upload_error}", flush=True)
                        import traceback
                        traceback.print_exc()
                        # Fallback to container URL
                        file_url = f"{BASE_URL}/app/output/{mp4_file.name}"
                        storage_type = "local"
                else:
                    # No storage available - return container URL
                    file_url = f"{BASE_URL}/app/output/{mp4_file.name}"
                    storage_type = "local"
                    print(f"⚠️ No cloud storage - file saved locally: {file_url}", flush=True)
                
                output_files.append({
                    "filename": mp4_file.name,
                    "size": file_size,
                    "url": file_url,
                    "type": "video/mp4",
                    "created_at": datetime.utcnow().isoformat(),
                    "storage": storage_type
                })
        
        processing_time = time.time() - start_time
        
        # Check if successful
        if len(output_files) == 0:
            error_details = f"STDOUT:\n{result.stdout[:3000]}\n\nSTDERR:\n{result.stderr[:3000]}\n\nReturn code: {result.returncode}"
            print(f"❌ No output files generated. Details:\n{error_details}", flush=True)
            update_job_status(
                job_id, 
                "failed", 
                "No video clips generated",
                progress=100,
                completed_at=datetime.utcnow().isoformat(),
                processing_time=processing_time,
                error_message=error_details
            )
        else:
            update_job_status(
                job_id,
                "completed",
                f"Successfully generated {len(output_files)} video clips",
                progress=100,
                completed_at=datetime.utcnow().isoformat(),
                processing_time=processing_time,
                output_files=output_files
            )
            
    except subprocess.TimeoutExpired:
        processing_time = time.time() - start_time
        update_job_status(
            job_id,
            "failed",
            "Processing timed out after 2 hours",
            progress=100,
            completed_at=datetime.utcnow().isoformat(),
            processing_time=processing_time,
            error_message="Video processing took longer than 2 hours"
        )
    except Exception as e:
        processing_time = time.time() - start_time
        print(f"❌ Exception in background processing: {type(e).__name__}: {e}", flush=True)
        import traceback
        traceback.print_exc()
        update_job_status(
            job_id,
            "failed",
            f"Processing failed: {str(e)}",
            progress=100,
            completed_at=datetime.utcnow().isoformat(),
            processing_time=processing_time,
            error_message=str(e)
        )

@app.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get the status of a processing job"""
    with job_status_lock:
        if job_id not in job_status_store:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        return JobStatusResponse(**job_status_store[job_id])

@app.post("/process-async")
async def process_video_async(request: VideoProcessingRequest, background_tasks: BackgroundTasks):
    """
    Start video processing in background and return immediately
    Use /status/{job_id} to check progress
    """
    # Initialize job status
    update_job_status(request.job_id, "queued", "Job queued for processing")
    
    # Add background task
    background_tasks.add_task(process_video_background, request)
    
    return {
        "job_id": request.job_id,
        "status": "queued",
        "message": "Job queued for processing. Use /status/{job_id} to check progress.",
        "status_url": f"/status/{request.job_id}"
    }

@app.get("/debug/test-main")
async def test_main():
    """Test if main.py can be imported and diagnose environment issues"""
    results = {
        "python_version": sys.version,
        "python_path": sys.executable,
        "cwd": os.getcwd(),
        "app_contents": [],
        "import_tests": {},
        "env_vars": {},
        "main_import": None
    }
    
    # Check /app directory
    try:
        results["app_contents"] = sorted(os.listdir("/app"))[:50]  # Limit to 50 items
    except Exception as e:
        results["app_contents"] = f"Error: {e}"
    
    # Test critical imports
    imports_to_test = [
        "yt_dlp",
        "faster_whisper", 
        "moviepy.editor",
        "cv2",
        "openai",
        "numpy",
        "torch",
        "pydantic",
        "fastapi"
    ]
    
    for module in imports_to_test:
        try:
            __import__(module.split('.')[0])
            results["import_tests"][module] = "✅ OK"
        except ImportError as e:
            results["import_tests"][module] = f"❌ ImportError: {str(e)}"
        except Exception as e:
            results["import_tests"][module] = f"❌ {type(e).__name__}: {str(e)}"
    
    # Check environment variables (redacted for security)
    env_check = [
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_DEPLOYMENT_NAME",
        "OPENAI_API_KEY",
        "AZURE_STORAGE_CONNECTION_STRING",
        "AZURE_STORAGE_ACCOUNT_NAME"
    ]
    for var in env_check:
        val = os.environ.get(var, "")
        if val:
            # Show first 10 and last 4 chars for verification
            if len(val) > 20:
                results["env_vars"][var] = f"✅ Set ({val[:10]}...{val[-4:]})"
            else:
                results["env_vars"][var] = f"✅ Set ({len(val)} chars)"
        else:
            results["env_vars"][var] = "❌ Not set"
    
    # Try to import main.py
    try:
        sys.path.insert(0, "/app")
        import main
        results["main_import"] = "✅ main.py imported successfully"
        
        # Try to get main.py info
        if hasattr(main, '__file__'):
            results["main_file_path"] = main.__file__
        
    except ImportError as e:
        results["main_import"] = f"❌ ImportError: {str(e)}"
    except Exception as e:
        results["main_import"] = f"❌ {type(e).__name__}: {str(e)}"
    
    return results

@app.get("/debug/test-subprocess")
async def test_subprocess():
    """Test running main.py as subprocess with minimal arguments"""
    try:
        cmd = ["python3", "-c", "import sys; print(f'Python: {sys.version}'); import main; print('main.py imported OK')"]
        
        result = subprocess.run(
            cmd,
            cwd="/app",
            capture_output=True,
            text=True,
            timeout=30,
            env={**os.environ}
        )
        
        return {
            "command": " ".join(cmd),
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
    except Exception as e:
        return {
            "error": str(e),
            "error_type": type(e).__name__
        }

@app.post("/process", response_model=VideoProcessingResponse)
async def process_video(request: VideoProcessingRequest):
    """
    Process video from n8n request
    """
    start_time = time.time()
    
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
        
        # Execute processing with CRITICAL output capture
        print(f"🚀 Executing command: {' '.join(cmd)}", flush=True)
        
        result = subprocess.run(
            cmd,
            cwd="/app",
            capture_output=True,  # CRITICAL: Captures stdout and stderr
            text=True,
            timeout=1800,  # 30 minutes timeout
            env={**os.environ}  # Pass all environment variables
        )
        
        # Log the output regardless of success/failure
        print(f"\n{'='*50}", flush=True)
        print(f"=== SUBPROCESS OUTPUT ===", flush=True)
        print(f"{'='*50}", flush=True)
        print(f"STDOUT:\n{result.stdout}", flush=True)
        print(f"STDERR:\n{result.stderr}", flush=True)
        
        # Check for output files
        output_files = []
        output_dir = Path("/app/output")
        
        if output_dir.exists():
            # Initialize Azure Blob Storage if available
            storage_manager = None
            if AZURE_STORAGE_AVAILABLE:
                try:
                    storage_manager = get_storage_manager()
                    print("✅ Azure Blob Storage initialized", flush=True)
                except Exception as e:
                    print(f"⚠️ Failed to initialize Azure Blob Storage: {e}", flush=True)
                    storage_manager = None
            
            for mp4_file in output_dir.glob("**/*.mp4"):
                file_size = mp4_file.stat().st_size
                
                # Upload to Azure Blob Storage if available
                if storage_manager:
                    try:
                        print(f"📤 Uploading {mp4_file.name} to Azure Blob Storage...", flush=True)
                        file_url = storage_manager.upload_file(
                            file_path=str(mp4_file),
                            blob_name=f"{request.job_id}/{mp4_file.name}",
                            folder="videos"
                        )
                        print(f"✅ Upload successful: {file_url}", flush=True)
                        storage_type = "azure_blob"
                    except Exception as upload_error:
                        print(f"❌ Upload failed: {upload_error}", flush=True)
                        import traceback
                        traceback.print_exc()
                        # Fallback to container URL
                        file_url = f"{BASE_URL}/app/output/{mp4_file.name}"
                        storage_type = "local"
                else:
                    # No storage available - return container URL
                    file_url = f"{BASE_URL}/app/output/{mp4_file.name}"
                    storage_type = "local"
                    print(f"⚠️ No cloud storage - file saved locally: {file_url}", flush=True)
                
                output_files.append({
                    "filename": mp4_file.name,
                    "size": file_size,
                    "url": file_url,
                    "type": "video/mp4",
                    "created_at": datetime.utcnow().isoformat(),
                    "storage": storage_type
                })
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Return error details if no files produced
        if len(output_files) == 0:
            error_details = f"STDOUT:\n{result.stdout[:3000]}\n\nSTDERR:\n{result.stderr[:3000]}\n\nReturn code: {result.returncode}"
            print(f"❌ No output files generated. Details:\n{error_details}", flush=True)
            return VideoProcessingResponse(
                success=False,
                job_id=request.job_id,
                message="No video clips generated",
                processing_time=processing_time,
                output_files=[],
                error_message=error_details
            )
        
        # Calculate processing time
        processing_time = time.time() - start_time
        return VideoProcessingResponse(
            success=True,
            job_id=request.job_id,
            message="Video processing completed successfully",
            processing_time=processing_time,
            output_files=output_files
        )
    except subprocess.TimeoutExpired:
        processing_time = time.time() - start_time
        return VideoProcessingResponse(
            success=False,
            job_id=request.job_id,
            message="Processing timed out after 30 minutes",
            processing_time=processing_time,
            error_message="Video processing took longer than 30 minutes"
        )
    except Exception as e:
        processing_time = time.time() - start_time
        print(f"❌ Exception in process_video: {type(e).__name__}: {e}", flush=True)
        return VideoProcessingResponse(
            success=False,
            job_id=request.job_id,
            message=f"Processing failed: {str(e)}",
            processing_time=processing_time,
            error_message=str(e)
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
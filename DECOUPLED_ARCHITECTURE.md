# 🏗️ Decoupled Architecture Guide

## Overview

The Zuke Video Shorts Creator now uses a **fully decoupled microservices architecture** that separates concerns and enables easy integration, debugging, and scaling.

## 🏛️ Architecture Components

```
┌─────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌──────────────────┐
│   Frontend  │───▶│   n8n Workflow  │───▶│   API Gateway   │───▶│  Video Processor │
│  (Port 3000)│    │   (Optional)    │    │   (Port 8000)   │    │   (Port 8001)    │
└─────────────┘    └─────────────────┘    └─────────────────┘    └──────────────────┘
      │                       │                       │                       │
   Vue.js UI            Visual Debug          FastAPI Router         Core Processing
   Simple HTML           Automation          Request/Response       AI + Video Logic
                        Webhook Bridge       Job Management         JSON Output
```

## 🔄 Request Flow

### Standard Flow
```
1. Frontend sends request → API Gateway
2. API Gateway queues job → Video Processor
3. Video Processor processes → Returns JSON response
4. API Gateway forwards response → Frontend
```

### n8n Enhanced Flow
```
1. Frontend sends request → n8n Workflow
2. n8n processes/validates → API Gateway
3. API Gateway queues job → Video Processor
4. Video Processor completes → n8n via webhook
5. n8n distributes results → Multiple destinations
```

## 🚀 Quick Start

### Option 1: Start All Services
```bash
./start.sh all
```

This starts:
- **Frontend**: http://localhost:3000
- **API Gateway**: http://localhost:8000 
- **Video Processor**: http://localhost:8001

### Option 2: Start Individual Services

```bash
# Terminal 1: Video Processor
./start.sh processor

# Terminal 2: API Gateway  
./start.sh api

# Terminal 3: Frontend
./start.sh frontend
```

### Option 3: Docker Compose
```bash
# GPU version
./start.sh docker

# CPU version
./start.sh docker-cpu
```

## 📡 API Endpoints

### API Gateway (Port 8000)
- `POST /process` - Submit video processing job
- `GET /status/{job_id}` - Check job status
- `GET /jobs` - List all jobs
- `POST /webhook/n8n` - n8n integration endpoint
- `GET /health` - Service health check
- `GET /docs` - Interactive API documentation

### Video Processor (Port 8001)
- `POST /process` - Direct processing (async)
- `POST /process/sync` - Direct processing (sync)
- `GET /status/{job_id}` - Processing status
- `GET /health` - Processor health
- `GET /docs` - Processor API documentation

## 🐛 Debugging & Development

### 1. Component Isolation
Start services individually to isolate issues:
```bash
# Test processor only
./start.sh processor
curl http://localhost:8001/health

# Test API gateway
./start.sh api  
curl http://localhost:8000/health
```

### 2. Request Tracing
Use n8n to visualize request flow:
1. Import workflow from `n8n-workflows/`
2. Send request through n8n
3. Watch each step in real-time
4. Inspect data transformations

### 3. Log Analysis
Each service logs independently:
- **Processor**: Core video processing logs
- **API Gateway**: Request routing and job management
- **n8n**: Workflow execution and webhooks

### 4. Direct Testing
Test components directly:
```bash
# Direct processor test
curl -X POST http://localhost:8001/process/sync \
  -H "Content-Type: application/json" \
  -d '{
    "youtube_url": "https://youtube.com/watch?v=...",
    "num_clips": 1,
    "auto_approve": true
  }'

# API gateway test
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{
    "youtube_url": "https://youtube.com/watch?v=...",
    "num_clips": 1
  }'
```

## 🔄 n8n Integration

### Setup n8n Workflow
1. Import `n8n-workflows/youtube-to-shorts-workflow.json`
2. Configure webhook URLs:
   - **Trigger**: `http://your-n8n.com/webhook/video-shorts-webhook`
   - **Results**: `http://your-n8n.com/webhook/results`
3. Set environment variables:
   - `ZUKE_API_KEY`: Your API key (optional)
4. Update API endpoint: `http://localhost:8000/process`

### Test n8n Flow
```bash
# Send request to n8n webhook
curl -X POST http://your-n8n.com/webhook/video-shorts-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "youtube_url": "https://youtube.com/watch?v=...",
    "num_clips": 2,
    "output_types": ["subtitled"]
  }'
```

### n8n Benefits
- **Visual Debugging**: See request flow graphically
- **Easy Integration**: Connect to other services
- **Webhook Management**: Automatic result distribution
- **Error Handling**: Visual error tracking
- **Future Expansion**: Easy to add new integrations

## 🔌 Integration Examples

### 1. Custom Frontend Integration
```javascript
// JavaScript example
const response = await fetch('http://localhost:8000/process', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    youtube_url: 'https://youtube.com/watch?v=...',
    num_clips: 3,
    webhook_url: 'https://your-app.com/webhook'
  })
});

const result = await response.json();
console.log('Job ID:', result.job_id);
```

### 2. Python Integration
```python
import requests

response = requests.post('http://localhost:8000/process', json={
    'youtube_url': 'https://youtube.com/watch?v=...',
    'num_clips': 2,
    'auto_approve': True
})

job_id = response.json()['job_id']
print(f"Processing job: {job_id}")
```

### 3. Webhook Integration
```python
# Your webhook receiver
@app.route('/webhook', methods=['POST'])
def handle_webhook():
    data = request.json
    if data['status'] == 'completed':
        # Process the video files
        for clip in data['output_files']:
            for file in clip['files']:
                download_file(file['url'])
    return 'OK'
```

## 🔧 Configuration

### Environment Variables
```bash
# API Gateway
API_PORT=8000
PROCESSOR_URL=http://localhost:8001
API_KEY=your-optional-api-key

# Video Processor
PROCESSOR_PORT=8001
PROCESSOR_MODE=api

# OpenAI
OPENAI_API_KEY=your-openai-key
# OR Azure OpenAI
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
```

### Docker Configuration
Update `docker-compose.yml` for your environment:
```yaml
services:
  video-processor:
    environment:
      - PROCESSOR_PORT=8001
      - OPENAI_API_KEY=${OPENAI_API_KEY}
  
  api-server:
    environment:
      - API_PORT=8000
      - PROCESSOR_URL=http://video-processor:8001
```

## 📊 Response Format

### Standard JSON Response
```json
{
  "success": true,
  "job_id": "abc123",
  "message": "Processing completed successfully",
  "output_files": [
    {
      "clip_number": 1,
      "start_time": 120,
      "end_time": 240,
      "duration": 120,
      "content": "Transcript excerpt...",
      "files": [
        {
          "filename": "video_clip1_subtitled.mp4",
          "url": "file:///app/output/video_clip1_subtitled.mp4",
          "type": "video/mp4",
          "size": 15728640
        }
      ]
    }
  ]
}
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Port Conflicts
```bash
# Check what's using ports
lsof -i :8000
lsof -i :8001

# Kill processes if needed
kill $(lsof -t -i:8000)
```

#### 2. Service Communication
```bash
# Test connectivity between services
curl http://localhost:8001/health  # Processor
curl http://localhost:8000/processor/health  # Gateway→Processor
```

#### 3. Missing Dependencies
```bash
# Install processor dependencies
pip install -r requirements.txt

# Install API dependencies
pip install -r api/requirements.txt
```

#### 4. Docker Issues
```bash
# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up
```

### Debug Modes

#### 1. Verbose Logging
```bash
export LOG_LEVEL=DEBUG
./start.sh all
```

#### 2. Service Health Check
```bash
# Check all services
curl http://localhost:8000/health
curl http://localhost:8001/health
```

#### 3. Manual Testing
```bash
# Test processor directly
python processor_server.py &
curl -X POST http://localhost:8001/process/sync -H "Content-Type: application/json" -d '{"youtube_url": "https://youtube.com/watch?v=dQw4w9WgXcQ", "num_clips": 1, "auto_approve": true}'
```

## 🔮 Future Integrations

This architecture makes it easy to add:

1. **Database Integration**: Replace in-memory job storage
2. **Message Queues**: Add Redis/RabbitMQ for job queuing
3. **Load Balancing**: Multiple processor instances
4. **Authentication**: User management and API keys
5. **Monitoring**: Prometheus/Grafana integration
6. **Cloud Storage**: AWS S3/Azure Blob for file storage
7. **CDN Integration**: CloudFlare/CloudFront for video delivery

## 📝 Notes

- Each service can be scaled independently
- Services communicate via HTTP APIs (JSON)
- n8n provides visual workflow management
- Easy to add new services or replace existing ones
- Perfect for microservices deployment
- Supports both development and production environments

---

**Architecture Benefits:**
✅ **Decoupled**: Services are independent  
✅ **Debuggable**: Easy to trace requests  
✅ **Scalable**: Each service scales independently  
✅ **Integrable**: Standard HTTP APIs  
✅ **Maintainable**: Clear separation of concerns
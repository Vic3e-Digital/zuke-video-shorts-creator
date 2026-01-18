# Archived Decoupled System

This folder contains the decoupled microservices architecture that was built:

## Files Archived:
- `processor_server.py` - Standalone video processing service (FastAPI)
- `processor_server_fixed.py` - Fixed version of processor server
- `api/gateway.py` - API gateway for routing requests
- `frontend/index.html` - Vue.js frontend interface
- `docker-compose.yml` - Docker orchestration for services
- `start.sh` - Service startup script

## Architecture:
```
Frontend (Port 3000) → API Gateway (Port 8000) → Video Processor (Port 8001) → n8n Webhooks
```

## To Use Later:
1. Move files back to root directory
2. Install Python dependencies with Python 3.10+
3. Start services in order:
   - `python3.10 processor_server.py` (Port 8001)
   - `python3.10 api/gateway.py` (Port 8000) 
   - Serve frontend on Port 3000
4. Configure n8n webhooks for integration

This system provides complete decoupling, JSON responses, and visual debugging through n8n workflows.
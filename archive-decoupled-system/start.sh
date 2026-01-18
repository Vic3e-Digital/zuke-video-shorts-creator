#!/bin/bash

# Zuke Video Shorts Creator - Decoupled Architecture Startup Script

echo "🎬 Starting Zuke Video Shorts Creator - Decoupled Architecture"
echo "=============================================================="

# Default configuration
PROCESSOR_PORT=${PROCESSOR_PORT:-8001}
API_PORT=${API_PORT:-8000}
FRONTEND_PORT=${FRONTEND_PORT:-3000}

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env file with your configuration before proceeding"
    exit 1
fi

# Function to check if port is available
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "❌ Port $1 is already in use"
        exit 1
    fi
}

# Check required ports
echo "🔍 Checking port availability..."
check_port $PROCESSOR_PORT
check_port $API_PORT

# Start services based on argument
case "$1" in
    "processor")
        echo "🚀 Starting Video Processor Server on port $PROCESSOR_PORT..."
        echo "   This service handles the actual video processing"
        python processor_server.py
        ;;
    
    "api")
        echo "🚀 Starting API Gateway on port $API_PORT..."
        echo "   This service routes requests to the processor"
        python api/gateway.py
        ;;
    
    "frontend")
        echo "🚀 Starting Frontend Interface on port $FRONTEND_PORT..."
        echo "   This provides the web interface for users"
        cd frontend
        python -m http.server $FRONTEND_PORT
        ;;
    
    "all")
        echo "🚀 Starting all services..."
        echo ""
        echo "📋 Architecture:"
        echo "   📱 Frontend (Port $FRONTEND_PORT) → 🌐 API Gateway (Port $API_PORT) → ⚙️  Processor (Port $PROCESSOR_PORT)"
        echo ""
        
        # Start processor in background
        echo "Starting Video Processor..."
        python processor_server.py &
        PROCESSOR_PID=$!
        sleep 3
        
        # Start API gateway in background
        echo "Starting API Gateway..."
        python api/gateway.py &
        API_PID=$!
        sleep 3
        
        # Start frontend
        echo "Starting Frontend Interface..."
        echo ""
        echo "🎉 All services started successfully!"
        echo ""
        echo "📱 Frontend:     http://localhost:$FRONTEND_PORT"
        echo "🌐 API Gateway:  http://localhost:$API_PORT"
        echo "⚙️  Processor:    http://localhost:$PROCESSOR_PORT"
        echo ""
        echo "📚 API Documentation: http://localhost:$API_PORT/docs"
        echo "🔧 Processor API:     http://localhost:$PROCESSOR_PORT/docs"
        echo ""
        echo "Press Ctrl+C to stop all services..."
        
        cd frontend
        python -m http.server $FRONTEND_PORT
        
        # Cleanup on exit
        trap "echo '🛑 Shutting down services...'; kill $PROCESSOR_PID $API_PID 2>/dev/null; exit" INT TERM
        ;;
    
    "docker")
        echo "🐳 Starting services with Docker Compose..."
        echo ""
        echo "Building and starting containers..."
        docker-compose up --build
        ;;
    
    "docker-cpu")
        echo "🐳 Starting CPU-only services with Docker Compose..."
        echo ""
        echo "Building and starting containers (CPU mode)..."
        docker-compose -f docker-compose-cpu.yml up --build
        ;;
    
    *)
        echo "Usage: $0 {processor|api|frontend|all|docker|docker-cpu}"
        echo ""
        echo "🏗️  Decoupled Architecture Components:"
        echo ""
        echo "   processor   - Start only the video processing service (port $PROCESSOR_PORT)"
        echo "   api        - Start only the API gateway (port $API_PORT)"
        echo "   frontend   - Start only the frontend interface (port $FRONTEND_PORT)"
        echo "   all        - Start all services locally"
        echo "   docker     - Start all services using Docker Compose (GPU)"
        echo "   docker-cpu - Start all services using Docker Compose (CPU only)"
        echo ""
        echo "🔄 Workflow Integration:"
        echo "   For n8n integration, use: http://localhost:$API_PORT/webhook/n8n"
        echo ""
        echo "📋 Architecture Flow:"
        echo "   Frontend → n8n (optional) → API Gateway → Video Processor"
        echo ""
        echo "🐛 For debugging:"
        echo "   - Start components individually to isolate issues"
        echo "   - Check logs in each terminal window"
        echo "   - Use n8n to visualize the request flow"
        exit 1
        ;;
esac
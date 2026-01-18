#!/bin/bash

# Zuke Video Shorts Creator - Simple n8n Frontend
# Serves the frontend on localhost:3000

echo "🎬 Starting Zuke Video Shorts Creator Frontend"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 Frontend will be available at: http://localhost:3000"
echo "🔗 Make sure your n8n webhook is configured and running"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start Python HTTP server on port 3000
python3 -m http.server 3000

echo "👋 Frontend stopped"
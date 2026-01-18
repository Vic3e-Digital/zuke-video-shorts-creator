#!/bin/bash

# Test script for n8n workflow with Azure video processor

set -e

# Configuration
AZURE_ENDPOINT="http://zuke-video-4563.eastus.azurecontainer.io:8000/process"
N8N_WEBHOOK="https://aigents.southafricanorth.azurecontainer.io/webhook/zuke-video-process"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 n8n Workflow Test Script${NC}"
echo "=================================="
echo ""

# Function to test endpoint
test_endpoint() {
    local endpoint=$1
    local name=$2
    local video_url=$3
    
    echo -e "${YELLOW}Testing: $name${NC}"
    echo "Endpoint: $endpoint"
    echo "Video: $video_url"
    echo ""
    
    JOB_ID="test_$(date +%s)_$(openssl rand -hex 4)"
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")
    
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$endpoint" \
      -H "Content-Type: application/json" \
      -d "{
        \"job_id\": \"$JOB_ID\",
        \"timestamp\": \"$TIMESTAMP\",
        \"input_type\": \"youtube\",
        \"processing_options\": {
          \"num_clips\": 1,
          \"auto_approve\": true,
          \"output_types\": [\"subtitled\"]
        },
        \"workflow_config\": {
          \"source\": \"test-script\",
          \"version\": \"1.0.0\",
          \"features_requested\": [\"subtitled\"],
          \"processing_mode\": \"batch\"
        },
        \"youtube_url\": \"$video_url\"
      }")
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    echo "HTTP Status: $HTTP_CODE"
    echo "Response:"
    echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
    echo ""
    
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "202" ]; then
        echo -e "${GREEN}✅ Test passed!${NC}"
        return 0
    else
        echo -e "${RED}❌ Test failed!${NC}"
        return 1
    fi
}

# Menu
echo "Select test mode:"
echo "1. Test Azure endpoint directly (YouTube)"
echo "2. Test via n8n webhook (YouTube)"
echo "3. Test both endpoints (YouTube)"
echo "4. Custom YouTube URL"
echo "5. Test with local video file"
echo ""
read -p "Enter choice (1-5): " choice

case $choice in
    1)
        echo ""
        test_endpoint "$AZURE_ENDPOINT" "Azure Direct" "https://www.youtube.com/watch?v=FeirRhBRc5w"
        ;;
    2)
        echo ""
        test_endpoint "$N8N_WEBHOOK" "n8n Webhook" "https://www.youtube.com/watch?v=FeirRhBRc5w"
        ;;
    3)
        echo ""
        test_endpoint "$AZURE_ENDPOINT" "Azure Direct" "https://www.youtube.com/watch?v=FeirRhBRc5w"
        echo ""
        echo "---"
        echo ""
        test_endpoint "$N8N_WEBHOOK" "n8n Webhook" "https://www.youtube.com/watch?v=FeirRhBRc5w"
        ;;
    4)
        echo ""
        read -p "Enter YouTube URL: " video_url
        read -p "Test (1) Azure direct or (2) n8n webhook? " endpoint_choice
        
        if [ "$endpoint_choice" = "1" ]; then
            test_endpoint "$AZURE_ENDPOINT" "Azure Direct (Custom)" "$video_url"
        else
            test_endpoint "$N8N_WEBHOOK" "n8n Webhook (Custom)" "$video_url"
        fi
        ;;
    5)
        echo ""
        read -p "Enter local video file path (e.g., videos/my-video.mp4): " local_file
        
        if [ ! -f "$local_file" ]; then
            echo -e "${RED}❌ File not found: $local_file${NC}"
            exit 1
        fi
        
        echo ""
        echo -e "${YELLOW}Testing with local file: $local_file${NC}"
        echo "Endpoint: $AZURE_ENDPOINT"
        echo ""
        
        JOB_ID="test_local_$(date +%s)_$(openssl rand -hex 4)"
        TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")
        
        RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$AZURE_ENDPOINT" \
          -H "Content-Type: application/json" \
          -d "{
            \"job_id\": \"$JOB_ID\",
            \"timestamp\": \"$TIMESTAMP\",
            \"input_type\": \"local\",
            \"local_file_path\": \"$local_file\",
            \"processing_options\": {
              \"num_clips\": 1,
              \"auto_approve\": true,
              \"output_types\": [\"subtitled\"]
            }
          }")
        
        HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
        BODY=$(echo "$RESPONSE" | sed '$d')
        
        echo "HTTP Status: $HTTP_CODE"
        echo "Response:"
        echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
        echo ""
        
        if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "202" ]; then
            echo -e "${GREEN}✅ Test passed!${NC}"
        else
            echo -e "${RED}❌ Test failed!${NC}"
        fi
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo "=================================="
echo -e "${BLUE}Test complete!${NC}"
echo ""
echo "📊 Check logs:"
echo "   Azure: az containerapp logs show --name zuke-video-4563 --resource-group <rg>"
echo "   n8n: Check your n8n execution history"

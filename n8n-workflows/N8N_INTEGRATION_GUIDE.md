# n8n Integration Guide

## Overview
This guide shows you how to integrate n8n workflow automation with the Zuke Video Shorts Creator API.

## Prerequisites
- n8n instance (self-hosted or cloud)
- Zuke Video Shorts Creator API deployed on Azure
- API key for authentication

## Setup Steps

### 1. Import the Workflow

1. Open your n8n instance
2. Click "Workflows" in the left sidebar
3. Click "Import from File" or "Import from URL"
4. Select the `youtube-to-shorts-workflow.json` file
5. Click "Import"

### 2. Configure Environment Variables

In your n8n instance, set up the following environment variables:

```bash
ZUKE_API_KEY=your-api-key-here
ZUKE_API_URL=https://your-azure-app.azurecontainerapps.io
```

Alternatively, you can configure credentials directly in n8n:

1. Go to "Credentials" in the left sidebar
2. Add new "Header Auth" credential
3. Set:
   - **Name**: `X-API-Key`
   - **Value**: Your API key

### 3. Update Workflow Nodes

#### Update API Endpoint
1. Open the "Send to Zuke API" node
2. Update the URL to your Azure Container App URL:
   ```
   https://your-azure-app.azurecontainerapps.io/webhook/n8n
   ```

#### Configure Webhook URLs
1. Open the "Webhook" node
2. Copy the webhook URL (it will look like: `https://your-n8n.com/webhook/video-shorts-webhook`)
3. This is the URL you'll use to trigger the workflow

#### Configure Notification Nodes (Optional)
- **Slack**: Update channel ID in "Notify Slack" nodes
- **Email**: Update recipient email in "Send Email Notification" node
- **Google Drive**: Configure Google Drive credentials for video storage

## Usage

### Trigger via Webhook

Send a POST request to your n8n webhook URL:

```bash
curl -X POST https://your-n8n.com/webhook/video-shorts-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "num_clips": 3,
    "output_types": ["subtitled", "original"],
    "auto_approve": true
  }'
```

### Trigger via n8n Schedule

Add a Schedule Trigger node:

1. Drag "Schedule Trigger" node onto the canvas
2. Connect it to "Send to Zuke API" node
3. Configure schedule (e.g., daily at 9 AM)
4. Add a "Code" node to provide YouTube URLs from a list or database

### Example: Process YouTube Playlist

```json
{
  "nodes": [
    {
      "name": "Get Playlist Videos",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "https://www.googleapis.com/youtube/v3/playlistItems",
        "qs": {
          "playlistId": "YOUR_PLAYLIST_ID",
          "key": "YOUR_YOUTUBE_API_KEY",
          "maxResults": 10
        }
      }
    },
    {
      "name": "Process Each Video",
      "type": "n8n-nodes-base.splitInBatches",
      "parameters": {
        "batchSize": 1
      }
    }
  ]
}
```

## Workflow Nodes Explained

### 1. Webhook Node
- Receives incoming requests
- Accepts JSON payload with video processing parameters

### 2. Send to Zuke API
- Sends request to your Azure-hosted API
- Includes authentication header
- Passes video processing parameters

### 3. Respond to Webhook
- Returns immediate response with job ID
- Acknowledges request received

### 4. Results Webhook
- Receives completion notification from Zuke API
- Webhook URL is automatically passed to the API

### 5. If Completed
- Checks if processing was successful
- Routes to success or error handlers

### 6. Download Videos
- Downloads generated video clips
- Converts to binary data for further processing

### 7. Upload to Google Drive (Optional)
- Stores videos in Google Drive
- Organizes by job ID

### 8. Notifications
- Sends Slack/Email notifications
- Updates on success or failure

## Advanced Workflows

### Workflow 1: Automated Content Pipeline

```
YouTube RSS Feed → Filter New Videos → Process with Zuke → 
Upload to Social Media → Track Performance
```

### Workflow 2: Bulk Processing

```
Google Sheets with URLs → Loop Through Rows → 
Process Each Video → Update Sheet with Results
```

### Workflow 3: Social Media Scheduler

```
Schedule Trigger → Get Video from Library → 
Process with Zuke → Post to Multiple Platforms
```

## Error Handling

The workflow includes error handling for:
- API connection failures
- Video processing errors
- Invalid input parameters

### Configure Error Workflow

1. Create a separate error workflow
2. Add "Error Trigger" node
3. Configure error notifications and logging

## Monitoring

### Check Job Status

Add a polling node to check job status:

```json
{
  "parameters": {
    "url": "https://your-azure-app.azurecontainerapps.io/status/{{ $json.job_id }}",
    "method": "GET",
    "options": {
      "repeat": {
        "interval": 30,
        "maxIterations": 20
      }
    }
  }
}
```

### View Active Jobs

Query all active jobs:

```bash
curl -X GET https://your-azure-app.azurecontainerapps.io/jobs?status=processing \
  -H "X-API-Key: your-api-key"
```

## Sample Payloads

### Simple Video Processing
```json
{
  "youtube_url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "num_clips": 3,
  "auto_approve": true
}
```

### Advanced Configuration
```json
{
  "youtube_url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "num_clips": 5,
  "output_types": ["subtitled", "original", "original-dimension"],
  "auto_approve": false,
  "webhook_url": "https://your-n8n.com/webhook/results",
  "job_id": "custom-job-id-123"
}
```

### Local Video File
```json
{
  "video_file_url": "https://your-blob-storage.com/input/video.mp4",
  "num_clips": 2,
  "output_types": ["subtitled"],
  "auto_approve": true
}
```

## Troubleshooting

### Webhook Not Receiving Data
- Check webhook URL is correct
- Verify n8n is accessible from Azure
- Check firewall/network settings

### API Authentication Errors
- Verify API key is correct
- Check API_KEY_HEADER environment variable
- Ensure header name matches (default: `X-API-Key`)

### Processing Timeouts
- Increase n8n workflow timeout settings
- Use asynchronous processing with webhooks
- Implement status polling

## Best Practices

1. **Use Environment Variables**: Store sensitive data (API keys, URLs) in environment variables
2. **Implement Retry Logic**: Add retry nodes for failed API calls
3. **Monitor Performance**: Track processing times and success rates
4. **Handle Errors Gracefully**: Implement proper error notifications
5. **Rate Limiting**: Add delays between batch processing to avoid overwhelming the API
6. **Version Control**: Export and backup your workflows regularly

## Support

For issues or questions:
- Check API documentation: `/docs` endpoint on your Azure app
- Review API logs in Application Insights
- Test API endpoints directly with Postman/curl

## Example Use Cases

### 1. Content Repurposing Agency
- Client submits YouTube URL via form
- n8n receives form submission
- Processes video with Zuke API
- Delivers shorts to client's Google Drive
- Sends invoice via Stripe integration

### 2. Social Media Manager
- Schedule monitors content calendar
- Automatically processes selected videos
- Posts to TikTok, Instagram, YouTube Shorts
- Tracks engagement metrics
- Reports weekly performance

### 3. Educational Platform
- Processes long-form lecture videos
- Generates bite-sized clips for social media
- Uploads to LMS platform
- Sends notifications to students
- Tracks view analytics

---

**Need Help?** Contact support or check the [API documentation](https://your-azure-app.azurecontainerapps.io/docs)
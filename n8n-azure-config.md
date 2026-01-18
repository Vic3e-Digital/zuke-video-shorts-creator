# n8n Workflow Configuration for Azure Video Processing

## Updated n8n HTTP Request Node Configuration

After deploying to Azure, update your "Make Request to Azure Deployment" node with these settings:

### HTTP Request Node Settings:
```json
{
  "method": "POST",
  "url": "http://your-container-url:8000/process",
  "authentication": "none",
  "sendQuery": false,
  "sendHeaders": true,
  "headerParameters": {
    "parameters": [
      {
        "name": "Content-Type",
        "value": "application/json"
      }
    ]
  },
  "sendBody": true,
  "bodyContentType": "json",
  "jsonBody": "={{ $json.body }}",
  "options": {
    "timeout": 1800000,
    "response": {
      "response": {
        "responseFormat": "json"
      }
    }
  }
}
```

### Complete n8n Workflow JSON:
```json
{
  "nodes": [
    {
      "parameters": {
        "httpMethod": "POST",
        "path": "video-processing",
        "options": {}
      },
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 2.1,
      "position": [0, 0],
      "id": "webhook-node",
      "name": "Receive Video Request"
    },
    {
      "parameters": {
        "method": "POST",
        "url": "http://YOUR-AZURE-URL:8000/process",
        "authentication": "none",
        "sendBody": true,
        "bodyContentType": "json",
        "jsonBody": "={{ $json.body }}",
        "options": {
          "timeout": 1800000
        }
      },
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.3,
      "position": [300, 0],
      "id": "azure-request",
      "name": "Process Video on Azure"
    },
    {
      "parameters": {
        "respondWith": "json",
        "responseBody": "={{ $json }}"
      },
      "type": "n8n-nodes-base.respondToWebhook",
      "typeVersion": 1.5,
      "position": [600, 0],
      "id": "respond",
      "name": "Return Results"
    }
  ],
  "connections": {
    "Receive Video Request": {
      "main": [[{
        "node": "Process Video on Azure",
        "type": "main",
        "index": 0
      }]]
    },
    "Process Video on Azure": {
      "main": [[{
        "node": "Return Results", 
        "type": "main",
        "index": 0
      }]]
    }
  }
}
```

## Expected Response Format from Azure:

```json
{
  "success": true,
  "job_id": "job_1768738199292",
  "message": "Successfully processed 3 video clips",
  "processing_time": 145.7,
  "output_files": [
    {
      "filename": "video_clip1_subtitled.mp4",
      "size": 5242880,
      "url": "https://your-storage.blob.core.windows.net/videos/clip1.mp4",
      "type": "video/mp4",
      "created_at": "2026-01-18T12:15:00.000Z"
    }
  ]
}
```

## Testing Steps:

1. **Deploy to Azure** (run deploy-to-azure.ps1)
2. **Update n8n HTTP Request URL** with your Azure container URL
3. **Test health endpoint**: http://your-azure-url:8000/
4. **Send test request** from your frontend (localhost:3000)
5. **Monitor n8n execution** for successful processing

## Troubleshooting:

- **Timeout errors**: Increase timeout in n8n HTTP Request node to 30 minutes
- **Memory issues**: Upgrade Azure Container Instance to 8GB memory
- **Connection refused**: Check Azure container status and firewall rules
- **API key errors**: Verify environment variables in Azure deployment
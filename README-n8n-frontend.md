# 🎬 Zuke Video Shorts Creator - n8n Integration

Simple frontend interface that sends JSON requests directly to n8n webhooks for video processing.

## ✨ Features

- **🌐 Direct n8n Integration**: Sends structured JSON to your n8n webhook
- **📹 Flexible Input**: YouTube URLs or local video file paths  
- **⚙️ Full Configuration**: All options from the main README
- **🎨 Multiple Output Types**: Original, subtitled, with different aspect ratios
- **💾 Smart Storage**: Remembers your webhook URL
- **📱 Responsive Design**: Works on desktop and mobile

## 🚀 Quick Start

### 1. Start the Frontend
```bash
./start-frontend.sh
```

### 2. Open in Browser
Navigate to: **http://localhost:3000**

### 3. Configure n8n Webhook
Enter your n8n webhook URL in the form (it will be saved automatically)

### 4. Submit Video Request
Fill out the form and click "Send to n8n Webhook"

## 📋 Form Options

### Video Input
- **YouTube URL**: Any YouTube video link
- **Local File**: Full path to video file on your system

### Processing Options  
- **Number of Clips**: 1-10 short clips (default: 3)
- **Auto-approve**: Skip interactive approval for batch processing

### Output Types
- **Original**: 9:16 vertical crop, no subtitles
- **Original-Dimension**: Preserves input aspect ratio, no subtitles  
- **Subtitled**: 9:16 vertical crop with burned-in captions
- **Original-Subtitled**: Original aspect ratio with captions

### Advanced
- **Custom Job ID**: Optional identifier for tracking in n8n

## 🔗 JSON Payload Structure

The frontend sends this JSON structure to your n8n webhook:

```json
{
  "job_id": "job_1234567890",
  "timestamp": "2026-01-18T10:30:00.000Z",
  "input_type": "youtube",
  "youtube_url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "video_file_path": null,
  "processing_options": {
    "num_clips": 3,
    "auto_approve": false,
    "output_types": ["original", "original-dimension", "subtitled"]
  },
  "workflow_config": {
    "source": "zuke-frontend",
    "version": "1.0.0", 
    "features_requested": ["original", "subtitled"],
    "processing_mode": "interactive"
  }
}
```

## 🛠️ n8n Workflow Setup

Your n8n webhook should:

1. **Receive** the JSON payload from this frontend
2. **Process** the video using the original Docker container:
   ```bash
   docker run --rm -it \
     --env-file .env \
     -v "$(pwd)/output:/app/output" \
     ai-youtube-shorts-generator:cpu \
     python3 main.py --clips 3 --auto-approve "YOUTUBE_URL"
   ```
3. **Return** status updates and file URLs back to your system

## 📁 File Structure

```
/
├── index.html              # Main frontend interface
├── start-frontend.sh       # Startup script  
├── archive-decoupled-system/  # Archived microservices architecture
│   ├── processor_server.py
│   ├── api/gateway.py
│   ├── frontend/index.html
│   └── README.md
└── README.md              # This file
```

## 🎯 Use Cases

### Development & Testing
- Quick video processing requests  
- Test different output combinations
- Debug n8n workflow integration

### Production Workflows
- Integrate with existing n8n automations
- Batch process multiple videos  
- Connect to other services via n8n

### Content Creation
- Generate multiple clip variations
- Process YouTube content for social media
- Create vertical videos for TikTok/Instagram

## 🔧 Technical Details

- **Frontend**: Pure HTML + Vue.js 3 + Axios
- **Server**: Python 3 HTTP server (port 3000)
- **Storage**: LocalStorage for webhook URL persistence
- **CORS**: Handled by browser (same-origin for local testing)

## 🚀 Next Steps (Todo)

- [ ] Docker deployment setup
- [ ] Production webhook authentication 
- [ ] File upload support for local videos
- [ ] Real-time status updates from n8n
- [ ] Batch processing multiple URLs

## 💡 Tips

1. **Webhook Testing**: Use tools like ngrok to expose local n8n to internet
2. **Error Handling**: Check browser console for detailed error messages  
3. **CORS Issues**: Ensure n8n webhook accepts requests from `localhost:3000`
4. **Persistence**: Webhook URL is saved automatically in browser storage

---

🎬 **Ready to create some viral shorts? Start the frontend and connect to n8n!**
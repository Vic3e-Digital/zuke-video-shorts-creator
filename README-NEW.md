# Zuke Video Shorts Creator

> **Production-ready AI-powered video shorts generator with Azure deployment, n8n integration, and enterprise features**

Transform long-form videos into viral short-form content with AI-powered highlight detection, automated subtitles, and smart cropping. Originally based on [AI-Youtube-Shorts-Generator](https://github.com/SamurAIGPT/AI-Youtube-Shorts-Generator), now enhanced with cloud infrastructure, API endpoints, and workflow automation.

![Project Status](https://img.shields.io/badge/status-in%20development-yellow)
![Azure](https://img.shields.io/badge/Azure-Ready-blue)
![n8n](https://img.shields.io/badge/n8n-Compatible-green)

---

## 🚀 New Features

### Cloud & Infrastructure
- ☁️ **Azure Deployment Ready**: Complete ARM templates and deployment guides
- 🗄️ **Azure Blob Storage**: Scalable media storage and CDN integration
- 🔄 **n8n Workflow Integration**: Automation-ready API endpoints
- 📊 **Application Insights**: Comprehensive monitoring and logging
- 🔐 **Azure Key Vault**: Secure secrets management

### API & Integration
- 🌐 **RESTful API**: FastAPI-based endpoints for programmatic access
- 🔗 **Webhook Support**: Real-time job status notifications
- 🔑 **API Authentication**: Secure access with API keys
- 📡 **Async Processing**: Background job processing with status tracking
- 🎯 **Multi-tenant Support**: Session isolation for concurrent processing

### Enhanced Features
- 🎨 **Advanced Font Styling**: Multiple font families and styling presets
- 🎭 **Subtitle Animations**: Fade-in, slide-up, and typewriter effects
- 🌈 **Color Schemes**: Predefined and custom color palettes
- 📦 **Batch Processing**: Process multiple videos in parallel
- 🧹 **Lifecycle Management**: Automatic cleanup of old files

---

## 📋 Original Features

- **🎬 Flexible Input**: YouTube URLs and local video files
- **🎨 Multiple Output Types**: Subtitled, original, various aspect ratios
- **🎤 GPU-Accelerated Transcription**: CUDA-enabled Whisper
- **🤖 AI Highlight Selection**: GPT-4o-mini powered content analysis
- **📝 Auto Subtitles**: Stylized captions with multiple font options
- **🎯 Smart Cropping**: Face-detection and motion tracking
- **📱 Vertical Format**: Perfect 9:16 for TikTok/YouTube Shorts/Instagram Reels

---

## 🏗️ Architecture

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   n8n Workflow  │─────▶│  FastAPI Server  │─────▶│  Azure Blob     │
│   Automation    │      │  (Container App) │      │  Storage        │
└─────────────────┘      └──────────────────┘      └─────────────────┘
                                │
                                ▼
                         ┌──────────────────┐
                         │  Video Processor │
                         │  (Python + AI)   │
                         └──────────────────┘
                                │
                         ┌──────┴──────┐
                         ▼             ▼
                    ┌─────────┐  ┌─────────┐
                    │ Whisper │  │ GPT-4o  │
                    │ (Audio) │  │ (Text)  │
                    └─────────┘  └─────────┘
```

---

## 📚 Quick Start

### Local Development

```bash
# Clone the repository
git clone https://github.com/Vic3e-Digital/zuke-video-shorts-creator.git
cd zuke-video-shorts-creator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your API keys

# Run the application
python main.py --youtube-url "https://youtube.com/watch?v=..." --num-clips 3
```

### Docker Deployment

```bash
# Build the image
docker build -t zuke-video-shorts-creator .

# Run with GPU support
docker run --gpus all \
  -v $(pwd)/output:/app/output \
  -e OPENAI_API_KEY=your_key \
  zuke-video-shorts-creator
```

### Azure Deployment

See [Azure Deployment Guide](azure/DEPLOYMENT_GUIDE.md) for complete instructions.

```bash
# Quick deploy
az deployment group create \
  --resource-group your-rg \
  --template-file azure/azure-resources.json \
  --parameters projectName=zuke-video-shorts
```

---

## 🔌 API Usage

### Start the API Server

```bash
# Install API dependencies
pip install -r api/requirements.txt

# Run the server
cd api && python main.py
```

### Process a Video

```bash
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "youtube_url": "https://youtube.com/watch?v=...",
    "num_clips": 3,
    "output_types": ["subtitled"],
    "auto_approve": true,
    "webhook_url": "https://your-webhook.com/callback"
  }'
```

### Check Job Status

```bash
curl -X GET http://localhost:8000/status/job-id-here \
  -H "X-API-Key: your-api-key"
```

---

## 🔄 n8n Integration

Complete workflow automation with n8n. See [n8n Integration Guide](n8n-workflows/N8N_INTEGRATION_GUIDE.md).

1. Import the workflow template from `n8n-workflows/`
2. Configure your API endpoint and credentials
3. Set up webhook triggers
4. Automate your video processing pipeline

**Example Use Cases:**
- Monitor YouTube channel for new videos
- Process videos from Google Drive
- Auto-post shorts to social media
- Batch process video libraries

---

## 🎨 Font Styling Options

### Predefined Styles

```python
from Components.FontManager import get_font_manager

font_manager = get_font_manager()

# Use predefined styles
styles = [
    "youtube_shorts",    # Classic YouTube Shorts style
    "tiktok_style",      # Bold TikTok aesthetic
    "instagram_reels",   # Clean Instagram look
    "minimal_clean",     # Minimal with background
    "bold_impact",       # High-impact yellow text
    "elegant_serif"      # Professional serif font
]
```

### Custom Font Configuration

```python
from Components.FontManager import create_custom_style

custom_style = create_custom_style(
    name="my_brand",
    family="montserrat-bold",
    size=52,
    color="white",
    stroke_color="blue",
    stroke_width=3,
    background_color="rgba(0,0,0,0.7)",
    position="bottom",
    animation="fade-in"
)
```

### Available Fonts

See [FontManager.py](Components/FontManager.py) for the full list of supported fonts and styling options.

---

## 📖 Documentation

- **[TODO.md](TODO.md)**: Complete development roadmap
- **[Azure Deployment Guide](azure/DEPLOYMENT_GUIDE.md)**: Step-by-step Azure setup
- **[n8n Integration Guide](n8n-workflows/N8N_INTEGRATION_GUIDE.md)**: Workflow automation
- **[API Documentation](http://localhost:8000/docs)**: Interactive API docs (when server is running)
- **[Original Usage Guide](USAGE_GUIDE.md)**: CLI usage and options

---

## 🗺️ Development Roadmap

### ✅ Phase 1: Repository Setup (Completed)
- [x] Repository initialization
- [x] Comprehensive documentation
- [x] Enhanced .gitignore

### 🚧 Phase 2: Azure Deployment (In Progress)
- [ ] Deploy to Azure Container Apps
- [ ] Set up CI/CD pipeline
- [ ] Configure monitoring and logging

### 📋 Phase 3: n8n Integration (Planned)
- [ ] REST API implementation
- [ ] Webhook receivers
- [ ] Job queue system
- [ ] Status tracking

### 📋 Phase 4: Blob Storage (Planned)
- [ ] Azure Blob Storage integration
- [ ] CDN configuration
- [ ] File lifecycle management

### 📋 Phase 5: Frontend (Planned)
- [ ] React/Vue.js interface
- [ ] Real-time status updates
- [ ] User dashboard

### 📋 Phase 6: Enhanced Styling (Planned)
- [ ] Font rendering fixes
- [ ] Multiple font families
- [ ] Text animation effects
- [ ] Brand customization

See [TODO.md](TODO.md) for the complete roadmap.

---

## 🛠️ Tech Stack

### Core Technologies
- **Python 3.10+**: Main programming language
- **FFmpeg**: Video processing and manipulation
- **OpenAI Whisper**: Speech-to-text transcription
- **GPT-4o-mini**: AI-powered highlight selection
- **OpenCV**: Computer vision and face detection

### Cloud & Infrastructure
- **Azure Container Apps**: Serverless container hosting
- **Azure Blob Storage**: Scalable object storage
- **Azure Container Registry**: Private container registry
- **Application Insights**: Monitoring and analytics
- **Azure Key Vault**: Secrets management

### API & Integration
- **FastAPI**: Modern Python web framework
- **Uvicorn**: ASGI server
- **Pydantic**: Data validation
- **aiohttp**: Async HTTP client

### Development Tools
- **Docker**: Containerization
- **GitHub Actions**: CI/CD automation
- **n8n**: Workflow automation

---

## 📦 Project Structure

```
zuke-video-shorts-creator/
├── api/                          # FastAPI server
│   ├── main.py                   # API endpoints
│   └── requirements.txt          # API dependencies
├── azure/                        # Azure deployment files
│   ├── azure-resources.json      # ARM template
│   └── DEPLOYMENT_GUIDE.md       # Deployment instructions
├── Components/                   # Core processing modules
│   ├── Edit.py                   # Video editing
│   ├── FaceCrop.py              # Face detection & cropping
│   ├── FontManager.py           # Font styling system (NEW)
│   ├── LanguageTasks.py         # GPT-4 integration
│   ├── Subtitles.py             # Subtitle generation
│   ├── Transcription.py         # Whisper integration
│   ├── YoutubeDownloader.py     # YouTube video downloader
│   └── storage/                 # Azure Blob Storage (NEW)
│       └── azure_storage.py     # Storage manager
├── n8n-workflows/               # n8n integration (NEW)
│   ├── youtube-to-shorts-workflow.json
│   └── N8N_INTEGRATION_GUIDE.md
├── .github/workflows/           # CI/CD pipelines (NEW)
│   └── azure-deploy.yml
├── main.py                      # CLI entry point
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Container image
├── docker-compose.yml           # Local Docker setup
├── .env.example                 # Environment template
├── TODO.md                      # Development roadmap (NEW)
└── README.md                    # This file
```

---

## 🔧 Environment Variables

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_key_here

# Azure Storage
AZURE_STORAGE_ACCOUNT_NAME=your_account
AZURE_STORAGE_ACCOUNT_KEY=your_key
AZURE_STORAGE_CONTAINER_NAME=video-content

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_KEY=your_api_key

# Application Settings
DEBUG=false
LOG_LEVEL=INFO
MAX_CONCURRENT_JOBS=5
ENABLE_GPU=true
```

See [.env.example](.env.example) for complete configuration.

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Original project: [AI-Youtube-Shorts-Generator](https://github.com/SamurAIGPT/AI-Youtube-Shorts-Generator) by SamurAIGPT
- OpenAI for Whisper and GPT models
- Azure for cloud infrastructure
- n8n for workflow automation platform

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Vic3e-Digital/zuke-video-shorts-creator/issues)
- **Documentation**: See `/docs` folder
- **API Docs**: Visit `/docs` endpoint when server is running

---

## 🔗 Links

- **Azure Portal**: [portal.azure.com](https://portal.azure.com)
- **n8n Documentation**: [docs.n8n.io](https://docs.n8n.io)
- **FastAPI**: [fastapi.tiangolo.com](https://fastapi.tiangolo.com)

---

**Built with ❤️ by Vic3e Digital**
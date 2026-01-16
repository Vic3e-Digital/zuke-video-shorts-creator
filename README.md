# AI YouTube Shorts Generator

AI-powered tool to automatically generate engaging YouTube Shorts from long-form videos. Uses GPT-4o-mini and Whisper to extract highlights, add subtitles, and crop videos vertically for social media.

![longshorts](https://github.com/user-attachments/assets/3f5d1abf-bf3b-475f-8abf-5e253003453a)

## Features

- **🎬 Flexible Input**: Supports both YouTube URLs and local video files
- **� Multiple Clips**: Generate 1-10 viral clips from a single video (default: 3)
- **🎨 Multiple Output Types**: 
  - **Original**: Vertical crop without subtitles
  - **Original-Dimension**: Preserves input video dimensions without subtitles
  - **Subtitled**: Vertical crop with burned-in subtitles  
  - **Original-Subtitled**: Original aspect ratio with subtitles
- **🎤 GPU-Accelerated Transcription**: CUDA-enabled Whisper for fast speech-to-text
- **🤖 AI Highlight Selection**: GPT-4o-mini automatically finds the most engaging 2-minute segments
- **✅ Interactive Approval**: Review and approve/regenerate selections with 15-second auto-approve timeout
- **📝 Auto Subtitles**: Stylized captions with Franklin Gothic font burned into video
- **🎯 Smart Cropping**: 
  - **Face videos**: Static face-centered crop (no jerky movement)
  - **Screen recordings**: Half-width display with smooth motion tracking (1 shift/second max)
- **📱 Vertical Format**: Perfect 9:16 aspect ratio for TikTok/YouTube Shorts/Instagram Reels
- **⚙️ Automation Ready**: CLI arguments, auto-quality selection, timeout-based approvals
- **🔄 Concurrent Execution**: Unique session IDs allow multiple instances to run simultaneously
- **📦 Clean Output**: Slugified filenames and automatic temp file cleanup

## Installation

### Prerequisites

- Python 3.10+
- FFmpeg with development headers
- NVIDIA GPU with CUDA support (optional, but recommended for faster transcription)
- ImageMagick (for subtitle rendering)
- OpenAI API key

### Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/SamurAIGPT/AI-Youtube-Shorts-Generator.git
   cd AI-Youtube-Shorts-Generator
   ```

2. **Install system dependencies:**
   ```bash
   sudo apt install -y ffmpeg libavdevice-dev libavfilter-dev libopus-dev \
     libvpx-dev pkg-config libsrtp2-dev imagemagick
   ```

3. **Fix ImageMagick security policy** (required for subtitles):
   ```bash
   sudo sed -i 's/rights="none" pattern="@\*"/rights="read|write" pattern="@*"/' /etc/ImageMagick-6/policy.xml
   ```

4. **Create and activate virtual environment:**
   ```bash
   python3.10 -m venv venv
   source venv/bin/activate
   ```

5. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

6. **Set up environment variables:**
   
   Create a `.env` file in the project root:
   ```bash
   OPENAI_API=your_openai_api_key_here
   ```

## Docker Setup (Recommended)

For easier deployment and consistent environments, use Docker:

### Prerequisites for Docker
- Docker Desktop installed and running
- Azure OpenAI account (or OpenAI API key)

### Docker Installation Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/SamurAIGPT/AI-Youtube-Shorts-Generator.git
   cd AI-Youtube-Shorts-Generator
   ```

2. **Set up environment variables for Azure OpenAI:**
   
   Create a `.env` file with your Azure OpenAI credentials:
   ```bash
   AZURE_OPENAI_API_KEY=your_azure_openai_api_key
   AZURE_OPENAI_ENDPOINT=https://your-resource-name.cognitiveservices.azure.com/
   AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4.1
   AZURE_OPENAI_API_VERSION=2024-04-01-preview
   
   # Optional: Subtitle Styling Configuration
   SUBTITLE_FONT=Franklin-Gothic
   SUBTITLE_SIZE_RATIO=0.065
   SUBTITLE_COLOR=#2699ff
   SUBTITLE_STROKE_COLOR=black
   SUBTITLE_STROKE_WIDTH=2
   ```

   **Note**: Find your exact endpoint and deployment name in the Azure Portal under your OpenAI resource.

3. **Build the CPU-optimized Docker image:**
   ```bash
   docker build -f Dockerfile.cpu -t ai-youtube-shorts-generator:cpu .
   ```

4. **Run with Docker:**
   ```bash
   docker run --rm -it \
     --env-file .env \
     -v "$(pwd)/output:/app/output" \
     ai-youtube-shorts-generator:cpu \
     python3 main.py "https://youtu.be/VIDEO_ID"
   ```

### Accessing Processed Videos

All generated short videos are saved to the `output` folder in your project directory:

- **Output location**: `./output/` (automatically created)
- **Filename format**: `{video-title}_{session-id}_short.mp4`
- **Example**: `empowering-women-leaders-mentorship-&-community-in-higher-education-wlhe2025_f7325328_short.mp4`

To view your processed videos:
```bash
# List all generated videos
ls -la output/

# Play video (macOS)
open output/your-video-name_short.mp4

# Play video (Linux)
xdg-open output/your-video-name_short.mp4
```

The videos are ready to upload directly to:
- YouTube Shorts
- TikTok
- Instagram Reels
- Any vertical video platform (9:16 aspect ratio)

## Usage

### Quick Start Examples

#### Generate 3 clips with default output types (original + subtitled):
```bash
python main.py "https://youtu.be/VIDEO_ID"
```

#### Generate 5 clips with all output types:
```bash
python main.py --clips 5 --output-types original subtitled original-subtitled "https://youtu.be/VIDEO_ID"
```

#### Batch process with auto-approve:
```bash
python main.py --auto-approve --clips 3 "https://youtu.be/VIDEO_ID"
```

### Command Line Options

```bash
python main.py [OPTIONS] VIDEO_URL_OR_PATH

Options:
  --clips N                     Number of clips to generate (default: 3)
  --output-types TYPE [TYPE...] Output types: original, subtitled, original-subtitled
                               (default: original subtitled)
  --auto-approve               Skip interactive approval (for batch processing)
  --help                       Show help message
```

### Docker Usage (Recommended)

#### Basic Usage - Generate 3 clips with default output types:
```bash
docker run --rm -it \
  --env-file .env \
  -v "$(pwd)/output:/app/output" \
  ai-youtube-shorts-generator:cpu \
  python3 main.py "https://www.youtube.com/watch?v=FeirRhBRc5w"
```

#### Generate 5 clips with all output variations:
```bash
docker run --rm -it \
  --env-file .env \
  -v "$(pwd)/output:/app/output" \
  ai-youtube-shorts-generator:cpu \
  python3 main.py --clips 5 --output-types original subtitled original-subtitled "https://youtu.be/VIDEO_ID"
```

#### Generate only original cuts (no subtitles):
```bash
docker run --rm -it \
  --env-file .env \
  -v "$(pwd)/output:/app/output" \
  ai-youtube-shorts-generator:cpu \
  python3 main.py --clips 3 --output-types original "https://youtu.be/VIDEO_ID"
```

#### Batch processing with auto-approve:
```bash
docker run --rm -it \
  --env-file .env \
  -v "$(pwd)/output:/app/output" \
  ai-youtube-shorts-generator:cpu \
  python3 main.py --auto-approve --clips 5 "https://youtu.be/VIDEO_ID"
```

#### Interactive Mode (Enter URL when prompted):
```bash
docker run --rm -it \
  --env-file .env \
  -v "$(pwd)/output:/app/output" \
  ai-youtube-shorts-generator:cpu
```

#### Process local video files:
```bash
# Mount your video directory and process local file
docker run --rm -it \
  --env-file .env \
  -v "$(pwd)/output:/app/output" \
  -v "$(pwd)/videos:/app/videos" \
  ai-youtube-shorts-generator:cpu \
  python3 main.py --clips 3 "/app/videos/your-video.mp4"
```

#### Batch process multiple URLs:
```bash
# Create urls.txt with one URL per line, then process all
docker run --rm -it \
  --env-file .env \
  -v "$(pwd)/output:/app/output" \
  -v "$(pwd)/urls.txt:/app/urls.txt" \
  ai-youtube-shorts-generator:cpu \
  bash -c "xargs -a urls.txt -I{} python3 main.py --auto-approve --clips 3 {}"
```

### Native Python Usage

#### Multiple clips with custom output types:
```bash
./run.sh --clips 5 --output-types original subtitled "https://youtu.be/VIDEO_ID"
```

#### With Local Video File:
```bash
./run.sh --clips 3 "/path/to/your/video.mp4"
```

#### Batch Processing Multiple URLs:
Create a `urls.txt` file with one URL per line, then:

```bash
# Process all URLs with 3 clips each, auto-approve
xargs -a urls.txt -I{} ./run.sh --auto-approve --clips 3 {}
```

### Output Types Explained

- **`original`**: Cropped to 9:16 aspect ratio, no subtitles
- **`original-dimension`**: Preserves original video dimensions (e.g., 16:9), no subtitles
- **`subtitled`**: Cropped to 9:16 aspect ratio, with burned-in subtitles  
- **`original-subtitled`**: Original aspect ratio, with burned-in subtitles

**Default output types**: `original`, `original-dimension`, `subtitled` (3 files per clip)

### File Naming

Generated files follow this pattern:
```
{video_title}_clip1_{session_id}_original.mp4
{video_title}_clip1_{session_id}_subtitled.mp4
{video_title}_clip2_{session_id}_original.mp4
...
```

## Resolution Selection

When downloading from YouTube, you'll see:
```
Available video streams:
  0. Resolution: 1080p, Size: 45.2 MB, Type: Adaptive
  1. Resolution: 720p, Size: 28.1 MB, Type: Adaptive
  2. Resolution: 480p, Size: 15.3 MB, Type: Adaptive

Select resolution number (0-2) or wait 5s for auto-select...
Auto-selecting highest quality in 5 seconds...
```

- **Enter a number** to select that resolution immediately
- **Wait 5 seconds** to auto-select highest quality (1080p)
- **Invalid input** falls back to highest quality

## How It Works

1. **Download/Load**: Fetches from YouTube or loads local file
2. **Resolution Selection**: Choose video quality (5s timeout, auto-selects highest)
3. **Extract Audio**: Converts to WAV format
4. **Transcribe**: GPU-accelerated Whisper transcription (~30s for 5min video)
5. **AI Analysis**: GPT-4o-mini selects most engaging 2-minute segment
6. **Interactive Approval**: Review selection, regenerate if needed, or auto-approve in 15s
7. **Extract Clip**: Crops selected timeframe
8. **Smart Crop**: 
   - Detects faces → static face-centered vertical crop
   - No faces → half-width screen recording with motion tracking
9. **Add Subtitles**: Burns Franklin Gothic captions with blue text/black outline
10. **Combine Audio**: Merges audio track with final video
11. **Cleanup**: Removes all temporary files

**Output**: `{video-title}_{session-id}_short.mp4` with slugified filename and unique identifier

## Interactive Workflow

After AI selects a highlight, you'll see:

```
============================================================
SELECTED SEGMENT DETAILS:
Time: 68s - 187s (119s duration)
============================================================

Options:
  [Enter/y] Approve and continue
  [r] Regenerate selection
  [n] Cancel

Auto-approving in 15 seconds if no input...
```

- Press **Enter** or **y** to approve
- Press **r** to regenerate a different selection (can repeat multiple times)
- Press **n** to cancel
- Wait 15 seconds to auto-approve (perfect for automation)

## Configuration

### Subtitle Styling
Configure in your `.env` file:
- **Font**: `SUBTITLE_FONT=Franklin-Gothic` (any system font)
- **Size Ratio**: `SUBTITLE_SIZE_RATIO=0.065` (percentage of video height)
- **Color**: `SUBTITLE_COLOR=#2699ff` (hex color code)
- **Stroke Color**: `SUBTITLE_STROKE_COLOR=black` (outline color)
- **Stroke Width**: `SUBTITLE_STROKE_WIDTH=2` (outline thickness in pixels)

Examples:
```bash
# Large yellow subtitles with red outline
SUBTITLE_FONT=Arial
SUBTITLE_SIZE_RATIO=0.08
SUBTITLE_COLOR=#ffff00
SUBTITLE_STROKE_COLOR=#ff0000
SUBTITLE_STROKE_WIDTH=3

# Small white subtitles with no outline
SUBTITLE_COLOR=#ffffff
SUBTITLE_SIZE_RATIO=0.05
SUBTITLE_STROKE_WIDTH=0
```

### Highlight Selection Criteria
Edit `Components/LanguageTasks.py`:
- **Prompt**: Line 29 (adjust what's "interesting, useful, surprising, controversial, or thought-provoking")
- **Model**: Line 54 (`model="gpt-4o-mini"`)
- **Temperature**: Line 55 (`temperature=1.0`)

### Motion Tracking
Edit `Components/FaceCrop.py`:
- **Update frequency**: Line 93 (`update_interval = int(fps)`) - currently 1 shift/second
- **Smoothing**: Line 115 (`0.90 * smoothed_x + 0.10 * target_x`) - currently 90%/10%
- **Motion threshold**: Line 107 (`motion_threshold = 2.0`)

### Face Detection
Edit `Components/FaceCrop.py`:
- **Sensitivity**: Line 37 (`minNeighbors=8`) - Higher = fewer false positives
- **Minimum size**: Line 37 (`minSize=(30, 30)`) - Minimum face size in pixels

### Video Quality
Edit `Components/Subtitles.py` and `Components/FaceCrop.py`:
- **Bitrate**: Subtitles.py line 74 (`bitrate='3000k'`)
- **Preset**: Subtitles.py line 73 (`preset='medium'`)

## Output Files

Final videos are named: `{video-title}_{session-id}_short.mp4`

Example: `my-awesome-video_a1b2c3d4_short.mp4`

- **Slugified title**: Lowercase, hyphens instead of spaces
- **Session ID**: 8-character unique identifier for traceability
- **Resolution**: Matches source video height (720p → 404x720, 1080p → 607x1080)

## Concurrent Execution

Run multiple instances simultaneously:
```bash
./run.sh "https://youtu.be/VIDEO1" &
./run.sh "https://youtu.be/VIDEO2" &
./run.sh "/path/to/video3.mp4" &
```

Each instance gets a unique session ID and temporary files, preventing conflicts.

## Troubleshooting

### CUDA/GPU Issues
```bash
# Verify CUDA libraries
export LD_LIBRARY_PATH=$(find $(pwd)/venv/lib/python3.10/site-packages/nvidia -name "lib" -type d | paste -sd ":" -)
```
The `run.sh` script handles this automatically.

### No Subtitles
Ensure ImageMagick policy allows file operations:
```bash
grep 'pattern="@\*"' /etc/ImageMagick-6/policy.xml
# Should show: rights="read|write"
```

### Face Detection Issues
- Video needs visible faces in first 30 frames
- For screen recordings, automatic motion tracking applies
- Low-resolution videos may have less reliable detection

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

## License

This project is licensed under the MIT License.

## Related Projects

- [AI Influencer Generator](https://github.com/SamurAIGPT/AI-Influencer-Generator)
- [Text to Video AI](https://github.com/SamurAIGPT/Text-To-Video-AI)
- [Faceless Video Generator](https://github.com/SamurAIGPT/Faceless-Video-Generator)
- [AI B-roll Generator](https://github.com/Anil-matcha/AI-B-roll)
- [No-code YouTube Shorts Generator](https://www.vadoo.tv/clip-youtube-video)


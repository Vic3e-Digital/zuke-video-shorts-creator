# AI YouTube Shorts Generator

AI-powered tool to automatically generate engaging YouTube Shorts from long-form videos. Uses GPT-4o-mini and Whisper to extract highlights, add subtitles, and crop videos vertically for social media.

![longshorts](https://github.com/user-attachments/assets/3f5d1abf-bf3b-475f-8abf-5e253003453a)

## Features

- **🎬 Video Processing**: Supports both YouTube URLs and local video files
- **🎤 AI Transcription**: GPU-accelerated Whisper transcription with CUDA support
- **🤖 Smart Highlight Detection**: GPT-4o-mini identifies the most interesting 2-minute segments
- **📝 Automatic Subtitles**: Burns stylized captions directly into the video
- **🎯 Face Detection**: Static face detection with intelligent cropping (no jerky camera movement)
- **📱 Vertical Format**: Automatic 9:16 crop for TikTok/YouTube Shorts/Instagram Reels
- **⚙️ Command-Line Support**: Pass URLs/files as arguments for automation

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

## Usage

### With YouTube URL (Interactive)
```bash
./run.sh
# Then enter YouTube URL when prompted
```

### With YouTube URL (Command-Line)
```bash
./run.sh "https://youtu.be/VIDEO_ID"
```

### With Local Video File
```bash
./run.sh "/path/to/your/video.mp4"
```

## How It Works

1. **Download/Load Video**: Fetches from YouTube or loads local file
2. **Extract Audio**: Converts video audio to WAV format
3. **Transcribe**: Uses faster-whisper with CUDA for speech-to-text
4. **Analyze**: GPT-4o-mini selects the most engaging 2-minute segment
5. **Extract Clip**: Crops the selected timeframe from original video
6. **Detect Face**: Analyzes first 30 frames to find optimal face position
7. **Crop Vertical**: Creates 9:16 aspect ratio with static face-centered crop
8. **Add Subtitles**: Burns stylized captions with Franklin Gothic font
9. **Combine Audio**: Merges audio track with final video

**Output**: `Final.mp4` in the project directory

## Configuration

### Subtitle Styling
Edit `Components/Subtitles.py` to customize:
- **Font**: Line 51 (`font='Franklin-Gothic'`)
- **Font Size**: Line 47 (`fontsize=80`)
- **Text Color**: Line 48 (`color='#2699ff'`)
- **Outline Color**: Line 49 (`stroke_color='black'`)
- **Outline Width**: Line 50 (`stroke_width=2`)

### Highlight Selection
Edit `Components/LanguageTasks.py` to customize:
- **Prompt**: Line 28 (adjust what makes content "interesting")
- **Model**: Line 54 (`model="gpt-4o-mini"`)
- **Temperature**: Line 55 (`temperature=1.0`)

### Video Quality
Edit `Components/Subtitles.py` and `Components/FaceCrop.py`:
- **Bitrate**: Line 74 in Subtitles.py (`bitrate='3000k'`)
- **Preset**: Line 73 (`preset='medium'`)

## Troubleshooting

### CUDA/GPU Issues
If transcription fails with CUDA errors:
```bash
# Verify CUDA libraries are accessible
export LD_LIBRARY_PATH=$(find $(pwd)/venv/lib/python3.10/site-packages/nvidia -name "lib" -type d | paste -sd ":" -)
```
The `run.sh` script handles this automatically.

### No Subtitles Appearing
Ensure ImageMagick policy allows file operations:
```bash
grep 'pattern="@\*"' /etc/ImageMagick-6/policy.xml
# Should show: rights="read|write"
```

### Face Detection Issues
- Ensure video has visible faces in first 30 frames
- For low-resolution videos, face detection may be less reliable
- Adjust `minSize` parameter in `FaceCrop.py` if needed

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


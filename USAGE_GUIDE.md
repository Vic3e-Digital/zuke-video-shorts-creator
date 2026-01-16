# AI YouTube Shorts Generator - Usage Guide

## New Features

### Multiple Clips Generation
You can now generate multiple viral clips from a single video with configurable number of clips (default: 3).

### Multiple Output Types
Generate different variations of each clip:
- `original`: Cropped to vertical format without subtitles
- `subtitled`: Cropped to vertical format with subtitles 
- `original-subtitled`: Original aspect ratio with subtitles

## Command Line Usage

### Basic Usage (3 clips, original + subtitled outputs)
```bash
python main.py "https://youtube.com/watch?v=VIDEO_ID"
```

### Custom Number of Clips
```bash
# Generate 5 clips
python main.py --clips 5 "https://youtube.com/watch?v=VIDEO_ID"

# Generate 1 clip (backward compatible)
python main.py --clips 1 "https://youtube.com/watch?v=VIDEO_ID"
```

### Custom Output Types
```bash
# Only original cuts (no subtitles)
python main.py --output-types original "https://youtube.com/watch?v=VIDEO_ID"

# Only subtitled cuts
python main.py --output-types subtitled "https://youtube.com/watch?v=VIDEO_ID"

# All three types
python main.py --output-types original subtitled original-subtitled "https://youtube.com/watch?v=VIDEO_ID"

# Original aspect ratio with subtitles only
python main.py --output-types original-subtitled "https://youtube.com/watch?v=VIDEO_ID"
```

### Batch Processing (Auto-approve)
```bash
# Auto-approve selections for batch processing
python main.py --auto-approve --clips 5 "https://youtube.com/watch?v=VIDEO_ID"
```

### Local Files
```bash
# Process local video file
python main.py --clips 3 "/path/to/video.mp4"
```

## Output File Naming

Files are now named with descriptive patterns:
- `{video_title}_clip1_{session_id}_original.mp4`
- `{video_title}_clip1_{session_id}_subtitled.mp4`
- `{video_title}_clip2_{session_id}_original_subtitled.mp4`
- etc.

## Examples

### Generate 3 clips with all output types:
```bash
python main.py --clips 3 --output-types original subtitled original-subtitled "https://youtube.com/watch?v=dQw4w9WgXcQ"
```

This will create 9 files total (3 clips × 3 output types).

### Quick single clip with subtitles:
```bash
python main.py --clips 1 --output-types subtitled "https://youtube.com/watch?v=dQw4w9WgXcQ"
```

This will create 1 file (1 clip × 1 output type).

### Batch process 5 clips, original cuts only:
```bash
python main.py --auto-approve --clips 5 --output-types original "https://youtube.com/watch?v=dQw4w9WgXcQ"
```

This will create 5 files automatically without user interaction.

## Interactive Mode

When not using `--auto-approve`, the system will:
1. Show you all selected clips with time ranges and content previews
2. Allow you to approve, regenerate, or cancel
3. Auto-approve after 15 seconds if no input

## Output Types Explained

1. **original**: Cropped to 9:16 aspect ratio, no subtitles - perfect for platforms that handle their own subtitles
2. **subtitled**: Cropped to 9:16 aspect ratio, with burned-in subtitles - ready for immediate upload
3. **original-subtitled**: Maintains original aspect ratio, with burned-in subtitles - good for platforms that support various aspect ratios

## Migration from Old Version

The old single-clip behavior is preserved when using `--clips 1`. All existing scripts should continue to work unchanged.
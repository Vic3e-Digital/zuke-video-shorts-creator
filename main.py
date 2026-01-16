from Components.YoutubeDownloader import download_youtube_video
from Components.Edit import extractAudio, crop_video
from Components.Transcription import transcribeAudio
from Components.LanguageTasks import GetHighlight, GetMultipleHighlights
from Components.FaceCrop import crop_to_vertical, combine_videos
from Components.Subtitles import add_subtitles_to_video
from Components.MultiClipProcessor import process_multiple_clips
import sys
import os
import uuid
import re
import argparse

def upload_to_cloudinary(file_path, cloud_name, upload_preset):
    """Upload video to Cloudinary and return the public URL"""
    try:
        import cloudinary
        import cloudinary.uploader
        
        # Configure Cloudinary for unsigned uploads
        cloudinary.config(
            cloud_name=cloud_name,
            secure=True
        )
        
        print(f"Uploading {os.path.basename(file_path)} to Cloudinary...")
        
        # Upload the video with unsigned preset
        response = cloudinary.uploader.unsigned_upload(
            file_path,
            upload_preset,
            resource_type="video",
            folder="ai-youtube-shorts"
        )
        
        public_url = response.get('secure_url')
        public_id = response.get('public_id')
        
        print(f"✓ Upload successful!")
        print(f"📹 Video URL: {public_url}")
        print(f"📄 Public ID: {public_id}")
        
        return public_url, public_id
        
    except ImportError:
        print("⚠️ Cloudinary library not installed. Skipping upload.")
        print("   Install with: pip install cloudinary")
        return None, None
    except Exception as e:
        print(f"❌ Upload failed: {str(e)}")
        return None, None

# Set up argument parser
parser = argparse.ArgumentParser(description='AI YouTube Shorts Generator')
parser.add_argument('input', nargs='?', help='YouTube video URL or local video file path')
parser.add_argument('--auto-approve', action='store_true', help='Auto-approve selections without user input')
parser.add_argument('--clips', type=int, default=3, help='Number of clips to generate (default: 3)')
parser.add_argument('--output-types', nargs='+', 
                   choices=['original', 'subtitled', 'original-subtitled', 'original-dimension'], 
                   default=['original', 'original-dimension', 'subtitled'],
                   help='Types of outputs to generate (default: original, original-dimension, subtitled)')

args = parser.parse_args()

# Generate unique session ID for this run (for concurrent execution support)
session_id = str(uuid.uuid4())[:8]
print(f"Session ID: {session_id}")
print(f"Clips to generate: {args.clips}")
print(f"Output types: {args.output_types}")

auto_approve = args.auto_approve
num_clips = args.clips
output_types = args.output_types

# Get input URL/file
if args.input:
    url_or_file = args.input
    print(f"Using input from command line: {url_or_file}")
else:
    url_or_file = input("Enter YouTube video URL or local video file path: ")

# Check if input is a local file
video_title = None
if os.path.isfile(url_or_file):
    print(f"Using local video file: {url_or_file}")
    Vid = url_or_file
    # Extract title from filename
    video_title = os.path.splitext(os.path.basename(url_or_file))[0]
else:
    # Assume it's a YouTube URL
    print(f"Downloading from YouTube: {url_or_file}")
    Vid = download_youtube_video(url_or_file)
    if Vid:
        Vid = Vid.replace(".webm", ".mp4")
        print(f"Downloaded video and audio files successfully! at {Vid}")
        # Extract title from downloaded file path
        video_title = os.path.splitext(os.path.basename(Vid))[0]

# Clean and slugify title for filename
def clean_filename(title):
    # Convert to lowercase
    cleaned = title.lower()
    # Remove or replace invalid filename characters
    cleaned = re.sub(r'[<>:"/\\|?*\[\]]', '', cleaned)
    # Replace spaces and underscores with hyphens
    cleaned = re.sub(r'[\s_]+', '-', cleaned)
    # Remove multiple consecutive hyphens
    cleaned = re.sub(r'-+', '-', cleaned)
    # Remove leading/trailing hyphens
    cleaned = cleaned.strip('-')
    # Limit length
    return cleaned[:80]

# Process video (works for both local files and downloaded videos)
if Vid:
    # Create unique temporary filenames
    audio_file = f"audio_{session_id}.wav"
    temp_clip = f"temp_clip_{session_id}.mp4"
    temp_cropped = f"temp_cropped_{session_id}.mp4"
    temp_subtitled = f"temp_subtitled_{session_id}.mp4"
    
    Audio = extractAudio(Vid, audio_file)
    if Audio:

        transcriptions = transcribeAudio(Audio)
        if len(transcriptions) > 0:
            print(f"\n{'='*60}")
            print(f"TRANSCRIPTION SUMMARY: {len(transcriptions)} segments")
            print(f"{'='*60}\n")
            TransText = ""

            for text, start, end in transcriptions:
                TransText += (f"{start} - {end}: {text}\n")

            print(f"Analyzing transcription to find {num_clips} best highlights...")
            
            # Get multiple highlights if more than 1 clip requested
            if num_clips > 1:
                highlights = GetMultipleHighlights(TransText, num_clips)
            else:
                # Use single highlight function for backwards compatibility
                start, stop = GetHighlight(TransText)
                if start is not None and stop is not None:
                    highlights = [{'start': start, 'end': stop, 'content': 'Single highlight'}]
                else:
                    highlights = []
            
            # Check if we got valid highlights
            if not highlights:
                print(f"\n{'='*60}")
                print("ERROR: Failed to get highlights from LLM")
                print(f"{'='*60}")
                print("This could be due to:")
                print("  - OpenAI API issues or rate limiting")
                print("  - Invalid API key")
                print("  - Network connectivity problems")
                print("  - Malformed transcription data")
                print(f"\nTranscription summary:")
                print(f"  Total segments: {len(transcriptions)}")
                print(f"  Total length: {len(TransText)} characters")
                print(f"{'='*60}\n")
                sys.exit(1)
            
            # Interactive approval loop (skip if auto-approve)
            import select
            
            approved = auto_approve
            
            if not auto_approve:
                while not approved:
                    print(f"\n{'='*60}")
                    print(f"SELECTED HIGHLIGHTS ({len(highlights)} clips):")
                    print(f"{'='*60}")
                    for i, highlight in enumerate(highlights, 1):
                        duration = highlight['end'] - highlight['start']
                        print(f"Clip {i}: {highlight['start']}s - {highlight['end']}s ({duration}s duration)")
                        if 'content' in highlight:
                            preview = highlight['content'][:100] + '...' if len(highlight['content']) > 100 else highlight['content']
                            print(f"  Content: {preview}")
                    print(f"Output types: {output_types}")
                    print(f"{'='*60}\n")
                    
                    print("Options:")
                    print("  [Enter/y] Approve and continue")
                    print("  [r] Regenerate selections")
                    print("  [n] Cancel")
                    print("\nAuto-approving in 15 seconds if no input...")
                    
                    try:
                        ready, _, _ = select.select([sys.stdin], [], [], 15)
                        if ready:
                            user_input = sys.stdin.readline().strip().lower()
                            if user_input == 'r':
                                print("\nRegenerating selections...")
                                if num_clips > 1:
                                    highlights = GetMultipleHighlights(TransText, num_clips)
                                else:
                                    start, stop = GetHighlight(TransText)
                                    if start is not None and stop is not None:
                                        highlights = [{'start': start, 'end': stop, 'content': 'Single highlight'}]
                                    else:
                                        highlights = []
                                continue
                            elif user_input == 'n':
                                print("Cancelled by user")
                                sys.exit(0)
                            else:
                                print("Approved by user")
                                approved = True
                        else:
                            print("\nTimeout - auto-approving selections")
                            approved = True
                    except:
                        print("\nAuto-approving (timeout not available on this platform)")
                        approved = True
            else:
                print(f"\n{'='*60}")
                print(f"SELECTED HIGHLIGHTS ({len(highlights)} clips):")
                print(f"{'='*60}")
                for i, highlight in enumerate(highlights, 1):
                    duration = highlight['end'] - highlight['start']
                    print(f"Clip {i}: {highlight['start']}s - {highlight['end']}s ({duration}s duration)")
                print(f"Output types: {output_types}")
                print(f"{'='*60}")
                print("Auto-approved (batch mode)\n")
            
            # Process all clips
            clean_title = clean_filename(video_title) if video_title else "output"
            all_outputs = process_multiple_clips(
                Vid, highlights, transcriptions, session_id, clean_title, output_types
            )
            
            # Print summary
            print(f"\n{'='*60}")
            print(f"✅ SUCCESS: Generated {len(highlights)} clips with {len(output_types)} variations each")
            print(f"{'='*60}")
            
            total_files = 0
            for clip_num, clip_data in all_outputs.items():
                print(f"\nClip {clip_num}:")
                highlight = clip_data['highlight']
                duration = highlight['end'] - highlight['start']
                print(f"  Time: {highlight['start']}s - {highlight['end']}s ({duration}s)")
                print(f"  Files created:")
                for file_path in clip_data['files']:
                    print(f"    - {file_path}")
                    total_files += 1
            
            print(f"\nTotal files created: {total_files}")
            print(f"{'='*60}\n")
            
            # Upload to Cloudinary if credentials are available
            cloudinary_cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME')
            cloudinary_upload_preset = os.getenv('CLOUDINARY_UPLOAD_PRESET')
            
            # Cloudinary upload disabled - future: implement Azure Storage
            print("ℹ️  Cloud upload disabled (will be replaced with Azure Storage in future)")
            
            # Clean up audio file
            try:
                if os.path.exists(audio_file):
                    os.remove(audio_file)
                print(f"\n🧹 Cleaned up temporary files for session {session_id}")
            except Exception as e:
                print(f"Warning: Could not clean up audio file: {e}")
        else:
            print("No transcriptions found")
    else:
        print("No audio file found")
else:
    print("Unable to process the video")
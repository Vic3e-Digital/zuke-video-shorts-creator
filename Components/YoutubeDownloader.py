import os
import sys
import yt_dlp
import re

def sanitize_filename(filename):
    """Sanitize filename to be filesystem-safe"""
    # Remove or replace problematic characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = re.sub(r'\s+', ' ', filename).strip()
    return filename

def download_youtube_video(url):
    try:
        if not os.path.exists('videos'):
            os.makedirs('videos')
        
        # First, get video info to show available formats
        print("Fetching video information...")
        ydl_opts_info = {
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'video')
            formats = info.get('formats', [])
            
            # Filter and sort video formats (only those with video)
            video_formats = [
                f for f in formats 
                if f.get('vcodec') != 'none' and f.get('height') is not None
            ]
            video_formats = sorted(video_formats, key=lambda x: x.get('height', 0), reverse=True)
            
            # Get unique resolutions (deduplicate)
            seen_heights = set()
            unique_formats = []
            for fmt in video_formats:
                height = fmt.get('height')
                if height and height not in seen_heights and len(unique_formats) < 5:
                    seen_heights.add(height)
                    unique_formats.append(fmt)
            
            if not unique_formats:
                print("No suitable video formats found, using best available...")
                selected_format = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            else:
                # Show available streams
                print("\nAvailable video streams:")
                for i, fmt in enumerate(unique_formats):
                    height = fmt.get('height', 'N/A')
                    filesize = fmt.get('filesize') or fmt.get('filesize_approx', 0)
                    size_mb = filesize / (1024 * 1024) if filesize else 0
                    fps = fmt.get('fps', 'N/A')
                    ext = fmt.get('ext', 'N/A')
                    print(f"  {i}. Resolution: {height}p, Size: ~{size_mb:.1f} MB, FPS: {fps}, Format: {ext}")
                
                # Interactive selection with timeout
                print("\nSelect resolution number (0-{}) or wait 5s for auto-select...".format(len(unique_formats)-1))
                print("Auto-selecting highest quality in 5 seconds...")
                
                selected_idx = None
                try:
                    # Platform-independent timeout input
                    import select
                    if hasattr(select, 'select'):
                        ready, _, _ = select.select([sys.stdin], [], [], 5)
                        if ready:
                            user_input = sys.stdin.readline().strip()
                            if user_input.isdigit():
                                choice = int(user_input)
                                if 0 <= choice < len(unique_formats):
                                    selected_idx = choice
                                    print(f"✓ User selected: {unique_formats[choice]['height']}p")
                                else:
                                    print("Invalid choice, using highest quality")
                            else:
                                print("Invalid input, using highest quality")
                        else:
                            print("\nTimeout - auto-selecting highest quality")
                    else:
                        print("\nAuto-selecting highest quality (timeout not available on this platform)")
                except:
                    print("\nAuto-selecting highest quality")
                
                # Use selected format or default to best
                if selected_idx is not None:
                    format_id = unique_formats[selected_idx]['format_id']
                    selected_format = f"{format_id}+bestaudio/best"
                    print(f"\nFinal selection: {unique_formats[selected_idx]['height']}p")
                else:
                    selected_format = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
                    print(f"\nFinal selection: {unique_formats[0]['height']}p (highest quality)")
        
        # Download with selected format
        safe_title = sanitize_filename(title)
        output_template = os.path.join('videos', f"{safe_title}.%(ext)s")
        
        ydl_opts = {
            'format': selected_format,
            'outtmpl': output_template,
            'merge_output_format': 'mp4',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
        }
        
        print(f"Downloading video: {title}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        output_file = os.path.join('videos', f"{safe_title}.mp4")
        print(f"Downloaded: {title} to 'videos' folder")
        print(f"File path: {output_file}")
        return output_file

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("Please make sure you have the latest version of yt-dlp installed.")
        print("You can update it by running:")
        print("pip install --upgrade yt-dlp")
        print("Also, ensure that ffmpeg is installed on your system and available in your PATH.")
        return None

if __name__ == "__main__":
    youtube_url = input("Enter YouTube video URL: ")
    download_youtube_video(youtube_url)

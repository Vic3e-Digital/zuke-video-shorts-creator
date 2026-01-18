import os
import sys
import yt_dlp
import re
import random

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
        
        # Check if cookies file exists
        cookies_file = os.path.join(os.getcwd(), 'youtube_cookies.txt')
        use_cookies = os.path.exists(cookies_file)
        
        # Try to use browser cookies as fallback
        browser_cookies = os.environ.get('YOUTUBE_COOKIES_BROWSER', None)  # e.g., 'chrome', 'firefox'
        
        if use_cookies:
            print(f"✓ Using cookies from: {cookies_file}")
        elif browser_cookies:
            print(f"✓ Will extract cookies from browser: {browser_cookies}")
        else:
            print("⚠️  No cookies configured. YouTube may block requests.")
            print("   Options:")
            print("   1. Place 'youtube_cookies.txt' in the app directory")
            print("   2. Set YOUTUBE_COOKIES_BROWSER env var (e.g., 'chrome')")
        
        # First, get video info to show available formats
        print("Fetching video information...")
        
        # Rotate between different clients to avoid detection
        client_combinations = [
            ['ios', 'android'],
            ['android', 'web'],
            ['tv', 'ios'],
            ['web_creator', 'android'],
            ['ios', 'web'],
            ['android'],
        ]
        selected_clients = random.choice(client_combinations)
        print(f"Using player clients: {', '.join(selected_clients)}")
        
        ydl_opts_info = {
            'quiet': True,
            'no_warnings': True,
            'extractor_args': {
                'youtube': {
                    'player_client': selected_clients,
                    'skip': ['hls', 'dash', 'translated_subs']
                }
            },
            'http_headers': {
                'User-Agent': 'com.google.ios.youtube/19.29.1 (iPhone16,2; U; CPU iOS 17_5_1 like Mac OS X;)',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            },
            # Age gate bypass
            'age_limit': None,
            # Retry settings
            'retries': 10,
            'fragment_retries': 10,
            'skip_unavailable_fragments': True,
            # Sleep between requests (be polite to YouTube)
            'sleep_interval': 1,
            'max_sleep_interval': 5,
            'sleep_interval_requests': 1,
        }
        
        # Add cookies configuration
        if use_cookies:
            ydl_opts_info['cookiefile'] = cookies_file
        elif browser_cookies:
            ydl_opts_info['cookiesfrombrowser'] = (browser_cookies,)
        
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
            'extractor_args': {
                'youtube': {
                    'player_client': selected_clients,
                    'skip': ['hls', 'dash', 'translated_subs']
                }
            },
            'http_headers': {
                'User-Agent': 'com.google.ios.youtube/19.29.1 (iPhone16,2; U; CPU iOS 17_5_1 like Mac OS X;)',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            },
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
            # Age gate bypass
            'age_limit': None,
            # Retry settings for reliability
            'retries': 10,
            'fragment_retries': 10,
            'skip_unavailable_fragments': True,
            # Sleep between requests
            'sleep_interval': 1,
            'max_sleep_interval': 5,
            'sleep_interval_requests': 1,
        }
        
        # Add cookies configuration
        if use_cookies:
            ydl_opts['cookiefile'] = cookies_file
        elif browser_cookies:
            ydl_opts['cookiesfrombrowser'] = (browser_cookies,)
        
        print(f"Downloading video: {title}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        output_file = os.path.join('videos', f"{safe_title}.mp4")
        print(f"Downloaded: {title} to 'videos' folder")
        print(f"File path: {output_file}")
        return output_file

    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        print(f"Download error: {error_msg}")
        
        if "Sign in to confirm" in error_msg or "bot" in error_msg.lower():
            print("\n🤖 YouTube detected automated access. Solutions:")
            print("\n1. UPDATE YOUR COOKIES (Recommended):")
            print("   Your cookies may be expired. Export fresh cookies from your browser:")
            print("   a. Install 'Get cookies.txt LOCALLY' extension")
            print("   b. Sign in to YouTube in your browser")
            print("   c. Export cookies and replace youtube_cookies.txt")
            print("\n2. USE BROWSER COOKIES DIRECTLY:")
            print("   Set environment variable: YOUTUBE_COOKIES_BROWSER=chrome")
            print("   (or 'firefox', 'edge', 'safari', 'brave')")
            print("\n3. UPDATE yt-dlp:")
            print("   pip install --upgrade yt-dlp")
            print("\n4. Try a different video or wait a few minutes before retrying")
        
        return None
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

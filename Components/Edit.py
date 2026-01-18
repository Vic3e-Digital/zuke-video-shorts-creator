from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.editor import VideoFileClip
import subprocess

def extractAudio(video_path, audio_path="audio.wav"):
    try:
        video_clip = VideoFileClip(video_path)
        video_clip.audio.write_audiofile(audio_path)
        video_clip.close()
        print(f"Extracted audio to: {audio_path}")
        return audio_path
    except Exception as e:
        print(f"An error occurred while extracting audio: {e}")
        return None


def crop_video(input_file, output_file, start_time, end_time):
    """Crop video to specified time range with proper resource management."""
    video = None
    cropped_video = None
    
    try:
        video = VideoFileClip(input_file)
        
        # Ensure end_time doesn't exceed video duration
        max_time = video.duration - 0.1  # Small buffer to avoid edge cases
        if end_time > max_time:
            print(f"Warning: Requested end time ({end_time}s) exceeds video duration ({video.duration}s). Capping to {max_time}s")
            end_time = max_time
        
        cropped_video = video.subclip(start_time, end_time)
        cropped_video.write_videofile(
            output_file, 
            codec='libx264', 
            audio_codec='aac',
            threads=2,
            logger=None
        )
        
    except Exception as e:
        print(f"❌ Error cropping video: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
        
    finally:
        # Clean up resources
        try:
            if cropped_video:
                cropped_video.close()
            if video:
                video.close()
        except Exception as cleanup_error:
            print(f"Warning: Error during crop cleanup: {cleanup_error}")

# Example usage:
if __name__ == "__main__":
    input_file = r"Example.mp4" ## Test
    print(input_file)
    output_file = "Short.mp4"
    start_time = 31.92 
    end_time = 49.2   

    crop_video(input_file, output_file, start_time, end_time)


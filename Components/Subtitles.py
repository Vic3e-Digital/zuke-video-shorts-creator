from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
import re
import os

def add_subtitles_to_video(input_video, output_video, transcriptions, video_start_time=0):
    """
    Add subtitles to video based on transcription segments.
    Includes proper memory management and error handling.
    
    Args:
        input_video: Path to input video file
        output_video: Path to output video file
        transcriptions: List of [text, start, end] from transcribeAudio
        video_start_time: Start time offset if video was cropped
    """
    video = None
    final_video = None
    text_clips = []
    
    try:
        video = VideoFileClip(input_video)
        video_duration = video.duration
        
        # Filter transcriptions to only those within the video timeframe
        relevant_transcriptions = []
        for text, start, end in transcriptions:
            # Adjust times relative to video start
            adjusted_start = start - video_start_time
            adjusted_end = end - video_start_time
            
            # Only include if within video duration
            if adjusted_end > 0 and adjusted_start < video_duration:
                adjusted_start = max(0, adjusted_start)
                adjusted_end = min(video_duration, adjusted_end)
                relevant_transcriptions.append([text.strip(), adjusted_start, adjusted_end])
        
        if not relevant_transcriptions:
            print("No transcriptions found for this video segment")
            video.write_videofile(
                output_video, 
                codec='libx264', 
                audio_codec='aac',
                threads=2,
                logger=None
            )
            return
        
        # Get subtitle styling from environment variables with defaults
        subtitle_font = os.getenv('SUBTITLE_FONT', 'Franklin-Gothic')
        subtitle_size_ratio = float(os.getenv('SUBTITLE_SIZE_RATIO', '0.065'))
        subtitle_color = os.getenv('SUBTITLE_COLOR', '#2699ff')
        subtitle_stroke_color = os.getenv('SUBTITLE_STROKE_COLOR', 'black')
        subtitle_stroke_width = int(os.getenv('SUBTITLE_STROKE_WIDTH', '2'))
        
        # Scale font size proportionally to video height
        # 1080p → 70px, 720p → 47px (with default 0.065 ratio)
        dynamic_fontsize = int(video.h * subtitle_size_ratio)
        
        for text, start, end in relevant_transcriptions:
            # Clean up text
            text = text.strip()
            if not text:
                continue
                
            try:
                # Create text clip with configurable styling
                txt_clip = TextClip(
                    text,
                    fontsize=dynamic_fontsize,
                    color=subtitle_color,
                    stroke_color=subtitle_stroke_color,
                    stroke_width=subtitle_stroke_width,
                    font=subtitle_font,
                    method='caption',
                    size=(video.w - 100, None)  # Leave 50px margin on each side
                )
                
                # Position between middle and bottom (at 75% of video height)
                txt_clip = txt_clip.set_position(('center', video.h * 0.75))
                txt_clip = txt_clip.set_start(start)
                txt_clip = txt_clip.set_duration(end - start)
                
                text_clips.append(txt_clip)
            except Exception as clip_error:
                print(f"⚠️ Warning: Failed to create subtitle clip for '{text[:30]}...': {clip_error}")
                continue
        
        if not text_clips:
            print("⚠️ Warning: No subtitle clips could be created, saving video without subtitles")
            video.write_videofile(
                output_video,
                codec='libx264',
                audio_codec='aac',
                threads=2,
                logger=None
            )
            return
        
        # Composite video with subtitles
        print(f"Adding {len(text_clips)} subtitle segments to video...")
        final_video = CompositeVideoClip([video] + text_clips)
        
        # Write output with memory-conscious settings
        final_video.write_videofile(
            output_video,
            codec='libx264',
            audio_codec='aac',
            fps=video.fps,
            preset='medium',
            bitrate='3000k',
            threads=2,  # Limit threads to reduce memory
            logger=None  # Reduce console output
        )
        
        print(f"✓ Subtitles added successfully -> {output_video}")
        
    except Exception as e:
        print(f"❌ Error adding subtitles: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
        
    finally:
        # Critical: Clean up all clips to free memory
        try:
            for clip in text_clips:
                clip.close()
            if final_video:
                final_video.close()
            if video:
                video.close()
        except Exception as cleanup_error:
            print(f"Warning: Error during subtitle cleanup: {cleanup_error}")

import os
from Components.Edit import crop_video
from Components.FaceCrop import crop_to_vertical, combine_videos
from Components.Subtitles import add_subtitles_to_video

def create_output_variations(original_video, highlight, transcriptions, session_id, video_title, output_types):
    """
    Create different variations of the output video based on the requested types.
    
    Args:
        original_video: Path to the original video file
        highlight: Dictionary containing 'start' and 'end' times
        transcriptions: List of transcription segments
        session_id: Unique session identifier
        video_title: Clean title for output filename
        output_types: List of output types to generate
        
    Returns:
        List of generated output files
    """
    start, end = highlight['start'], highlight['end']
    output_files = []
    failed_outputs = []
    
    # Ensure output directory exists
    os.makedirs('output', exist_ok=True)
    
    # Temporary file names
    temp_clip = f"temp_clip_{session_id}.mp4"
    temp_cropped = f"temp_cropped_{session_id}.mp4"
    temp_subtitled = f"temp_subtitled_{session_id}.mp4"
    
    try:
        # Step 1: Extract the clip from the original video
        print(f"Extracting clip: {start}s - {end}s ({end-start}s duration)")
        crop_video(original_video, temp_clip, start, end)
        
        # Step 2: Crop to vertical format (9:16) - needed for all variants except original-dimension
        needs_cropping = any(t in output_types for t in ['original', 'subtitled'])
        if needs_cropping:
            print("Cropping to vertical format (9:16)...")
            try:
                crop_to_vertical(temp_clip, temp_cropped)
            except Exception as e:
                print(f"⚠️ Warning: Cropping failed: {e}")
                print("   Continuing with other output types...")
                # Remove outputs that require cropping
                for out_type in ['original', 'subtitled']:
                    if out_type in output_types:
                        failed_outputs.append(out_type)
        
        for output_type in output_types:
            try:
                if output_type == 'original':
                    if 'original' in failed_outputs:
                        print(f"⏭️ Skipping 'original' (cropping failed)")
                        continue
                    # Original cropped video without subtitles
                    output_filename = os.path.join('output', f"{video_title}_{session_id}_original.mp4")
                    combine_videos(temp_clip, temp_cropped, output_filename)
                    output_files.append(output_filename)
                    print(f"✓ Created original cut: {output_filename}")
                    
                elif output_type == 'subtitled':
                    if 'subtitled' in failed_outputs:
                        print(f"⏭️ Skipping 'subtitled' (cropping failed)")
                        continue
                    # Cropped video with subtitles
                    print("Adding subtitles to video...")
                    add_subtitles_to_video(temp_cropped, temp_subtitled, transcriptions, video_start_time=start)
                    output_filename = os.path.join('output', f"{video_title}_{session_id}_subtitled.mp4")
                    combine_videos(temp_clip, temp_subtitled, output_filename)
                    output_files.append(output_filename)
                    print(f"✓ Created subtitled cut: {output_filename}")
                    
                elif output_type == 'original-subtitled':
                    # Full video with subtitles (uncropped aspect ratio)
                    print("Adding subtitles to uncropped video...")
                    temp_original_subtitled = f"temp_original_subtitled_{session_id}.mp4"
                    add_subtitles_to_video(temp_clip, temp_original_subtitled, transcriptions, video_start_time=start)
                    output_filename = os.path.join('output', f"{video_title}_{session_id}_original_subtitled.mp4")
                    # For original-subtitled, we combine the original clip with subtitles (no cropping)
                    os.rename(temp_original_subtitled, output_filename)
                    output_files.append(output_filename)
                    print(f"✓ Created original with subtitles: {output_filename}")
                    
                    # Clean up temp file
                    if os.path.exists(temp_original_subtitled):
                        os.remove(temp_original_subtitled)
                        
                elif output_type == 'original-dimension':
                    # Original video dimensions without cropping or subtitles
                    print("Creating clip with original dimensions...")
                    output_filename = os.path.join('output', f"{video_title}_{session_id}_original_dimension.mp4")
                    # Simply copy the temp_clip (which maintains original dimensions) to output
                    import shutil
                    shutil.copy2(temp_clip, output_filename)
                    output_files.append(output_filename)
                    print(f"✓ Created original dimension cut: {output_filename}")
                    
            except Exception as e:
                print(f"❌ Error creating '{output_type}' output: {e}")
                print(f"   Continuing with remaining output types...")
                failed_outputs.append(output_type)
                continue
        
        # Report summary
        if failed_outputs:
            print(f"\n⚠️ Some outputs failed: {', '.join(failed_outputs)}")
        if output_files:
            print(f"✓ Successfully created {len(output_files)}/{len(output_types)} output variations")
        
    except Exception as e:
        print(f"❌ Critical error in create_output_variations: {e}")
        print(f"   Attempting to return any files that were created...")
        
    finally:
        # Clean up temporary files
        for temp_file in [temp_clip, temp_cropped, temp_subtitled]:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception as e:
                    print(f"⚠️ Warning: Could not remove temp file {temp_file}: {e}")
    
    return output_files

def process_multiple_clips(original_video, highlights, transcriptions, session_id, video_title, output_types):
    """
    Process multiple clips with different output variations
    
    Returns:
        Dictionary mapping clip numbers to their output files
    """
    all_outputs = {}
    
    for i, highlight in enumerate(highlights, 1):
        print(f"\n{'='*60}")
        print(f"PROCESSING CLIP {i}/{len(highlights)}")
        print(f"Time: {highlight['start']}s - {highlight['end']}s")
        print(f"{'='*60}")
        
        # Create clip-specific title
        clip_title = f"{video_title}_clip{i}"
        
        # Generate output variations for this clip
        output_files = create_output_variations(
            original_video, highlight, transcriptions, 
            session_id, clip_title, output_types
        )
        
        all_outputs[i] = {
            'highlight': highlight,
            'files': output_files
        }
        
        print(f"✓ Completed clip {i}: {len(output_files)} variations created")
    
    return all_outputs
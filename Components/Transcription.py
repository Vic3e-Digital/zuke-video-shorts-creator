"""
Transcription module using faster-whisper (CPU-optimized)
"""

from faster_whisper import WhisperModel
import os

# Global model instance (loaded once)
_model = None

def get_whisper_model(model_size: str = "base"):
    """
    Load or return cached Whisper model.
    Uses faster-whisper with CTranslate2 backend (CPU-optimized).
    """
    global _model
    
    if _model is None:
        print(f"🎙️ Loading Whisper model: {model_size}")
        # Use CPU with int8 quantization for speed
        _model = WhisperModel(
            model_size, 
            device="cpu", 
            compute_type="int8"
        )
        print("✅ Whisper model loaded")
    
    return _model

def transcribeAudio(audio_path: str, model_size: str = "base") -> dict:
    """
    Transcribe audio file to text with timestamps.
    
    Args:
        audio_path: Path to audio file (mp3, wav, etc.)
        model_size: Whisper model size (tiny, base, small, medium, large)
    
    Returns:
        Dictionary with transcription results
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    
    model = get_whisper_model(model_size)
    
    print(f"📝 Transcribing: {audio_path}")
    
    # Transcribe with word-level timestamps
    segments, info = model.transcribe(
        audio_path,
        beam_size=5,
        word_timestamps=True,
        vad_filter=True  # Voice activity detection for better accuracy
    )
    
    # Convert generator to list and format results
    segments_list = []
    full_text = []
    
    for segment in segments:
        segment_data = {
            "start": segment.start,
            "end": segment.end,
            "text": segment.text.strip(),
        }
        
        # Include word-level timestamps if available
        if segment.words:
            segment_data["words"] = [
                {
                    "word": word.word,
                    "start": word.start,
                    "end": word.end,
                    "probability": word.probability
                }
                for word in segment.words
            ]
        
        segments_list.append(segment_data)
        full_text.append(segment.text.strip())
    
    result = {
        "text": " ".join(full_text),
        "segments": segments_list,
        "language": info.language,
        "language_probability": info.language_probability,
        "duration": info.duration
    }
    
    print(f"✅ Transcription complete: {len(segments_list)} segments, {info.duration:.1f}s duration")
    
    return result


def transcribe_with_timestamps(audio_path: str, model_size: str = "base") -> list:
    """
    Convenience function to get just the timestamped segments.
    
    Returns:
        List of segments with start, end, and text
    """
    result = transcribeAudio(audio_path, model_size)
    return result["segments"]


# For backwards compatibility
def transcribe(audio_path: str) -> str:
    """Simple transcription returning just the text."""
    result = transcribeAudio(audio_path)
    return result["text"]


if __name__ == "__main__":
    audio_path = "audio.wav"
    transcriptions = transcribeAudio(audio_path)
    
    print("\n📄 Full Text:")
    print(transcriptions["text"])
    
    print(f"\n⏱️ Segments ({len(transcriptions['segments'])}):")
    for segment in transcriptions["segments"]:
        print(f"{segment['start']:.2f}s - {segment['end']:.2f}s: {segment['text']}")
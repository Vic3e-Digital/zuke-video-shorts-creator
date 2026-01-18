import cv2
import numpy as np
import webrtcvad
import wave
import contextlib
from pydub import AudioSegment
import os
import urllib.request

# Get absolute path to models directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")

# Model file paths
prototxt_path = os.path.join(MODELS_DIR, "deploy.prototxt")
model_path = os.path.join(MODELS_DIR, "res10_300x300_ssd_iter_140000.caffemodel")
temp_audio_path = os.path.join(BASE_DIR, "temp_audio.wav")

def ensure_face_detection_models():
    """Download face detection models if they don't exist."""
    os.makedirs(MODELS_DIR, exist_ok=True)
    
    # Download prototxt if missing
    if not os.path.exists(prototxt_path):
        print("📥 Downloading face detection prototxt...")
        url = "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt"
        urllib.request.urlretrieve(url, prototxt_path)
        print(f"✅ Downloaded: {prototxt_path}")
    
    # Download caffemodel if missing
    if not os.path.exists(model_path):
        print("📥 Downloading face detection model (~10MB)...")
        url = "https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel"
        urllib.request.urlretrieve(url, model_path)
        print(f"✅ Downloaded: {model_path}")

# Ensure models exist before loading
ensure_face_detection_models()

# Load DNN model
print(f"🔄 Loading face detection model from: {model_path}")
net = cv2.dnn.readNetFromCaffe(prototxt_path, model_path)
print("✅ Face detection model loaded")

# Initialize VAD
vad = webrtcvad.Vad(2)  # Aggressiveness mode from 0 to 3

def voice_activity_detection(audio_frame, sample_rate=16000):
    return vad.is_speech(audio_frame, sample_rate)

def extract_audio_from_video(video_path, audio_path):
    audio = AudioSegment.from_file(video_path)
    audio = audio.set_frame_rate(16000).set_channels(1)
    audio.export(audio_path, format="wav")

def process_audio_frame(audio_data, sample_rate=16000, frame_duration_ms=30):
    n = int(sample_rate * frame_duration_ms / 1000) * 2  # 2 bytes per sample
    offset = 0
    while offset + n <= len(audio_data):
        frame = audio_data[offset:offset + n]
        offset += n
        yield frame

global Frames
Frames = []  # [x,y,w,h]

def detect_faces_and_speakers(input_video_path, output_video_path):
    # Return Frames:
    global Frames
    Frames = []  # Reset frames for each call
    
    # Extract audio from the video
    extract_audio_from_video(input_video_path, temp_audio_path)

    # Read the extracted audio
    with contextlib.closing(wave.open(temp_audio_path, 'rb')) as wf:
        sample_rate = wf.getframerate()
        audio_data = wf.readframes(wf.getnframes())

    cap = cv2.VideoCapture(input_video_path)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_path, fourcc, 30.0, (int(cap.get(3)), int(cap.get(4))))

    frame_duration_ms = 30  # 30ms frames
    audio_generator = process_audio_frame(audio_data, sample_rate, frame_duration_ms)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        h, w = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
        net.setInput(blob)
        detections = net.forward()

        audio_frame = next(audio_generator, None)
        if audio_frame is None:
            break
        is_speaking_audio = voice_activity_detection(audio_frame, sample_rate)
        MaxDif = 0
        Add = []
        face_found = False
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > 0.3:  # Confidence threshold
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (x, y, x1, y1) = box.astype("int")
                face_width = x1 - x
                face_height = y1 - y

                # Draw bounding box
                cv2.rectangle(frame, (x, y), (x1, y1), (0, 255, 0), 2)

                # Assuming lips are approximately at the bottom third of the face
                lip_distance = abs((y + 2 * face_height // 3) - (y1))
                Add.append([[x, y, x1, y1], lip_distance])

                MaxDif = max(lip_distance, MaxDif)
                face_found = True
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > 0.3:  # Confidence threshold
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (x, y, x1, y1) = box.astype("int")
                face_width = x1 - x
                face_height = y1 - y

                # Draw bounding box
                cv2.rectangle(frame, (x, y), (x1, y1), (0, 255, 0), 2)

                # Assuming lips are approximately at the bottom third of the face
                lip_distance = abs((y + 2 * face_height // 3) - (y1))
                # print(lip_distance)  # Commented out for cleaner logs

                # Combine visual and audio cues
                if lip_distance >= MaxDif and is_speaking_audio:  # Adjust the threshold as needed
                    cv2.putText(frame, "Active Speaker", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                if lip_distance >= MaxDif:
                    break

        if face_found:
            Frames.append([x, y, x1, y1])
        else:
            # If no face detected, append previous frame's values or None
            if len(Frames) > 0:
                Frames.append(Frames[-1])
            else:
                Frames.append(None)

        out.write(frame)

    cap.release()
    out.release()
    cv2.destroyAllWindows()
    
    # Clean up temp audio file
    if os.path.exists(temp_audio_path):
        os.remove(temp_audio_path)


if __name__ == "__main__":
    detect_faces_and_speakers("test_video.mp4", "output_video.mp4")
    print(Frames)
    print(len(Frames))
    print(Frames[1:5])
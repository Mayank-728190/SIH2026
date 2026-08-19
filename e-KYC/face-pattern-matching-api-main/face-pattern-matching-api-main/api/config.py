import os
import cv2 as cv
import urllib.request

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")

DETECTOR_URL = "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
RECOGNIZER_URL = "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx"

DETECTOR_PATH = os.path.join(MODEL_DIR, "face_detection_yunet_2023mar.onnx")
RECOGNIZER_PATH = os.path.join(MODEL_DIR, "face_recognition_sface_2021dec.onnx")

def download_model(url, path):
    if not os.path.exists(path):
        print(f"Downloading {os.path.basename(path)}...")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        urllib.request.urlretrieve(url, path)
        print("Download complete.")

class FaceVerifier:
    def __init__(self):
        download_model(DETECTOR_URL, DETECTOR_PATH)
        download_model(RECOGNIZER_URL, RECOGNIZER_PATH)
        
        # Initialize detector with default size, will be resized on inference
        self.detector = cv.FaceDetectorYN.create(
            model=DETECTOR_PATH,
            config="",
            input_size=(320, 320),
            score_threshold=0.8,
            nms_threshold=0.3,
            top_k=5000
        )
        
        # Initialize recognizer
        self.recognizer = cv.FaceRecognizerSF.create(
            model=RECOGNIZER_PATH,
            config=""
        )

# Global verifier instance to be used across requests
verifier = FaceVerifier()

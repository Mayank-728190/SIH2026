import cv2 as cv
import numpy as np
import base64

def image_to_base64(img):
    """Encodes an OpenCV image to a base64 string."""
    _, buffer = cv.imencode('.jpg', img)
    return base64.b64encode(buffer).decode('utf-8')

def read_image_from_bytes(data):
    """Reads bytes from a multipart upload and converts to an OpenCV image."""
    nparr = np.frombuffer(data, np.uint8)
    return cv.imdecode(nparr, cv.IMREAD_COLOR)

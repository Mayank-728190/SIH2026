import cv2 as cv
import numpy as np
from config import verifier
from utils import image_to_base64

def create_oval_face(image, face):
    """
    Create an oval face shape instead of rectangle or segmentation
    """
    try:
        x, y, w_face, h_face = face[:4].astype(int)
        x = max(0, x)
        y = max(0, y)
        w_face = min(w_face, image.shape[1] - x)
        h_face = min(h_face, image.shape[0] - y)
        
        center = (x + w_face//2, y + h_face//2)
        axes = (w_face//2, h_face//2)
        
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        cv.ellipse(mask, center, axes, 0, 0, 360, 255, -1)
        oval_face = cv.bitwise_and(image, image, mask=mask)
        
        return oval_face, mask, center, axes
    except Exception as e:
        print(f'Oval creation warning: {e}')
        return None, None, None, None

def convert_to_grayscale_enhanced(image):
    if len(image.shape) == 3:
        gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    try:
        clahe = cv.createCLAHE(clipLimit=2.5, tileGridSize=(8,8))
        return clahe.apply(gray)
    except:
        return gray

def detect_faces_with_oval(image):
    h, w = image.shape[:2]
    verifier.detector.setInputSize((w, h))
    _, faces = verifier.detector.detect(image)
    
    if faces is None or len(faces) == 0:
        gray = convert_to_grayscale_enhanced(image)
        gray_3channel = cv.cvtColor(gray, cv.COLOR_GRAY2BGR)
        verifier.detector.setInputSize((w, h))
        _, faces = verifier.detector.detect(gray_3channel)
    
    return faces

def get_embedding_safe(image, face):
    try:
        aligned = verifier.recognizer.alignCrop(image, face)
        embedding = verifier.recognizer.feature(aligned).flatten()
        
        if len(embedding) != 128:
            if len(embedding) < 128:
                padded = np.zeros(128)
                padded[:len(embedding)] = embedding
                embedding = padded
            else:
                embedding = embedding[:128]
        
        embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
        return embedding
    except:
        return np.random.randn(128) / np.sqrt(128)

def process_and_annotate_image(img, label_prefix="Face"):
    """
    Detects all faces, extracts embeddings, and draws oval annotations.
    Returns: annotated_image_b64, list_of_embeddings
    """
    gray_img = convert_to_grayscale_enhanced(img)
    gray_3channel = cv.cvtColor(gray_img, cv.COLOR_GRAY2BGR)
    
    faces = detect_faces_with_oval(img)
    if faces is None or len(faces) == 0:
        return None, []
    
    embeddings = []
    display_img = img.copy()
    
    for i, face in enumerate(faces):
        _, _, center, axes = create_oval_face(gray_3channel, face)
        embedding = get_embedding_safe(img, face)
        
        # Label each face uniquely (e.g., Face 1.1, Face 1.2)
        label = f"{label_prefix}.{i+1}" if len(faces) > 1 else label_prefix
        embeddings.append((label, embedding))
        
        if center is not None and axes is not None:
            cv.ellipse(display_img, center, axes, 0, 0, 360, (255, 255, 255), 2)
            inner_axes = (int(axes[0] * 0.85), int(axes[1] * 0.85))
            cv.ellipse(display_img, center, inner_axes, 0, 0, 360, (200, 200, 200), 1)
            
            (text_w, text_h), _ = cv.getTextSize(label, cv.FONT_HERSHEY_SIMPLEX, 0.7, 2)
            label_x = center[0] - text_w//2
            label_y = center[1] - axes[1] - 15
            
            label_x = max(10, min(label_x, display_img.shape[1] - text_w - 10))
            label_y = max(30, label_y)
            
            cv.rectangle(display_img, (label_x-5, label_y-25), (label_x+text_w+5, label_y), (0, 0, 0), -1)
            cv.putText(display_img, label, (label_x, label_y-5), 
                       cv.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                       
    annotated_b64 = image_to_base64(display_img)
    return annotated_b64, embeddings

def compare_faces(emb1, emb2):
    if emb1 is None or emb2 is None:
        return 0.0
    
    min_len = min(len(emb1), len(emb2))
    norm1 = emb1[:min_len] / (np.linalg.norm(emb1[:min_len]) + 1e-8)
    norm2 = emb2[:min_len] / (np.linalg.norm(emb2[:min_len]) + 1e-8)
    
    raw_sim = np.dot(norm1, norm2)
    scaled_sim = 1 / (1 + np.exp(-8 * (raw_sim - 0.25)))
    return scaled_sim

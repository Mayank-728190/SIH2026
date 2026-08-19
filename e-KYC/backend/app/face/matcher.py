import sys
import asyncio
import logging
import cv2 as cv
import numpy as np
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

FACE_MATCHER_DIR = r"c:\Users\user\Downloads\SIH26\e-KYC\face-pattern-matching-api-main\face-pattern-matching-api-main\api"
if FACE_MATCHER_DIR not in sys.path:
    sys.path.insert(0, FACE_MATCHER_DIR)

try:
    from services import process_and_annotate_image, compare_faces
except ImportError as e:
    logger.error(f"Failed to import Face matcher modules: {e}")

class FaceMatcherAdapter:
    @classmethod
    async def extract_face_embedding(cls, image_bytes: bytes) -> Optional[np.ndarray]:
        """
        Extracts the face embedding using the provided ONNX models.
        Runs securely in the backend. Never sends this embedding to the LLM.
        """
        def _extract():
            try:
                # Decode image from bytes
                nparr = np.frombuffer(image_bytes, np.uint8)
                img = cv.imdecode(nparr, cv.IMREAD_COLOR)
                if img is None:
                    return None
                    
                _, embeddings = process_and_annotate_image(img)
                if embeddings and len(embeddings) > 0:
                    # Return the embedding of the first face found
                    return embeddings[0][1] 
                return None
            except Exception as e:
                logger.error(f"Face extraction error: {e}")
                return None
                
        loop = asyncio.get_running_loop()
        embedding = await loop.run_in_executor(None, _extract)
        return embedding

    @classmethod
    async def compare_embeddings(cls, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """
        Compares two embeddings using the provided compare_faces logic.
        """
        def _compare():
            try:
                return float(compare_faces(emb1, emb2))
            except Exception as e:
                logger.error(f"Face comparison error: {e}")
                return 0.0
                
        loop = asyncio.get_running_loop()
        score = await loop.run_in_executor(None, _compare)
        return score

    @classmethod
    async def check_liveness(cls, video_frames: list[bytes]) -> bool:
        """
        Mock liveness check since no implementation was provided.
        Simulates an asynchronous liveness verification over multiple frames.
        """
        await asyncio.sleep(1) # Simulate processing
        logger.info("Mock liveness check passed.")
        return True

face_matcher = FaceMatcherAdapter()

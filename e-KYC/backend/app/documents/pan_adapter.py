import sys
import os
import asyncio
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Add the existing pan extractor to sys path so we can import its modules
PAN_EXTRACTOR_DIR = r"c:\Users\user\Downloads\SIH26\e-KYC\pan-extractor-main\pan-extractor-main"
if PAN_EXTRACTOR_DIR not in sys.path:
    sys.path.insert(0, PAN_EXTRACTOR_DIR)

# Import the specific modules from the existing implementation
try:
    from ocr.ocr_engine import extract_text
    from extraction.field_extractor import extract_fields
    from preprocessing.image_processor import preprocess_image, correct_perspective
except ImportError as e:
    logger.error(f"Failed to import PAN extractor modules: {e}")

class PANAdapter:
    @classmethod
    async def extract_pan_data(cls, image_path: str) -> Optional[Dict[str, Any]]:
        """
        Runs the PAN extraction pipeline asynchronously.
        Never sends this PII data to the LLM.
        """
        def _run_pipeline():
            try:
                # 1. Preprocess
                processed_image, processed_path = preprocess_image(image_path)
                
                # 2. Perspective (optional fallback)
                corrected_image, _ = correct_perspective(processed_image)
                
                # 3. OCR
                ocr_results = extract_text(corrected_image)
                
                if not ocr_results:
                    return None
                    
                # 4. Fields extraction
                fields = extract_fields(ocr_results)
                return fields
                
            except Exception as e:
                logger.error(f"PAN Extraction Error: {e}")
                return None

        # Run the CPU-heavy OpenCV/OCR code in a separate thread
        loop = asyncio.get_running_loop()
        fields = await loop.run_in_executor(None, _run_pipeline)
        
        return fields

pan_adapter = PANAdapter()

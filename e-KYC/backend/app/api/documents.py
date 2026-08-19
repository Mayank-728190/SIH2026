from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import logging

from app.db.mongodb import mongodb
from app.kyc.orchestrator import KYCOrchestrator
from app.models.session import KYCState, VerificationRecord
from app.documents.pan_adapter import pan_adapter
from app.documents.aadhaar_adapter import aadhaar_adapter
from app.face.matcher import face_matcher

logger = logging.getLogger(__name__)

router = APIRouter()

import asyncio

async def mock_process_document(session_id: str, document_type: str, delay_seconds: int = 5):
    """Mocks backend processing (OCR, Liveness, Face Match) taking time."""
    await asyncio.sleep(delay_seconds)
    
    # Update verification record securely
    record = await mongodb.get_verification_record(session_id)
    if not record:
        record = VerificationRecord(session_id=session_id)
        
    if document_type == "PAN":
        record.pan_name_score = 0.98
    elif document_type == "FACE":
        record.face_match_score = 0.95
        record.liveness = True
    elif document_type == "AADHAAR":
        record.aadhaar_name_score = 0.99
        
    await mongodb.save_verification_record(record)
    
    # Determine next state internally based on document type
    if document_type == "FACE":
        next_state = KYCState.PAN_CAPTURE
    elif document_type == "PAN":
        next_state = KYCState.AADHAAR_CAPTURE
    else:
        next_state = KYCState.APPROVED
        
    await KYCOrchestrator.transition_state(session_id, next_state, completed_step=f"{document_type}_CAPTURE")
    await mongodb.set_processing_status(session_id, "COMPLETED")

@router.post("/upload/pan")
async def upload_pan(session_id: str = Form(...), file: UploadFile = File(...)):
    logger.info(f"Received PAN upload for session {session_id}")
    session = await mongodb.get_session(session_id)
    if not session or session.capture_requested != "PAN":
        raise HTTPException(status_code=400, detail="Invalid session or capture not requested")
        
    idempotency_key = f"PAN_CAPTURE_{session.version}"
    success = await mongodb.start_processing(session_id, idempotency_key)
    if not success:
        return {"status": "ALREADY_CAPTURED"}
        
    # Start async processing
    asyncio.create_task(mock_process_document(session_id, "PAN", delay_seconds=5))
    return {"status": "SUCCESS", "capture_id": idempotency_key}

@router.post("/upload/face")
async def upload_face(session_id: str = Form(...), file: UploadFile = File(...)):
    logger.info(f"Received Face upload for session {session_id}")
    session = await mongodb.get_session(session_id)
    if not session or session.capture_requested != "FACE":
        raise HTTPException(status_code=400, detail="Invalid session or capture not requested")
        
    idempotency_key = f"FACE_CAPTURE_{session.version}"
    success = await mongodb.start_processing(session_id, idempotency_key)
    if not success:
        return {"status": "ALREADY_CAPTURED"}
        
    # Start async processing
    asyncio.create_task(mock_process_document(session_id, "FACE", delay_seconds=5))
    return {"status": "SUCCESS", "capture_id": idempotency_key}

@router.post("/upload/aadhaar")
async def upload_aadhaar(session_id: str = Form(...), file: UploadFile = File(...)):
    logger.info(f"Received Aadhaar upload for session {session_id}")
    session = await mongodb.get_session(session_id)
    if not session or session.capture_requested != "AADHAAR":
        raise HTTPException(status_code=400, detail="Invalid session or capture not requested")
        
    idempotency_key = f"AADHAAR_CAPTURE_{session.version}"
    success = await mongodb.start_processing(session_id, idempotency_key)
    if not success:
        return {"status": "ALREADY_CAPTURED"}
        
    # Start async processing
    asyncio.create_task(mock_process_document(session_id, "AADHAAR", delay_seconds=5))
    return {"status": "SUCCESS", "capture_id": idempotency_key}

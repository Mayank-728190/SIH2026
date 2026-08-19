from app.database.mongodb import get_db
from app.security.session_guard import require_verified_customer
from app.security.authorization import verify_task_ownership
import uuid
from datetime import datetime

async def create_dispute(session_id: str, transaction_id: str, amount: float, idempotency_key: str) -> dict:
    customer_id = await require_verified_customer(session_id)
    db = get_db()
    
    # Idempotency check
    existing_dispute = await db.support_tasks.find_one({
        "events.details.idempotency_key": idempotency_key
    })
    
    if existing_dispute:
        return {"status": "success", "message": "Dispute already created (idempotent return).", "task_id": existing_dispute["task_id"]}

    task_id = f"TASK_{uuid.uuid4().hex[:8].upper()}"
    
    new_task = {
        "task_id": task_id,
        "customer_id": customer_id,
        "task_type": "TRANSACTION_DISPUTE",
        "status": "COMPLETED",
        "current_step": "COMPLETED",
        "completed_steps": ["DISPUTE_CREATED"],
        "confirmed_data": {
            "transaction_id": transaction_id,
            "amount": amount
        },
        "pending_steps": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "events": [{
            "event_type": "DISPUTE_CREATED",
            "timestamp": datetime.utcnow(),
            "details": {"idempotency_key": idempotency_key, "transaction_id": transaction_id}
        }]
    }
    
    await db.support_tasks.insert_one(new_task)
    return {"status": "success", "task_id": task_id}

async def verify_security_question(session_id: str, answer: str) -> dict:
    from app.state.session_state import SessionManager
    from fastapi import HTTPException
    
    session = await SessionManager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    if answer.strip().lower() == "fluffy":
        session.verification_status = "SECURITY_PASSED"
        await SessionManager.update_session(session)
        return {"status": "success", "message": "Security question passed! Access granted."}
    else:
        return {"status": "failed", "message": "Incorrect answer. Please ask the user to try again."}

async def block_credit_card(session_id: str, card_last4: str, reason: str) -> dict:
    customer_id = await require_verified_customer(session_id)
    db = get_db()
    task_id = f"TASK_{uuid.uuid4().hex[:8].upper()}"
    new_task = {
        "task_id": task_id,
        "customer_id": customer_id,
        "task_type": "BLOCK_CREDIT_CARD",
        "status": "COMPLETED",
        "confirmed_data": {"card_last4": card_last4, "reason": reason},
        "created_at": datetime.utcnow()
    }
    await db.support_tasks.insert_one(new_task)
    return {"status": "success", "message": f"Credit card ending in {card_last4} has been blocked due to: {reason}."}

async def order_replacement_card(session_id: str, card_last4: str, shipping_speed: str) -> dict:
    customer_id = await require_verified_customer(session_id)
    db = get_db()
    task_id = f"TASK_{uuid.uuid4().hex[:8].upper()}"
    new_task = {
        "task_id": task_id,
        "customer_id": customer_id,
        "task_type": "ORDER_REPLACEMENT_CARD",
        "status": "COMPLETED",
        "confirmed_data": {"card_last4": card_last4, "shipping_speed": shipping_speed},
        "created_at": datetime.utcnow()
    }
    await db.support_tasks.insert_one(new_task)
    return {"status": "success", "message": f"A replacement for card ending in {card_last4} has been ordered with {shipping_speed} shipping."}

async def report_fraud(session_id: str, transaction_ids: list[str]) -> dict:
    customer_id = await require_verified_customer(session_id)
    db = get_db()
    task_id = f"TASK_{uuid.uuid4().hex[:8].upper()}"
    new_task = {
        "task_id": task_id,
        "customer_id": customer_id,
        "task_type": "REPORT_FRAUD",
        "status": "COMPLETED",
        "confirmed_data": {"transaction_ids": transaction_ids},
        "created_at": datetime.utcnow()
    }
    await db.support_tasks.insert_one(new_task)
    return {"status": "success", "message": f"Fraud has been reported for transactions: {', '.join(transaction_ids)}."}

async def update_billing_address(session_id: str, new_address: str) -> dict:
    customer_id = await require_verified_customer(session_id)
    db = get_db()
    task_id = f"TASK_{uuid.uuid4().hex[:8].upper()}"
    new_task = {
        "task_id": task_id,
        "customer_id": customer_id,
        "task_type": "UPDATE_BILLING_ADDRESS",
        "status": "COMPLETED",
        "confirmed_data": {"new_address": new_address},
        "created_at": datetime.utcnow()
    }
    await db.support_tasks.insert_one(new_task)
    return {"status": "success", "message": f"Billing address updated to: {new_address}."}

from app.database.mongodb import get_db

async def verify_task_ownership(task_id: str, customer_id: str) -> bool:
    db = get_db()
    task = await db.support_tasks.find_one({"task_id": task_id, "customer_id": customer_id})
    return task is not None

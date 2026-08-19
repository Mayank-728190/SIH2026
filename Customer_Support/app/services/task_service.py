from app.database.mongodb import get_db
from app.models.task import SupportTask
from datetime import datetime

class TaskService:
    @staticmethod
    async def save_task_state_on_disconnect(session_id: str, task_id: str, state_machine, heard_state):
        db = get_db()
        # Commit whatever was heard
        heard_state.commit_state()
        confirmed_data = heard_state.get_committed_state()
        
        # Determine pending vs completed steps
        completed_steps = state_machine.get_completed_steps()
        pending_steps = state_machine.get_pending_steps()

        await db.support_tasks.update_one(
            {"task_id": task_id},
            {
                "$set": {
                    "status": "IN_PROGRESS",
                    "current_step": state_machine.state,
                    "completed_steps": completed_steps,
                    "pending_steps": pending_steps,
                    "updated_at": datetime.utcnow()
                },
                "$currentDate": {"updated_at": True},
                "$push": {
                    "events": {
                        "event_type": "CALL_DISCONNECTED",
                        "timestamp": datetime.utcnow(),
                        "details": {"session_id": session_id, "state_saved": state_machine.state}
                    }
                }
            }
        )
        
        # update confirmed_data mapping fields selectively
        if confirmed_data:
            update_fields = {f"confirmed_data.{k}": v for k,v in confirmed_data.items()}
            await db.support_tasks.update_one(
                {"task_id": task_id},
                {"$set": update_fields}
            )

    @staticmethod
    async def resume_task(customer_id: str):
        db = get_db()
        task = await db.support_tasks.find_one({
            "customer_id": customer_id,
            "status": "IN_PROGRESS"
        })
        
        if not task:
            return None
        
        await db.support_tasks.update_one(
            {"_id": task["_id"]},
            {
                "$push": {
                    "events": {
                        "event_type": "TASK_RESUMED",
                        "timestamp": datetime.utcnow(),
                        "details": {"step": task["current_step"]}
                    }
                }
            }
        )
        return task

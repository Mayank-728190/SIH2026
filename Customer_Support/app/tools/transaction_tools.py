from app.database.mongodb import get_db
from app.security.session_guard import require_verified_customer
from typing import Dict, Any, List

async def get_recent_transactions(session_id: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Get recent transactions for the currently authenticated user."""
    customer_id = await require_verified_customer(session_id)
    db = get_db()
    
    cursor = db.transactions.find({"customer_id": customer_id}).sort("timestamp", -1).limit(limit)
    transactions = await cursor.to_list(length=limit)
    
    # Sanitize and minimize data returned to LLM
    result = []
    for tx in transactions:
        result.append({
            "transaction_id": tx["_id"],
            "amount": tx["amount"],
            "merchant": tx["merchant"],
            "timestamp": tx["timestamp"].isoformat(),
            "status": tx["status"]
        })
    return result

async def get_transaction_details(session_id: str, transaction_id: str) -> Dict[str, Any]:
    customer_id = await require_verified_customer(session_id)
    db = get_db()
    
    tx = await db.transactions.find_one({"_id": transaction_id, "customer_id": customer_id})
    if not tx:
        return {"error": "Transaction not found or access denied."}
        
    return {
        "transaction_id": tx["_id"],
        "amount": tx["amount"],
        "merchant": tx["merchant"],
        "timestamp": tx["timestamp"].isoformat(),
        "status": tx["status"]
    }

async def get_account_balance_and_summary(session_id: str) -> Dict[str, Any]:
    """Get the current account balance and a summary of top spending merchants."""
    customer_id = await require_verified_customer(session_id)
    db = get_db()
    
    # Calculate balance: Assuming simple aggregate over all transactions
    # In a real system, you'd have an Accounts collection. 
    # Here, we'll pretend initial balance is 50,000 and subtract total spending.
    # We will just do a simple aggregation to get total spent.
    
    pipeline = [
        {"$match": {"customer_id": customer_id}},
        {"$group": {
            "_id": "$merchant",
            "total_spent": {"$sum": "$amount"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"total_spent": -1}},
        {"$limit": 5}
    ]
    
    cursor = db.transactions.aggregate(pipeline)
    summary = await cursor.to_list(length=5)
    
    # Get total spent across all
    total_spent_cursor = db.transactions.aggregate([
        {"$match": {"customer_id": customer_id}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ])
    total_spent_res = await total_spent_cursor.to_list(length=1)
    total_spent = total_spent_res[0]["total"] if total_spent_res else 0
    
    # Provide a pretend balance calculation based on total spent
    starting_balance = 100000.0  # arbitrary starting balance
    current_balance = round(starting_balance - total_spent, 2)
    
    formatted_summary = []
    for s in summary:
        formatted_summary.append(f"{s['_id']}: {round(s['total_spent'], 2)} ({s['count']} transactions)")
        
    return {
        "current_balance": current_balance,
        "total_spent_historically": round(total_spent, 2),
        "top_spending_merchants": formatted_summary
    }

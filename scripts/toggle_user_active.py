#!/usr/bin/env python3
"""
Script to toggle a user's active status for testing.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import os
import sys
from dotenv import load_dotenv

load_dotenv()

async def toggle_user_active(username):
    # Connect to MongoDB
    client = AsyncIOMotorClient(os.getenv("MONGODB_URL", "mongodb://localhost:27017"))
    db = client[os.getenv("DATABASE_NAME", "personal_dev_tracker")]
    
    # Find the user
    user = await db.users.find_one({"username": username})
    
    if not user:
        print(f"User '{username}' not found.")
        return
    
    # Toggle the active status
    new_status = not user.get("is_active", False)
    
    result = await db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "is_active": new_status,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )
    
    if result.modified_count > 0:
        status_text = "activated" if new_status else "deactivated"
        print(f"Successfully {status_text} user '{username}'!")
        print(f"Active status: {new_status}")
    else:
        print(f"Failed to update user '{username}'.")
    
    # Close the connection
    client.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python toggle_user_active.py <username>")
        sys.exit(1)
    
    username = sys.argv[1]
    asyncio.run(toggle_user_active(username))
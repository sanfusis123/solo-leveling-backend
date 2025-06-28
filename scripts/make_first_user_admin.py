#!/usr/bin/env python3
"""
Script to make the first user in the database an admin.
Run this after creating your first user account.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import os
from dotenv import load_dotenv

load_dotenv()

async def make_first_user_admin():
    # Connect to MongoDB
    client = AsyncIOMotorClient(os.getenv("MONGODB_URL", "mongodb://localhost:27017"))
    db = client[os.getenv("DATABASE_NAME", "personal_dev_tracker")]
    
    # Find the first user (sorted by creation date)
    first_user = await db.users.find_one(sort=[("created_at", 1)])
    
    if not first_user:
        print("No users found in the database.")
        return
    
    # Update the user to be active and superuser
    result = await db.users.update_one(
        {"_id": first_user["_id"]},
        {
            "$set": {
                "is_active": True,
                "is_superuser": True,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )
    
    if result.modified_count > 0:
        print(f"Successfully made user '{first_user['username']}' an admin!")
        print(f"Email: {first_user['email']}")
        print("This user now has full admin privileges and can approve other users.")
    else:
        print(f"User '{first_user['username']}' is already an admin.")
    
    # Close the connection
    client.close()

if __name__ == "__main__":
    asyncio.run(make_first_user_admin())
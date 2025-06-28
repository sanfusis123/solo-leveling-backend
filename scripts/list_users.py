#!/usr/bin/env python3
"""
Script to list all users and their status.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

async def list_users():
    # Connect to MongoDB
    client = AsyncIOMotorClient(os.getenv("MONGODB_URL", "mongodb://localhost:27017"))
    db = client[os.getenv("DATABASE_NAME", "personal_dev_tracker")]
    
    # Find all users
    users = await db.users.find().to_list(length=None)
    
    if not users:
        print("No users found in the database.")
        return
    
    print(f"\nTotal users: {len(users)}\n")
    print(f"{'Username':<20} {'Email':<30} {'Active':<10} {'Admin':<10} {'Created'}")
    print("-" * 85)
    
    for user in users:
        username = user.get('username', 'N/A')
        email = user.get('email', 'N/A')
        is_active = "Yes" if user.get('is_active', False) else "No"
        is_admin = "Yes" if user.get('is_superuser', False) else "No"
        created = user.get('created_at', 'N/A')
        
        if created != 'N/A':
            created = created.strftime('%Y-%m-%d %H:%M')
        
        print(f"{username:<20} {email:<30} {is_active:<10} {is_admin:<10} {created}")
    
    # Close the connection
    client.close()

if __name__ == "__main__":
    asyncio.run(list_users())
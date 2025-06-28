from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.models.user import UserModel
from app.schemas.user import User, UserUpdate
from app.api.deps_admin import get_current_admin_user
from app.core.database import db
from app.core.security import get_password_hash
from datetime import datetime, timezone
from bson import ObjectId

router = APIRouter()

@router.get("/users", response_model=List[User])
async def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    is_active: Optional[bool] = None,
    current_admin: UserModel = Depends(get_current_admin_user)
):
    """
    Get all users. Admin only.
    Can filter by is_active status.
    """
    filter_query = {}
    if is_active is not None:
        filter_query["is_active"] = is_active
    
    users = []
    cursor = db.database.users.find(filter_query).skip(skip).limit(limit)
    
    async for user in cursor:
        user["id"] = str(user["_id"])
        users.append(User(**user))
    
    return users

@router.get("/users/{user_id}", response_model=User)
async def get_user_by_id(
    user_id: str,
    current_admin: UserModel = Depends(get_current_admin_user)
):
    """
    Get a specific user by ID. Admin only.
    """
    try:
        user = await db.database.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        user["id"] = str(user["_id"])
        return User(**user)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

@router.put("/users/{user_id}/activate", response_model=User)
async def activate_user(
    user_id: str,
    current_admin: UserModel = Depends(get_current_admin_user)
):
    """
    Activate a user account. Admin only.
    """
    try:
        result = await db.database.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "is_active": True,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user = await db.database.users.find_one({"_id": ObjectId(user_id)})
        user["id"] = str(user["_id"])
        return User(**user)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

@router.put("/users/{user_id}/deactivate", response_model=User)
async def deactivate_user(
    user_id: str,
    current_admin: UserModel = Depends(get_current_admin_user)
):
    """
    Deactivate a user account. Admin only.
    """
    try:
        # Prevent admin from deactivating themselves
        if str(current_admin.id) == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate your own account"
            )
        
        result = await db.database.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "is_active": False,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user = await db.database.users.find_one({"_id": ObjectId(user_id)})
        user["id"] = str(user["_id"])
        return User(**user)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

@router.put("/users/{user_id}/make-admin", response_model=User)
async def make_user_admin(
    user_id: str,
    current_admin: UserModel = Depends(get_current_admin_user)
):
    """
    Grant admin privileges to a user. Admin only.
    """
    try:
        result = await db.database.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "is_superuser": True,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user = await db.database.users.find_one({"_id": ObjectId(user_id)})
        user["id"] = str(user["_id"])
        return User(**user)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

@router.put("/users/{user_id}/remove-admin", response_model=User)
async def remove_user_admin(
    user_id: str,
    current_admin: UserModel = Depends(get_current_admin_user)
):
    """
    Remove admin privileges from a user. Admin only.
    """
    try:
        # Prevent admin from removing their own admin status
        if str(current_admin.id) == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove your own admin privileges"
            )
        
        result = await db.database.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "is_superuser": False,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user = await db.database.users.find_one({"_id": ObjectId(user_id)})
        user["id"] = str(user["_id"])
        return User(**user)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

@router.put("/users/{user_id}/password")
async def change_user_password(
    user_id: str,
    password_data: dict,
    current_admin: UserModel = Depends(get_current_admin_user)
):
    """
    Change a user's password. Admin only.
    Expects: {"new_password": "string"}
    """
    try:
        new_password = password_data.get("new_password")
        if not new_password or len(new_password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 6 characters long"
            )
        
        hashed_password = get_password_hash(new_password)
        
        result = await db.database.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "hashed_password": hashed_password,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {"message": "Password changed successfully"}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_admin: UserModel = Depends(get_current_admin_user)
):
    """
    Delete a user permanently. Admin only.
    """
    try:
        # Prevent admin from deleting themselves
        if str(current_admin.id) == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )
        
        result = await db.database.users.delete_one({"_id": ObjectId(user_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {"message": "User deleted successfully"}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

@router.get("/stats")
async def get_admin_stats(
    current_admin: UserModel = Depends(get_current_admin_user)
):
    """
    Get system statistics. Admin only.
    """
    total_users = await db.database.users.count_documents({})
    active_users = await db.database.users.count_documents({"is_active": True})
    inactive_users = await db.database.users.count_documents({"is_active": False})
    admin_users = await db.database.users.count_documents({"is_superuser": True})
    
    # Get counts from other collections
    total_events = await db.database.events.count_documents({})
    total_flashcards = await db.database.flashcards.count_documents({})
    total_diary_entries = await db.database.diary_entries.count_documents({})
    total_improvement_logs = await db.database.improvement_logs.count_documents({})
    
    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "inactive": inactive_users,
            "admins": admin_users
        },
        "content": {
            "events": total_events,
            "flashcards": total_flashcards,
            "diary_entries": total_diary_entries,
            "improvement_logs": total_improvement_logs
        }
    }
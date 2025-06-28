from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import get_current_active_user
from app.core.database import db
from app.core.security import get_password_hash
from app.models.user import UserModel
from app.schemas.user import User, UserCreate, UserUpdate
from datetime import datetime, timezone

router = APIRouter()

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(user_in: UserCreate):
    existing_user = await db.database.users.find_one(
        {"$or": [{"username": user_in.username}, {"email": user_in.email}]}
    )
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    user_dict = user_in.model_dump()
    user_dict["hashed_password"] = get_password_hash(user_dict.pop("password"))
    user_dict["created_at"] = datetime.now(timezone.utc)
    user_dict["updated_at"] = datetime.now(timezone.utc)
    user_dict["is_active"] = False  # New users need admin approval
    user_dict["is_superuser"] = False
    
    result = await db.database.users.insert_one(user_dict)
    user_dict["id"] = str(result.inserted_id)
    
    return User(**user_dict)

@router.get("/me", response_model=User)
async def read_current_user(current_user: UserModel = Depends(get_current_active_user)):
    user_dict = current_user.model_dump()
    user_dict["id"] = str(current_user.id) if current_user.id else None
    return User(**user_dict)

@router.put("/me", response_model=User)
async def update_current_user(
    user_update: UserUpdate,
    current_user: UserModel = Depends(get_current_active_user)
):
    update_data = user_update.model_dump(exclude_unset=True)
    
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc)
        await db.database.users.update_one(
            {"_id": current_user.id},
            {"$set": update_data}
        )
    
    updated_user = await db.database.users.find_one({"_id": current_user.id})
    updated_user["id"] = str(updated_user["_id"])
    
    return User(**updated_user)
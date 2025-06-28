from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from bson import ObjectId
from app.api.deps import get_current_active_user
from app.core.database import db
from app.models.user import UserModel
from app.models.improvement_log import ImprovementLog as ImprovementLogModel, LogType
from pydantic import BaseModel

router = APIRouter()

class ImprovementLogCreate(BaseModel):
    type: LogType
    title: str
    description: str
    category: Optional[str] = None
    tags: List[str] = []
    impact_level: int = 3
    frequency: Optional[str] = None
    trigger: Optional[str] = None
    solution: Optional[str] = None

class ImprovementLogUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    impact_level: Optional[int] = None
    frequency: Optional[str] = None
    trigger: Optional[str] = None
    solution: Optional[str] = None
    is_resolved: Optional[bool] = None

class ProgressNote(BaseModel):
    note: str
    progress_percentage: Optional[int] = None

@router.post("/", response_model=ImprovementLogModel, status_code=status.HTTP_201_CREATED)
async def create_log(
    log_in: ImprovementLogCreate,
    current_user: UserModel = Depends(get_current_active_user)
):
    log_dict = log_in.model_dump()
    log_dict["user_id"] = str(current_user.id)
    log_dict["progress_notes"] = []
    log_dict["is_resolved"] = False
    log_dict["created_at"] = datetime.now(timezone.utc)
    log_dict["updated_at"] = datetime.now(timezone.utc)
    
    result = await db.database.improvement_logs.insert_one(log_dict)
    log_dict["id"] = str(result.inserted_id)
    del log_dict["_id"]
    
    return ImprovementLogModel(**log_dict)

@router.get("/", response_model=List[ImprovementLogModel])
async def get_logs(
    log_type: Optional[LogType] = Query(None),
    category: Optional[str] = Query(None),
    is_resolved: Optional[bool] = Query(None),
    current_user: UserModel = Depends(get_current_active_user)
):
    query = {"user_id": str(current_user.id)}
    
    if log_type:
        query["type"] = log_type
    if category:
        query["category"] = category
    if is_resolved is not None:
        query["is_resolved"] = is_resolved
    
    logs = []
    async for log in db.database.improvement_logs.find(query).sort("created_at", -1):
        log["id"] = str(log["_id"])
        del log["_id"]
        logs.append(ImprovementLogModel(**log))
    
    return logs

@router.get("/{log_id}", response_model=ImprovementLogModel)
async def get_log(
    log_id: str,
    current_user: UserModel = Depends(get_current_active_user)
):
    log = await db.database.improvement_logs.find_one({
        "_id": ObjectId(log_id),
        "user_id": str(current_user.id)
    })
    
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log not found"
        )
    
    log["id"] = str(log["_id"])
    del log["_id"]
    return ImprovementLogModel(**log)

@router.put("/{log_id}", response_model=ImprovementLogModel)
async def update_log(
    log_id: str,
    log_update: ImprovementLogUpdate,
    current_user: UserModel = Depends(get_current_active_user)
):
    update_data = log_update.model_dump(exclude_unset=True)
    
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        if update_data.get("is_resolved"):
            update_data["resolved_at"] = datetime.now(timezone.utc)
        
        result = await db.database.improvement_logs.update_one(
            {"_id": ObjectId(log_id), "user_id": str(current_user.id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Log not found"
            )
    
    log = await db.database.improvement_logs.find_one({"_id": ObjectId(log_id)})
    log["id"] = str(log["_id"])
    del log["_id"]
    
    return ImprovementLogModel(**log)

@router.post("/{log_id}/progress", response_model=ImprovementLogModel)
async def add_progress_note(
    log_id: str,
    progress_note: ProgressNote,
    current_user: UserModel = Depends(get_current_active_user)
):
    note_dict = {
        "note": progress_note.note,
        "progress_percentage": progress_note.progress_percentage,
        "created_at": datetime.now(timezone.utc)
    }
    
    result = await db.database.improvement_logs.update_one(
        {"_id": ObjectId(log_id), "user_id": str(current_user.id)},
        {
            "$push": {"progress_notes": note_dict},
            "$set": {"updated_at": datetime.now(timezone.utc)}
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log not found"
        )
    
    log = await db.database.improvement_logs.find_one({"_id": ObjectId(log_id)})
    log["id"] = str(log["_id"])
    del log["_id"]
    
    return ImprovementLogModel(**log)

@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_log(
    log_id: str,
    current_user: UserModel = Depends(get_current_active_user)
):
    result = await db.database.improvement_logs.delete_one({
        "_id": ObjectId(log_id),
        "user_id": str(current_user.id)
    })
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log not found"
        )
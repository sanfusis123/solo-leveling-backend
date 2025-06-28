from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
from app.api.deps import get_current_active_user
from app.core.database import db
from app.models.user import UserModel
from app.schemas.project import (
    Skill, SkillCreate, SkillUpdate, SkillWithStats
)

router = APIRouter()

@router.post("/", response_model=Skill, status_code=status.HTTP_201_CREATED)
async def create_skill(
    skill_in: SkillCreate,
    current_user: UserModel = Depends(get_current_active_user)
):
    """Create a new skill"""
    skill_dict = skill_in.model_dump()
    skill_dict["user_id"] = str(current_user.id)
    skill_dict["created_at"] = datetime.now(timezone.utc)
    skill_dict["updated_at"] = datetime.now(timezone.utc)
    
    result = await db.database.skills.insert_one(skill_dict)
    skill_dict["id"] = str(result.inserted_id)
    
    return Skill(**skill_dict)

@router.get("/", response_model=List[Skill])
async def get_skills(
    category: Optional[str] = None,
    current_user: UserModel = Depends(get_current_active_user)
):
    """Get all skills for the current user"""
    query = {"user_id": str(current_user.id)}
    if category:
        query["category"] = category
    
    skills = []
    async for skill in db.database.skills.find(query).sort("name", 1):
        skill["id"] = str(skill["_id"])
        del skill["_id"]
        skills.append(Skill(**skill))
    
    return skills

@router.get("/categories", response_model=List[str])
async def get_skill_categories(
    current_user: UserModel = Depends(get_current_active_user)
):
    """Get all unique skill categories"""
    categories = await db.database.skills.distinct(
        "category", 
        {"user_id": str(current_user.id), "category": {"$ne": None}}
    )
    return sorted(categories)

@router.get("/{skill_id}", response_model=SkillWithStats)
async def get_skill(
    skill_id: str,
    current_user: UserModel = Depends(get_current_active_user)
):
    """Get a specific skill with statistics"""
    skill = await db.database.skills.find_one({
        "_id": ObjectId(skill_id),
        "user_id": str(current_user.id)
    })
    
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )
    
    skill["id"] = str(skill["_id"])
    del skill["_id"]
    
    # Calculate statistics from calendar events
    pipeline = [
        {
            "$match": {
                "user_id": str(current_user.id),
                "skill": skill_id,
                "status": {"$in": ["completed", "in_progress"]}
            }
        },
        {
            "$group": {
                "_id": None,
                "total_hours": {
                    "$sum": {
                        "$divide": [
                            {"$subtract": ["$end_time", "$start_time"]},
                            3600000  # Convert to hours
                        ]
                    }
                },
                "tasks_completed": {
                    "$sum": {
                        "$cond": [{"$eq": ["$status", "completed"]}, 1, 0]
                    }
                },
                "last_practiced": {"$max": "$end_time"}
            }
        }
    ]
    
    stats_result = await db.database.calendar_events.aggregate(pipeline).to_list(1)
    
    skill_with_stats = SkillWithStats(**skill)
    if stats_result:
        stats = stats_result[0]
        skill_with_stats.total_hours = round(stats["total_hours"], 2)
        skill_with_stats.tasks_completed = stats["tasks_completed"]
        skill_with_stats.last_practiced = stats["last_practiced"]
    
    return skill_with_stats

@router.put("/{skill_id}", response_model=Skill)
async def update_skill(
    skill_id: str,
    skill_update: SkillUpdate,
    current_user: UserModel = Depends(get_current_active_user)
):
    """Update a skill"""
    update_data = skill_update.model_dump(exclude_unset=True)
    
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc)
        result = await db.database.skills.update_one(
            {"_id": ObjectId(skill_id), "user_id": str(current_user.id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Skill not found"
            )
    
    skill = await db.database.skills.find_one({"_id": ObjectId(skill_id)})
    skill["id"] = str(skill["_id"])
    del skill["_id"]
    
    return Skill(**skill)

@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    skill_id: str,
    current_user: UserModel = Depends(get_current_active_user)
):
    """Delete a skill"""
    result = await db.database.skills.delete_one({
        "_id": ObjectId(skill_id),
        "user_id": str(current_user.id)
    })
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
from app.api.deps import get_current_active_user
from app.core.database import db
from app.models.user import UserModel
from app.models.project import ProjectStatus
from app.schemas.project import (
    Project, ProjectCreate, ProjectUpdate, ProjectWithStats
)

router = APIRouter()

@router.post("/", response_model=Project, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_in: ProjectCreate,
    current_user: UserModel = Depends(get_current_active_user)
):
    """Create a new project"""
    project_dict = project_in.model_dump()
    project_dict["user_id"] = str(current_user.id)
    project_dict["created_at"] = datetime.now(timezone.utc)
    project_dict["updated_at"] = datetime.now(timezone.utc)
    
    result = await db.database.projects.insert_one(project_dict)
    project_dict["id"] = str(result.inserted_id)
    
    return Project(**project_dict)

@router.get("/", response_model=List[Project])
async def get_projects(
    status: Optional[ProjectStatus] = None,
    current_user: UserModel = Depends(get_current_active_user)
):
    """Get all projects for the current user"""
    query = {"user_id": str(current_user.id)}
    if status:
        query["status"] = status
    
    projects = []
    async for project in db.database.projects.find(query).sort("created_at", -1):
        project["id"] = str(project["_id"])
        del project["_id"]
        projects.append(Project(**project))
    
    return projects

@router.get("/{project_id}", response_model=ProjectWithStats)
async def get_project(
    project_id: str,
    current_user: UserModel = Depends(get_current_active_user)
):
    """Get a specific project with statistics"""
    project = await db.database.projects.find_one({
        "_id": ObjectId(project_id),
        "user_id": str(current_user.id)
    })
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    project["id"] = str(project["_id"])
    del project["_id"]
    
    # Calculate statistics from calendar events
    pipeline = [
        {
            "$match": {
                "user_id": str(current_user.id),
                "project": project_id,
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
                "completed_tasks": {
                    "$sum": {
                        "$cond": [{"$eq": ["$status", "completed"]}, 1, 0]
                    }
                },
                "total_tasks": {"$sum": 1}
            }
        }
    ]
    
    stats_result = await db.database.calendar_events.aggregate(pipeline).to_list(1)
    
    project_with_stats = ProjectWithStats(**project)
    if stats_result:
        stats = stats_result[0]
        project_with_stats.total_hours = round(stats["total_hours"], 2)
        project_with_stats.completed_tasks = stats["completed_tasks"]
        project_with_stats.total_tasks = stats["total_tasks"]
    
    return project_with_stats

@router.put("/{project_id}", response_model=Project)
async def update_project(
    project_id: str,
    project_update: ProjectUpdate,
    current_user: UserModel = Depends(get_current_active_user)
):
    """Update a project"""
    update_data = project_update.model_dump(exclude_unset=True)
    
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc)
        result = await db.database.projects.update_one(
            {"_id": ObjectId(project_id), "user_id": str(current_user.id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
    
    project = await db.database.projects.find_one({"_id": ObjectId(project_id)})
    project["id"] = str(project["_id"])
    del project["_id"]
    
    return Project(**project)

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    current_user: UserModel = Depends(get_current_active_user)
):
    """Delete a project"""
    result = await db.database.projects.delete_one({
        "_id": ObjectId(project_id),
        "user_id": str(current_user.id)
    })
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
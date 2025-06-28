from typing import List, Dict, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from app.api.deps import get_current_active_user
from app.core.database import db
from app.models.user import UserModel
from app.models.calendar import TaskStatus

router = APIRouter()

@router.get("/skills/time-spent")
async def get_skills_time_spent(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Get time spent on each skill"""
    query = {
        "user_id": str(current_user.id),
        "status": {"$in": [TaskStatus.COMPLETED, TaskStatus.IN_PROGRESS]}
    }
    
    if start_date and end_date:
        query["start_time"] = {"$gte": start_date, "$lte": end_date}
    elif start_date:
        query["start_time"] = {"$gte": start_date}
    elif end_date:
        query["start_time"] = {"$lte": end_date}
    
    # Aggregate time by skill
    pipeline = [
        {"$match": query},
        {"$match": {"skill_id": {"$ne": None, "$exists": True, "$ne": ""}}},
        {
            "$lookup": {
                "from": "skills",
                "let": {"skill_id": {"$toObjectId": "$skill_id"}},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$_id", "$$skill_id"]}}}
                ],
                "as": "skill_info"
            }
        },
        {"$unwind": "$skill_info"},
        {
            "$project": {
                "skill_id": 1,
                "skill_name": "$skill_info.name",
                "duration": {
                    "$divide": [
                        {"$subtract": ["$end_time", "$start_time"]},
                        3600000  # Convert milliseconds to hours
                    ]
                }
            }
        },
        {
            "$group": {
                "_id": {"id": "$skill_id", "name": "$skill_name"},
                "total_hours": {"$sum": "$duration"},
                "task_count": {"$sum": 1}
            }
        },
        {"$sort": {"total_hours": -1}}
    ]
    
    results = []
    async for doc in db.database.calendar_events.aggregate(pipeline):
        results.append({
            "skill_id": doc["_id"]["id"],
            "skill_name": doc["_id"]["name"],
            "total_hours": round(doc["total_hours"], 2),
            "task_count": doc["task_count"]
        })
    
    return results

@router.get("/projects/time-spent")
async def get_projects_time_spent(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Get time spent on each project"""
    query = {
        "user_id": str(current_user.id),
        "status": {"$in": [TaskStatus.COMPLETED, TaskStatus.IN_PROGRESS]}
    }
    
    if start_date and end_date:
        query["start_time"] = {"$gte": start_date, "$lte": end_date}
    elif start_date:
        query["start_time"] = {"$gte": start_date}
    elif end_date:
        query["start_time"] = {"$lte": end_date}
    
    # Aggregate time by project
    pipeline = [
        {"$match": query},
        {"$match": {"project_id": {"$ne": None, "$exists": True, "$ne": ""}}},
        {
            "$lookup": {
                "from": "projects",
                "let": {"project_id": {"$toObjectId": "$project_id"}},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$_id", "$$project_id"]}}}
                ],
                "as": "project_info"
            }
        },
        {"$unwind": "$project_info"},
        {
            "$project": {
                "project_id": 1,
                "project_name": "$project_info.name",
                "duration": {
                    "$divide": [
                        {"$subtract": ["$end_time", "$start_time"]},
                        3600000  # Convert milliseconds to hours
                    ]
                }
            }
        },
        {
            "$group": {
                "_id": {"id": "$project_id", "name": "$project_name"},
                "total_hours": {"$sum": "$duration"},
                "task_count": {"$sum": 1}
            }
        },
        {"$sort": {"total_hours": -1}}
    ]
    
    results = []
    async for doc in db.database.calendar_events.aggregate(pipeline):
        results.append({
            "project_id": doc["_id"]["id"],
            "project_name": doc["_id"]["name"],
            "total_hours": round(doc["total_hours"], 2),
            "task_count": doc["task_count"]
        })
    
    return results

@router.get("/productivity/overview")
async def get_productivity_overview(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Get overall productivity statistics"""
    query = {"user_id": str(current_user.id)}
    
    if start_date and end_date:
        query["start_time"] = {"$gte": start_date, "$lte": end_date}
    elif start_date:
        query["start_time"] = {"$gte": start_date}
    elif end_date:
        query["start_time"] = {"$lte": end_date}
    
    # Get various statistics
    total_tasks = await db.database.calendar_events.count_documents(query)
    
    completed_query = {**query, "status": TaskStatus.COMPLETED}
    completed_tasks = await db.database.calendar_events.count_documents(completed_query)
    
    # Calculate total hours
    pipeline = [
        {"$match": query},
        {
            "$project": {
                "duration": {
                    "$divide": [
                        {"$subtract": ["$end_time", "$start_time"]},
                        3600000  # Convert milliseconds to hours
                    ]
                }
            }
        },
        {
            "$group": {
                "_id": None,
                "total_hours": {"$sum": "$duration"}
            }
        }
    ]
    
    total_hours = 0
    async for doc in db.database.calendar_events.aggregate(pipeline):
        total_hours = doc["total_hours"]
    
    # Get most productive day
    day_pipeline = [
        {"$match": query},
        {
            "$project": {
                "day": {"$dateToString": {"format": "%Y-%m-%d", "date": "$start_time"}},
                "duration": {
                    "$divide": [
                        {"$subtract": ["$end_time", "$start_time"]},
                        3600000
                    ]
                }
            }
        },
        {
            "$group": {
                "_id": "$day",
                "hours": {"$sum": "$duration"},
                "tasks": {"$sum": 1}
            }
        },
        {"$sort": {"hours": -1}},
        {"$limit": 1}
    ]
    
    most_productive_day = None
    async for doc in db.database.calendar_events.aggregate(day_pipeline):
        most_productive_day = {
            "date": doc["_id"],
            "hours": round(doc["hours"], 2),
            "tasks": doc["tasks"]
        }
    
    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "completion_rate": round(completed_tasks / total_tasks * 100, 2) if total_tasks > 0 else 0,
        "total_hours": round(total_hours, 2),
        "average_hours_per_task": round(total_hours / total_tasks, 2) if total_tasks > 0 else 0,
        "most_productive_day": most_productive_day
    }
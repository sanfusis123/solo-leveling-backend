from typing import List, Optional
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from bson import ObjectId
from app.api.deps import get_current_active_user
from app.core.database import db
from app.models.user import UserModel
from app.models.calendar import CalendarEvent as CalendarEventModel, TaskStatus
from app.schemas.calendar import (
    CalendarEvent, CalendarEventCreate, CalendarEventUpdate,
    TaskComplete, TaskSkip
)

router = APIRouter()

@router.post("/events", response_model=CalendarEvent, status_code=status.HTTP_201_CREATED)
async def create_event(
    event_in: CalendarEventCreate,
    current_user: UserModel = Depends(get_current_active_user)
):
    event_dict = event_in.model_dump()
    event_dict["user_id"] = str(current_user.id)
    event_dict["status"] = TaskStatus.PENDING
    event_dict["created_at"] = datetime.now(timezone.utc)
    event_dict["updated_at"] = datetime.now(timezone.utc)
    
    # Log the received times for debugging
    print(f"Received start_time: {event_dict['start_time']}")
    print(f"Received end_time: {event_dict['end_time']}")
    
    # Ensure times are stored as naive datetimes (no timezone)
    if isinstance(event_dict['start_time'], datetime):
        event_dict['start_time'] = event_dict['start_time'].replace(tzinfo=None)
    if isinstance(event_dict['end_time'], datetime):
        event_dict['end_time'] = event_dict['end_time'].replace(tzinfo=None)
    
    result = await db.database.calendar_events.insert_one(event_dict)
    event_dict["id"] = str(result.inserted_id)
    
    return CalendarEvent(**event_dict)

@router.get("/events", response_model=List[CalendarEvent])
async def get_events(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    status: Optional[TaskStatus] = Query(None),
    category: Optional[str] = Query(None),
    current_user: UserModel = Depends(get_current_active_user)
):
    query = {"user_id": str(current_user.id)}
    
    if start_date and end_date:
        query["start_time"] = {"$gte": start_date, "$lte": end_date}
    elif start_date:
        query["start_time"] = {"$gte": start_date}
    elif end_date:
        query["start_time"] = {"$lte": end_date}
    
    if status:
        query["status"] = status
    
    if category:
        query["category"] = category
    
    events = []
    async for event in db.database.calendar_events.find(query).sort("start_time", 1):
        event["id"] = str(event["_id"])
        del event["_id"]
        events.append(CalendarEvent(**event))
    
    return events

@router.get("/events/{event_id}", response_model=CalendarEvent)
async def get_event(
    event_id: str,
    current_user: UserModel = Depends(get_current_active_user)
):
    event = await db.database.calendar_events.find_one({
        "_id": ObjectId(event_id),
        "user_id": str(current_user.id)
    })
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    event["id"] = str(event["_id"])
    return CalendarEvent(**event)

@router.put("/events/{event_id}", response_model=CalendarEvent)
async def update_event(
    event_id: str,
    event_update: CalendarEventUpdate,
    current_user: UserModel = Depends(get_current_active_user)
):
    update_data = event_update.model_dump(exclude_unset=True)
    
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        # Ensure times are stored as naive datetimes (no timezone)
        if 'start_time' in update_data and isinstance(update_data['start_time'], datetime):
            update_data['start_time'] = update_data['start_time'].replace(tzinfo=None)
        if 'end_time' in update_data and isinstance(update_data['end_time'], datetime):
            update_data['end_time'] = update_data['end_time'].replace(tzinfo=None)
        
        result = await db.database.calendar_events.update_one(
            {"_id": ObjectId(event_id), "user_id": str(current_user.id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
    
    event = await db.database.calendar_events.find_one({"_id": ObjectId(event_id)})
    event["id"] = str(event["_id"])
    
    return CalendarEvent(**event)

@router.post("/events/{event_id}/complete", response_model=CalendarEvent)
async def complete_event(
    event_id: str,
    task_complete: TaskComplete,
    current_user: UserModel = Depends(get_current_active_user)
):
    update_data = {
        "status": TaskStatus.COMPLETED,
        "completed_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    
    result = await db.database.calendar_events.update_one(
        {"_id": ObjectId(event_id), "user_id": str(current_user.id)},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    event = await db.database.calendar_events.find_one({"_id": ObjectId(event_id)})
    event["id"] = str(event["_id"])
    
    return CalendarEvent(**event)

@router.post("/events/{event_id}/skip", response_model=CalendarEvent)
async def skip_event(
    event_id: str,
    task_skip: TaskSkip,
    current_user: UserModel = Depends(get_current_active_user)
):
    update_data = {
        "status": TaskStatus.SKIPPED,
        "skipped_at": datetime.now(timezone.utc),
        "skip_reason": task_skip.reason,
        "updated_at": datetime.now(timezone.utc)
    }
    
    result = await db.database.calendar_events.update_one(
        {"_id": ObjectId(event_id), "user_id": str(current_user.id)},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    event = await db.database.calendar_events.find_one({"_id": ObjectId(event_id)})
    event["id"] = str(event["_id"])
    
    return CalendarEvent(**event)

@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: str,
    current_user: UserModel = Depends(get_current_active_user)
):
    result = await db.database.calendar_events.delete_one({
        "_id": ObjectId(event_id),
        "user_id": str(current_user.id)
    })
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
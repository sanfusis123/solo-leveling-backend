from typing import List, Optional
from datetime import datetime, date, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from bson import ObjectId
from app.api.deps import get_current_active_user
from app.core.database import db
from app.models.user import UserModel
from app.models.diary import DiaryEntry as DiaryEntryModel, MoodLevel
from pydantic import BaseModel, Field

router = APIRouter()

# Mood mapping from frontend to backend
MOOD_MAPPING = {
    "amazing": "excellent",
    "happy": "good", 
    "neutral": "neutral",
    "sad": "bad",
    "angry": "very_bad"
}

# Reverse mapping for sending to frontend
MOOD_REVERSE_MAPPING = {v: k for k, v in MOOD_MAPPING.items()}

class DiaryEntryCreate(BaseModel):
    date: date
    title: Optional[str] = None
    content: str
    mood: Optional[str] = None  # Changed to accept string from frontend
    activities: List[str] = []
    accomplishments: List[str] = []
    challenges: List[str] = []
    gratitude_list: List[str] = Field([], alias="gratitude")  # Support both field names
    tomorrow_goals: List[str] = []
    tags: List[str] = []
    weather: Optional[str] = None
    location: Optional[str] = None

class DiaryEntryUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    mood: Optional[str] = None  # Changed to accept string from frontend
    activities: Optional[List[str]] = None
    accomplishments: Optional[List[str]] = None
    challenges: Optional[List[str]] = None
    gratitude_list: Optional[List[str]] = Field(None, alias="gratitude")  # Support both field names
    tomorrow_goals: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    weather: Optional[str] = None
    location: Optional[str] = None

@router.post("/entries", response_model=DiaryEntryModel, status_code=status.HTTP_201_CREATED)
async def create_entry(
    entry_in: DiaryEntryCreate,
    current_user: UserModel = Depends(get_current_active_user)
):
    # Check if entry already exists for this date
    existing_entry = await db.database.diary_entries.find_one({
        "user_id": str(current_user.id),
        "date": entry_in.date.isoformat()
    })
    
    if existing_entry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Entry already exists for this date"
        )
    
    entry_dict = entry_in.model_dump()
    
    # Map gratitude_list to gratitude for database
    if "gratitude_list" in entry_dict:
        entry_dict["gratitude"] = entry_dict.pop("gratitude_list")
    
    # Map frontend mood to backend mood
    if entry_dict.get("mood") and entry_dict["mood"] in MOOD_MAPPING:
        entry_dict["mood"] = MOOD_MAPPING[entry_dict["mood"]]
    
    entry_dict["date"] = entry_in.date.isoformat()
    entry_dict["user_id"] = str(current_user.id)
    entry_dict["photos"] = []
    entry_dict["is_private"] = True
    entry_dict["created_at"] = datetime.now(timezone.utc)
    entry_dict["updated_at"] = datetime.now(timezone.utc)
    
    result = await db.database.diary_entries.insert_one(entry_dict)
    entry_dict["id"] = str(result.inserted_id)
    del entry_dict["_id"]
    
    # Map backend mood to frontend mood for response
    if entry_dict.get("mood") and entry_dict["mood"] in MOOD_REVERSE_MAPPING:
        entry_dict["mood"] = MOOD_REVERSE_MAPPING[entry_dict["mood"]]
    
    # Keep date as ISO string for response
    entry_dict["date"] = entry_in.date.isoformat()
    
    return DiaryEntryModel(**entry_dict)

@router.get("/entries", response_model=List[DiaryEntryModel])
async def get_entries(
    start_timestamp: Optional[int] = Query(None, description="Unix timestamp for start date"),
    end_timestamp: Optional[int] = Query(None, description="Unix timestamp for end date"),
    mood: Optional[MoodLevel] = Query(None),
    tag: Optional[str] = Query(None),
    current_user: UserModel = Depends(get_current_active_user)
):
    query = {"user_id": str(current_user.id)}
    
    if start_timestamp and end_timestamp:
        # Convert timestamps to date strings for comparison
        # Use UTC to avoid timezone issues
        start_date = datetime.fromtimestamp(start_timestamp, tz=timezone.utc).date()
        end_date = datetime.fromtimestamp(end_timestamp, tz=timezone.utc).date()
        query["date"] = {
            "$gte": start_date.isoformat(),
            "$lte": end_date.isoformat()
        }
    elif start_timestamp:
        start_date = datetime.fromtimestamp(start_timestamp, tz=timezone.utc).date()
        query["date"] = {"$gte": start_date.isoformat()}
    elif end_timestamp:
        end_date = datetime.fromtimestamp(end_timestamp, tz=timezone.utc).date()
        query["date"] = {"$lte": end_date.isoformat()}
    
    if mood:
        query["mood"] = mood
    
    if tag:
        query["tags"] = tag
    
    entries = []
    async for entry in db.database.diary_entries.find(query).sort("date", -1):
        entry["id"] = str(entry["_id"])
        del entry["_id"]
        
        # Map backend mood to frontend mood
        if entry.get("mood") and entry["mood"] in MOOD_REVERSE_MAPPING:
            entry["mood"] = MOOD_REVERSE_MAPPING[entry["mood"]]
        
        # Keep date as ISO string for frontend compatibility
        entries.append(DiaryEntryModel(**entry))
    
    return entries

@router.get("/entries/{entry_date}", response_model=DiaryEntryModel)
async def get_entry_by_date(
    entry_date: date,
    current_user: UserModel = Depends(get_current_active_user)
):
    entry = await db.database.diary_entries.find_one({
        "user_id": str(current_user.id),
        "date": entry_date.isoformat()
    })
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found for this date"
        )
    
    entry["id"] = str(entry["_id"])
    del entry["_id"]
    
    # Map backend mood to frontend mood
    if entry.get("mood") and entry["mood"] in MOOD_REVERSE_MAPPING:
        entry["mood"] = MOOD_REVERSE_MAPPING[entry["mood"]]
    
    # Keep date as ISO string for frontend compatibility
    return DiaryEntryModel(**entry)

@router.put("/entries/{entry_date}", response_model=DiaryEntryModel)
async def update_entry(
    entry_date: date,
    entry_update: DiaryEntryUpdate,
    current_user: UserModel = Depends(get_current_active_user)
):
    update_data = entry_update.model_dump(exclude_unset=True)
    
    # Map gratitude_list to gratitude for database
    if "gratitude_list" in update_data:
        update_data["gratitude"] = update_data.pop("gratitude_list")
    
    # Map frontend mood to backend mood
    if update_data.get("mood") and update_data["mood"] in MOOD_MAPPING:
        update_data["mood"] = MOOD_MAPPING[update_data["mood"]]
    
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc)
        result = await db.database.diary_entries.update_one(
            {
                "user_id": str(current_user.id),
                "date": entry_date.isoformat()
            },
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Entry not found for this date"
            )
    
    entry = await db.database.diary_entries.find_one({
        "user_id": str(current_user.id),
        "date": entry_date.isoformat()
    })
    
    entry["id"] = str(entry["_id"])
    del entry["_id"]
    
    # Map backend mood to frontend mood
    if entry.get("mood") and entry["mood"] in MOOD_REVERSE_MAPPING:
        entry["mood"] = MOOD_REVERSE_MAPPING[entry["mood"]]
    
    # Keep date as ISO string for frontend compatibility
    
    return DiaryEntryModel(**entry)

@router.get("/mood-summary", response_model=dict)
async def get_mood_summary(
    start_timestamp: Optional[int] = Query(None, description="Unix timestamp for start date"),
    end_timestamp: Optional[int] = Query(None, description="Unix timestamp for end date"),
    current_user: UserModel = Depends(get_current_active_user)
):
    query = {"user_id": str(current_user.id)}
    
    if start_timestamp and end_timestamp:
        # Convert timestamps to date strings for comparison
        # Use UTC to avoid timezone issues
        start_date = datetime.fromtimestamp(start_timestamp, tz=timezone.utc).date()
        end_date = datetime.fromtimestamp(end_timestamp, tz=timezone.utc).date()
        query["date"] = {
            "$gte": start_date.isoformat(),
            "$lte": end_date.isoformat()
        }
    elif start_timestamp:
        start_date = datetime.fromtimestamp(start_timestamp, tz=timezone.utc).date()
        query["date"] = {"$gte": start_date.isoformat()}
    elif end_timestamp:
        end_date = datetime.fromtimestamp(end_timestamp, tz=timezone.utc).date()
        query["date"] = {"$lte": end_date.isoformat()}
    
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": "$mood",
            "count": {"$sum": 1}
        }}
    ]
    
    mood_counts = {}
    async for result in db.database.diary_entries.aggregate(pipeline):
        if result["_id"]:
            mood_counts[result["_id"]] = result["count"]
    
    return mood_counts

@router.delete("/entries/{entry_date}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entry(
    entry_date: date,
    current_user: UserModel = Depends(get_current_active_user)
):
    result = await db.database.diary_entries.delete_one({
        "user_id": str(current_user.id),
        "date": entry_date.isoformat()
    })
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found for this date"
        )
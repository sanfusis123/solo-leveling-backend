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

class DiaryEntryResponse(BaseModel):
    id: Optional[str] = None
    user_id: str
    date: date
    title: Optional[str] = None
    content: str
    mood: Optional[str] = None  # Frontend mood format
    activities: List[str] = []
    accomplishments: List[str] = []
    challenges: List[str] = []
    gratitude: List[str] = []
    tomorrow_goals: List[str] = []
    tags: List[str] = []
    weather: Optional[str] = None
    location: Optional[str] = None
    photos: List[str] = []
    is_private: bool = True
    created_at: datetime
    updated_at: datetime

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

@router.post("/entries", response_model=DiaryEntryResponse, status_code=status.HTTP_201_CREATED)
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
    
    # Create DiaryEntryModel first to validate
    diary_entry = DiaryEntryModel(**entry_dict)
    
    # Convert to response format with frontend mood
    response_dict = diary_entry.model_dump()
    response_dict["date"] = entry_in.date  # Keep as date object
    if response_dict.get("mood"):
        # Convert backend mood to frontend format
        backend_mood = response_dict["mood"]
        if hasattr(backend_mood, 'value'):
            backend_mood = backend_mood.value
        response_dict["mood"] = MOOD_REVERSE_MAPPING.get(backend_mood, backend_mood)
    
    return DiaryEntryResponse(**response_dict)

@router.get("/entries", response_model=List[DiaryEntryResponse])
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
        
        # Handle mood mapping - ensure we have a valid backend mood for the model
        if entry.get("mood"):
            if entry["mood"] in ["very_bad", "bad", "neutral", "good", "excellent"]:
                # Already in valid backend format, keep it
                pass
            elif entry["mood"] in MOOD_MAPPING:
                # Frontend format (like "amazing"), convert to backend
                entry["mood"] = MOOD_MAPPING[entry["mood"]]
            else:
                # Unknown mood, default to neutral
                entry["mood"] = "neutral"
        
        # Keep date as ISO string for frontend compatibility
        
        # Create DiaryEntryModel and then convert to response
        diary_entry = DiaryEntryModel(**entry)
        
        # Convert to response format with frontend mood
        response_dict = diary_entry.model_dump()
        if response_dict.get("mood"):
            # Convert backend mood to frontend format
            backend_mood = response_dict["mood"]
            if hasattr(backend_mood, 'value'):
                backend_mood = backend_mood.value
            response_dict["mood"] = MOOD_REVERSE_MAPPING.get(backend_mood, backend_mood)
        
        entries.append(DiaryEntryResponse(**response_dict))
    
    return entries

@router.get("/entries/{entry_date}", response_model=DiaryEntryResponse)
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
    
    # Handle mood mapping - ensure we have a valid backend mood for the model
    if entry.get("mood"):
        if entry["mood"] in ["very_bad", "bad", "neutral", "good", "excellent"]:
            # Already in valid backend format, keep it
            pass
        elif entry["mood"] in MOOD_MAPPING:
            # Frontend format (like "amazing"), convert to backend
            entry["mood"] = MOOD_MAPPING[entry["mood"]]
        else:
            # Unknown mood, default to neutral
            entry["mood"] = "neutral"
    
    # Create DiaryEntryModel and then convert to response
    diary_entry = DiaryEntryModel(**entry)
    
    # Convert to response format with frontend mood
    response_dict = diary_entry.model_dump()
    if response_dict.get("mood"):
        # Convert backend mood to frontend format
        backend_mood = response_dict["mood"]
        if hasattr(backend_mood, 'value'):
            backend_mood = backend_mood.value
        response_dict["mood"] = MOOD_REVERSE_MAPPING.get(backend_mood, backend_mood)
    
    return DiaryEntryResponse(**response_dict)

@router.put("/entries/{entry_date}", response_model=DiaryEntryResponse)
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
    
    # Handle mood mapping - ensure we have a valid backend mood for the model
    if entry.get("mood"):
        if entry["mood"] in ["very_bad", "bad", "neutral", "good", "excellent"]:
            # Already in valid backend format, keep it
            pass
        elif entry["mood"] in MOOD_MAPPING:
            # Frontend format (like "amazing"), convert to backend
            entry["mood"] = MOOD_MAPPING[entry["mood"]]
        else:
            # Unknown mood, default to neutral
            entry["mood"] = "neutral"
    
    # Create DiaryEntryModel and then convert to response
    diary_entry = DiaryEntryModel(**entry)
    
    # Convert to response format with frontend mood
    response_dict = diary_entry.model_dump()
    if response_dict.get("mood"):
        # Convert backend mood to frontend format
        backend_mood = response_dict["mood"]
        if hasattr(backend_mood, 'value'):
            backend_mood = backend_mood.value
        response_dict["mood"] = MOOD_REVERSE_MAPPING.get(backend_mood, backend_mood)
    
    return DiaryEntryResponse(**response_dict)

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
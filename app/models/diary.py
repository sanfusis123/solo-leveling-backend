from typing import Optional, List, Dict
from datetime import datetime, date, timezone
from pydantic import BaseModel, Field
from bson import ObjectId
from enum import Enum

class MoodLevel(str, Enum):
    VERY_BAD = "very_bad"
    BAD = "bad"
    NEUTRAL = "neutral"
    GOOD = "good"
    EXCELLENT = "excellent"

class DiaryEntry(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    user_id: str
    date: date
    title: Optional[str] = None
    content: str
    mood: Optional[MoodLevel] = None
    activities: List[str] = []
    accomplishments: List[str] = []
    challenges: List[str] = []
    gratitude: List[str] = Field([], alias="gratitude_list")
    tomorrow_goals: List[str] = []
    tags: List[str] = []
    weather: Optional[str] = None
    location: Optional[str] = None
    photos: List[str] = []
    is_private: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str, date: lambda v: v.isoformat()}
    }
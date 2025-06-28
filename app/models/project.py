from typing import Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from bson import ObjectId
from enum import Enum

class ProjectStatus(str, Enum):
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Project(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    user_id: str
    name: str
    description: Optional[str] = None
    status: ProjectStatus = ProjectStatus.ACTIVE
    color: Optional[str] = None  # For UI display
    target_hours: Optional[float] = None  # Target hours to complete
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }

class Skill(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    user_id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None  # e.g., "Programming", "Design", "Language"
    target_level: Optional[str] = None  # e.g., "Beginner", "Intermediate", "Expert"
    current_level: Optional[str] = None
    color: Optional[str] = None  # For UI display
    icon: Optional[str] = None  # Emoji or icon identifier
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }
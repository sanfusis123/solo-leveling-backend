from typing import Optional, List, Dict
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from bson import ObjectId
from enum import Enum

class MaterialType(str, Enum):
    NOTE = "note"
    ARTICLE = "article"
    TUTORIAL = "tutorial"
    REFERENCE = "reference"

class VisibilityLevel(str, Enum):
    PRIVATE = "private"
    PUBLIC = "public"
    SHARED = "shared"

class LearningMaterial(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    user_id: str
    title: str
    content: str
    summary: Optional[str] = None
    type: MaterialType = MaterialType.NOTE
    subject: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = []
    visibility: VisibilityLevel = VisibilityLevel.PRIVATE
    shared_with: List[str] = []
    attachments: List[Dict[str, str]] = []
    references: List[str] = []
    view_count: int = 0
    like_count: int = 0
    is_archived: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from bson import ObjectId
from enum import Enum

class LogType(str, Enum):
    IMPROVEMENT = "improvement"
    DISTRACTION = "distraction"

class ImprovementLog(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    user_id: str
    type: LogType
    title: str
    description: str
    category: Optional[str] = None
    tags: List[str] = []
    impact_level: int = Field(ge=1, le=5, default=3)
    frequency: Optional[str] = None
    trigger: Optional[str] = None
    solution: Optional[str] = None
    progress_notes: List[Dict[str, Any]] = []
    is_resolved: bool = False
    resolved_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }
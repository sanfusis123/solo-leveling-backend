from typing import Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from bson import ObjectId
from enum import Enum

class ContentType(str, Enum):
    POEM = "poem"
    JOKE = "joke"
    STORY = "story"
    QUOTE = "quote"
    THOUGHT = "thought"
    OTHER = "other"

from typing import Dict, Any

class FunContent(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    user_id: str
    title: str
    content: str
    type: ContentType = Field(alias="content_type")
    category: Optional[str] = None
    tags: List[str] = []
    is_public: bool = False
    likes: int = 0
    views: int = 0
    comments_count: int = 0
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }
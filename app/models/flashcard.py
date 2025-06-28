from typing import Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from bson import ObjectId
from enum import Enum

class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class FlashcardDeck(BaseModel):
    id: Optional[str] = None
    user_id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = []
    is_public: bool = False
    card_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }

class Flashcard(BaseModel):
    id: Optional[str] = None
    deck_id: str
    user_id: str
    front: str
    back: str
    hint: Optional[str] = None
    tags: List[str] = []
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    review_count: int = 0
    correct_count: int = 0
    last_reviewed: Optional[datetime] = None
    next_review: Optional[datetime] = None
    interval_days: int = 1
    ease_factor: float = 2.5
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }
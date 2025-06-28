from typing import Optional, List, Dict
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from bson import ObjectId
from enum import Enum

class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"

class RecurrenceType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    CUSTOM = "custom"

class RecurrenceRule(BaseModel):
    type: RecurrenceType
    interval: int = 1
    days_of_week: Optional[List[int]] = None
    day_of_month: Optional[int] = None
    end_date: Optional[datetime] = None
    occurrences: Optional[int] = None

class CalendarEvent(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    user_id: str
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    category: Optional[str] = None
    project_id: Optional[str] = None  # Reference to project
    skill_id: Optional[str] = None  # Reference to skill
    tags: List[str] = []
    location: Optional[str] = None
    is_recurring: bool = False
    recurrence_rule: Optional[RecurrenceRule] = None
    parent_event_id: Optional[str] = None
    reminders: List[int] = []
    completed_at: Optional[datetime] = None
    skipped_at: Optional[datetime] = None
    skip_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }
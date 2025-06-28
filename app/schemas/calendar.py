from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator
from app.models.calendar import TaskPriority, TaskStatus, RecurrenceType, RecurrenceRule

class CalendarEventBase(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    priority: TaskPriority = TaskPriority.MEDIUM
    category: Optional[str] = None
    project_id: Optional[str] = None
    skill_id: Optional[str] = None
    tags: List[str] = []
    location: Optional[str] = None
    is_recurring: bool = False
    recurrence_rule: Optional[RecurrenceRule] = None
    reminders: List[int] = []
    
    @validator('start_time', 'end_time', pre=True)
    def parse_datetime(cls, v):
        if isinstance(v, str):
            # Simple parsing - treat the string as local time
            # Expected format: "2024-01-15T09:00:00"
            try:
                # Remove any timezone indicators
                if 'Z' in v:
                    v = v.replace('Z', '')
                if '+' in v:
                    v = v.split('+')[0]
                if v.count('-') > 2 and v.rfind('-') > 10:  # Has negative timezone offset
                    v = v[:v.rfind('-')]
                
                # Parse as naive datetime
                dt = datetime.fromisoformat(v)
                return dt
            except:
                # Fallback to the original string
                return v
        return v
    
    class Config:
        # Ensure datetime is serialized without timezone
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%dT%H:%M:%S') if v else None
        }

class CalendarEventCreate(CalendarEventBase):
    pass

class CalendarEventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    category: Optional[str] = None
    project_id: Optional[str] = None
    skill_id: Optional[str] = None
    tags: Optional[List[str]] = None
    location: Optional[str] = None
    is_recurring: Optional[bool] = None
    recurrence_rule: Optional[RecurrenceRule] = None
    reminders: Optional[List[int]] = None

class CalendarEventInDB(CalendarEventBase):
    id: str
    user_id: str
    status: TaskStatus
    parent_event_id: Optional[str] = None
    completed_at: Optional[datetime] = None
    skipped_at: Optional[datetime] = None
    skip_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class CalendarEvent(CalendarEventInDB):
    class Config:
        # Ensure datetime is serialized without timezone
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%dT%H:%M:%S') if v else None
        }

class TaskComplete(BaseModel):
    completed: bool = True
    notes: Optional[str] = None

class TaskSkip(BaseModel):
    reason: Optional[str] = None
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator
from app.models.project import ProjectStatus

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: ProjectStatus = ProjectStatus.ACTIVE
    color: Optional[str] = None
    target_hours: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    @validator('start_date', 'end_date', pre=True)
    def parse_datetime(cls, v):
        if v is None:
            return v
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            # Parse the datetime string and ensure it's timezone-naive
            try:
                # Handle ISO format with timezone (e.g., "2023-12-01T00:00:00.000Z")
                if 'Z' in v:
                    v = v.replace('Z', '')
                if '+' in v:
                    v = v.split('+')[0]
                if v.count('-') > 2 and v.rfind('-') > 10:  # Has negative timezone offset
                    v = v[:v.rfind('-')]
                
                # Remove milliseconds if present
                if '.' in v:
                    v = v.split('.')[0]
                
                # Parse as naive datetime
                dt = datetime.fromisoformat(v)
                return dt
            except Exception as e:
                # Try parsing just the date part if it's a date string
                try:
                    if 'T' in v:
                        date_part = v.split('T')[0]
                        return datetime.fromisoformat(date_part)
                    return datetime.fromisoformat(v)
                except:
                    pass
                return None
        return v

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    color: Optional[str] = None
    target_hours: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    @validator('start_date', 'end_date', pre=True)
    def parse_datetime(cls, v):
        if v is None:
            return v
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            # Parse the datetime string and ensure it's timezone-naive
            try:
                # Handle ISO format with timezone (e.g., "2023-12-01T00:00:00.000Z")
                if 'Z' in v:
                    v = v.replace('Z', '')
                if '+' in v:
                    v = v.split('+')[0]
                if v.count('-') > 2 and v.rfind('-') > 10:  # Has negative timezone offset
                    v = v[:v.rfind('-')]
                
                # Remove milliseconds if present
                if '.' in v:
                    v = v.split('.')[0]
                
                # Parse as naive datetime
                dt = datetime.fromisoformat(v)
                return dt
            except Exception as e:
                # Try parsing just the date part if it's a date string
                try:
                    if 'T' in v:
                        date_part = v.split('T')[0]
                        return datetime.fromisoformat(date_part)
                    return datetime.fromisoformat(v)
                except:
                    pass
                return None
        return v

class ProjectInDB(ProjectBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

class Project(ProjectInDB):
    pass

class ProjectWithStats(Project):
    total_hours: float = 0
    completed_tasks: int = 0
    total_tasks: int = 0

# Skill schemas
class SkillBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    target_level: Optional[str] = None
    current_level: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None

class SkillCreate(SkillBase):
    pass

class SkillUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    target_level: Optional[str] = None
    current_level: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None

class SkillInDB(SkillBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

class Skill(SkillInDB):
    pass

class SkillWithStats(Skill):
    total_hours: float = 0
    tasks_completed: int = 0
    last_practiced: Optional[datetime] = None
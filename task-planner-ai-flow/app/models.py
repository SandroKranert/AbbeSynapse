"""
Pydantic models for data validation
"""
from datetime import date, time, datetime
from typing import Optional, List, Union
from pydantic import BaseModel, ConfigDict


class TaskCreate(BaseModel):
    """Model for task creation"""
    title: str
    date: date
    time: Union[str, time, None] = None # type: ignore
    description: Optional[str] = None


class Task(BaseModel):
    """Model to represent a task"""
    id: str
    title: str
    date: date
    time: Union[str, time, None] = None  # type: ignore
    description: Optional[str] = None
    is_completed: bool = False
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "abc123xyz",
                "title": "Team meeting",
                "date": "2023-12-01",
                "time": "14:30:00",
                "description": "Weekly team meeting",
                "is_completed": False
            }
        }
    )


class TaskList(BaseModel):
    """List of tasks"""
    tasks: List[Task] = []
    count: int


class AuthStatus(BaseModel):
    """Authentication status"""
    authenticated: bool
    expires_at: Optional[datetime] = None
    message: str

"""
Pydantic models for data validation
"""
from datetime import date, time, datetime
from typing import Optional, List, Annotated
from pydantic import BaseModel, Field, ConfigDict


class TaskCreate(BaseModel):
    """Model for task creation"""
    title: Annotated[str, Field(description="Task title")]
    date: Annotated[date, Field(description="Task date (YYYY-MM-DD)")]
    time: Optional[Annotated[time, Field(description="Task time (HH:MM)")]] = None
    description: Optional[Annotated[str, Field(description="Task description")]] = None


class Task(BaseModel):
    """Model to represent a task"""
    id: Annotated[str, Field(description="Google Calendar event ID")]
    title: Annotated[str, Field(description="Task title")]
    date: Annotated[date, Field(description="Task date")]
    time: Optional[Annotated[time, Field(description="Task time")]] = None
    description: Optional[Annotated[str, Field(description="Task description")]] = None
    is_completed: Annotated[bool, Field(description="Completion status")] = False
    
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
    tasks: Annotated[List[Task], Field(default_factory=list)]
    count: Annotated[int, Field(description="Total number of tasks")]


class AuthStatus(BaseModel):
    """Authentication status"""
    authenticated: Annotated[bool, Field(description="Authentication status")]
    expires_at: Optional[Annotated[datetime, Field(description="Token expiration date")]] = None
    message: Annotated[str, Field(description="Information message")]
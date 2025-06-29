"""
Main FastAPI application for Task-Planner Agent
"""
from datetime import date, timedelta
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models import Task, TaskCreate, TaskList
from app.auth import router as auth_router, require_auth
from app.calendar_service import get_calendar_service, CalendarService
from app.openai_service import OpenAIService
from app.config import DEBUG, OPENAI_API_KEY
from pydantic import BaseModel

# Create FastAPI application
app = FastAPI(
    title="Task-Planner Agent API",
    description="API for managing tasks with Google Calendar",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    debug=DEBUG
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include authentication router
app.include_router(auth_router)


@app.get("/health")
async def health_check():
    """
    API health check endpoint
    """
    return {"status": "ok", "message": "Service operational"}


@app.get("/tasks/today", response_model=TaskList, tags=["Tasks"])
async def get_today_tasks(
    calendar_service: CalendarService = Depends(get_calendar_service)
):
    """
    Get today's tasks
    """
    today = date.today()
    tasks = await calendar_service.get_tasks_for_day(today)
    return TaskList(tasks=tasks, count=len(tasks))


@app.get("/tasks/range", response_model=TaskList, tags=["Tasks"])
async def get_tasks_by_range(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    calendar_service: CalendarService = Depends(get_calendar_service)
):
    """
    Get tasks for a date range
    """
    if start_date is None:
        start_date = date.today()
    if end_date is None:
        end_date = start_date + timedelta(days=30)
    
    tasks = await calendar_service.get_tasks_for_range(start_date, end_date)
    return TaskList(tasks=tasks, count=len(tasks))


@app.post("/tasks", response_model=Task, tags=["Tasks"])
async def create_task(
    task: TaskCreate,
    calendar_service: CalendarService = Depends(get_calendar_service)
):
    """
    Create a new task
    """
    return await calendar_service.create_task(task)


@app.put("/tasks/{task_id}", response_model=Task, tags=["Tasks"])
async def update_task(
    task_id: str,
    task: TaskCreate,
    calendar_service: CalendarService = Depends(get_calendar_service)
):
    """
    Update an existing task
    """
    return await calendar_service.update_task(task_id, task)


@app.delete("/tasks/{task_id}", tags=["Tasks"])
async def delete_task(
    task_id: str,
    calendar_service: CalendarService = Depends(get_calendar_service)
):
    """
    Delete a task
    """
    return await calendar_service.delete_task(task_id)


@app.post("/tasks/{task_id}/done", response_model=Task, tags=["Tasks"])
async def mark_task_done(
    task_id: str,
    calendar_service: CalendarService = Depends(get_calendar_service)
):
    """
    Mark a task as done
    """
    return await calendar_service.mark_task_done(task_id)


class ChatRequest(BaseModel):
    message: str


@app.post("/chat", tags=["AI Assistant"])
async def chat_with_ai(
    request: ChatRequest,
    calendar_service: CalendarService = Depends(get_calendar_service)
):
    """
    Chat with AI assistant for task management
    """
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
    openai_service = OpenAIService(OPENAI_API_KEY)
    response = await openai_service.chat(request.message, calendar_service)
    return {"response": response}


if __name__ == "__main__":
    import uvicorn # type: ignore
    from app.config import FASTAPI_HOST, FASTAPI_PORT
    
    uvicorn.run(
        "app.main:app",
        host=FASTAPI_HOST,
        port=FASTAPI_PORT,
        reload=DEBUG
    )
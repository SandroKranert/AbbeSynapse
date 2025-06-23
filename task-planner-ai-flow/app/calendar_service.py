"""
Google Calendar API interaction service
"""
from datetime import datetime, date, time, timedelta
from typing import List, Optional, Dict, Any

from fastapi import Depends, HTTPException
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.auth import require_auth
from app.models import Task, TaskCreate
from app.config import CALENDAR_ID


class CalendarService:
    """Service to interact with Google Calendar API"""
    
    def __init__(self, credentials: Credentials):
        """Initialize the service with Google credentials"""
        self.service = build('calendar', 'v3', credentials=credentials)
        self.calendar_id = CALENDAR_ID
    
    async def get_tasks_for_day(self, day: date) -> List[Task]:
        """
        Get tasks/events for a specific day
        """
        # Define time limits for the day
        time_min = datetime.combine(day, time.min).isoformat() + 'Z'
        time_max = datetime.combine(day, time.max).isoformat() + 'Z'
        
        try:
            # Call to Google Calendar API
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Convert to Task models
            tasks = []
            for event in events:
                # Extract date and time
                start = event.get('start', {})
                if 'dateTime' in start:
                    # Format with time
                    dt = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
                    task_date = dt.date()
                    task_time = dt.time()
                else:
                    # All-day format
                    task_date = datetime.fromisoformat(start['date']).date()
                    task_time = None
                
                # Check if task is completed (via description)
                description = event.get('description', '')
                is_completed = "[COMPLETED]" in description
                
                # Clean description
                clean_description = description.replace("[COMPLETED]", "").strip()
                
                tasks.append(Task(
                    id=event['id'],
                    title=event['summary'],
                    date=task_date,
                    time=task_time,
                    description=clean_description if clean_description else None,
                    is_completed=is_completed
                ))
            
            return tasks
            
        except HttpError as error:
            raise HTTPException(status_code=500, detail=f"Google Calendar Error: {error}")
    
    async def create_task(self, task: TaskCreate) -> Task:
        """
        Create a new task in Google Calendar
        """
        # Prepare the event
        event = {
            'summary': task.title,
            'description': task.description or '',
        }
        
        # Configure date/time
        if task.time:
            # With specific time
            start_datetime = datetime.combine(task.date, task.time)
            end_datetime = start_datetime + timedelta(hours=1)  # Default 1h
            
            event['start'] = {
                'dateTime': start_datetime.isoformat(),
                'timeZone': 'UTC',
            }
            event['end'] = {
                'dateTime': end_datetime.isoformat(),
                'timeZone': 'UTC',
            }
        else:
            # All-day
            event['start'] = {
                'date': task.date.isoformat(),
            }
            event['end'] = {
                'date': (task.date + timedelta(days=1)).isoformat(),
            }
        
        try:
            # Create the event
            created_event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event
            ).execute()
            
            # Convert to Task
            return Task(
                id=created_event['id'],
                title=task.title,
                date=task.date,
                time=task.time,
                description=task.description,
                is_completed=False
            )
            
        except HttpError as error:
            raise HTTPException(status_code=500, detail=f"Task creation error: {error}")
    
    async def mark_task_done(self, task_id: str) -> Task:
        """
        Mark a task as done
        """
        try:
            # Get the event
            event = self.service.events().get(
                calendarId=self.calendar_id,
                eventId=task_id
            ).execute()
            
            # Add [COMPLETED] marker in description
            description = event.get('description', '')
            if "[COMPLETED]" not in description:
                event['description'] = f"[COMPLETED] {description}"
            
            # Update the event
            updated_event = self.service.events().update(
                calendarId=self.calendar_id,
                eventId=task_id,
                body=event
            ).execute()
            
            # Extract information
            start = updated_event.get('start', {})
            if 'dateTime' in start:
                dt = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
                task_date = dt.date()
                task_time = dt.time()
            else:
                task_date = datetime.fromisoformat(start['date']).date()
                task_time = None
            
            # Clean description
            description = updated_event.get('description', '')
            clean_description = description.replace("[COMPLETED]", "").strip()
            
            return Task(
                id=updated_event['id'],
                title=updated_event['summary'],
                date=task_date,
                time=task_time,
                description=clean_description if clean_description else None,
                is_completed=True
            )
            
        except HttpError as error:
            raise HTTPException(status_code=500, detail=f"Task update error: {error}")


def get_calendar_service(credentials: Credentials = Depends(require_auth)) -> CalendarService:
    """
    FastAPI dependency to get Calendar service
    """
    return CalendarService(credentials)
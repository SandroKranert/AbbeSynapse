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
        time_min = datetime(day.year, day.month, day.day, 0, 0, 0).isoformat() + 'Z'
        time_max = datetime(day.year, day.month, day.day, 23, 59, 59).isoformat() + 'Z'
        
        try:
            # Call to Google Calendar API
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime',
                maxResults=2500
            ).execute(num_retries=0)
            
            events = events_result.get('items', [])
            
            # Convert to Task models
            tasks = []
            for event in events:
                if not event.get('summary'):
                    continue
                    
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
                    time=task_time.strftime('%H:%M:%S') if task_time else None,
                    description=clean_description if clean_description else None,
                    is_completed=is_completed
                ))
            
            return tasks
            
        except HttpError as error:
            raise HTTPException(status_code=500, detail=f"Google Calendar Error: {error}")
    
    async def get_tasks_for_range(self, start_date: date, end_date: date) -> List[Task]:
        """
        Get tasks/events for a date range
        """
        time_min = datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0).isoformat() + 'Z'
        time_max = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59).isoformat() + 'Z'
        
        try:
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime',
                maxResults=2500
            ).execute(num_retries=0)
            
            events = events_result.get('items', [])
            
            tasks = []
            for event in events:
                # Skip events without title
                if not event.get('summary'):
                    continue
                    
                start = event.get('start', {})
                if 'dateTime' in start:
                    # Handle datetime with timezone
                    dt_str = start['dateTime']
                    if 'T' in dt_str:
                        # Remove timezone info for parsing
                        dt_str = dt_str.split('T')[0] + 'T' + dt_str.split('T')[1].split('+')[0].split('-')[0].split('Z')[0]
                        dt = datetime.fromisoformat(dt_str)
                        task_date = dt.date()
                        task_time = dt.time()
                    else:
                        task_date = datetime.fromisoformat(dt_str).date()
                        task_time = None
                elif 'date' in start:
                    # All-day event
                    task_date = datetime.fromisoformat(start['date']).date()
                    task_time = None
                else:
                    continue
                
                description = event.get('description', '')
                is_completed = "[COMPLETED]" in description
                clean_description = description.replace("[COMPLETED]", "").strip()
                
                tasks.append(Task(
                    id=event['id'],
                    title=event.get('summary', 'Untitled'),
                    date=task_date,
                    time=task_time.strftime('%H:%M:%S') if task_time else None,
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
        event = {
            'summary': task.title,
            'description': task.description or '',
        }
        
        if task.time:
            if isinstance(task.time, str):
                time_parts = task.time.split(':')
                hour, minute = int(time_parts[0]), int(time_parts[1])
                second = int(time_parts[2]) if len(time_parts) > 2 else 0
            else:
                hour, minute, second = task.time.hour, task.time.minute, task.time.second
            
            start_datetime = datetime(task.date.year, task.date.month, task.date.day, hour, minute, second)
            end_datetime = start_datetime + timedelta(hours=1)
            
            event['start'] = {
                'dateTime': start_datetime.isoformat(),
                'timeZone': 'UTC'
            }
            event['end'] = {
                'dateTime': end_datetime.isoformat(),
                'timeZone': 'UTC'
            }
        else:
            event['start'] = {'date': task.date.isoformat()}
            event['end'] = {'date': task.date.isoformat()}
        
        try:
            created_event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event
            ).execute()
            
            return Task(
                id=created_event['id'],
                title=task.title,
                date=task.date,
                time=str(task.time) if task.time else None,
                description=task.description,
                is_completed=False
            )
            
        except HttpError as error:
            raise HTTPException(status_code=500, detail=f"Task creation error: {error}")
    
    async def update_task(self, task_id: str, task: TaskCreate) -> Task:
        """
        Update an existing task
        """
        try:
            event = {
                'summary': task.title,
                'description': task.description or '',
            }
            
            if task.time:
                time_str = str(task.time)
                time_parts = time_str.split(':')
                hour, minute = int(time_parts[0]), int(time_parts[1])
                second = int(time_parts[2]) if len(time_parts) > 2 else 0
                
                start_datetime = datetime(task.date.year, task.date.month, task.date.day, hour, minute, second)
                end_datetime = start_datetime + timedelta(hours=1)
                
                event['start'] = {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': 'UTC'
                }
                event['end'] = {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': 'UTC'
                }
            else:
                event['start'] = {'date': task.date.isoformat()}
                event['end'] = {'date': task.date.isoformat()}
            
            updated_event = self.service.events().update(
                calendarId=self.calendar_id,
                eventId=task_id,
                body=event
            ).execute()
            
            return Task(
                id=updated_event['id'],
                title=task.title,
                date=task.date,
                time=task.time,
                description=task.description,
                is_completed=False
            )
            
        except HttpError as error:
            raise HTTPException(status_code=500, detail=f"Task update error: {error}")
    
    async def delete_task(self, task_id: str) -> dict:
        """
        Delete a task
        """
        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=task_id
            ).execute()
            
            return {"message": "Task deleted successfully"}
            
        except HttpError as error:
            raise HTTPException(status_code=500, detail=f"Task deletion error: {error}")
    
    async def mark_task_done(self, task_id: str) -> Task:
        """
        Mark a task as done
        """
        try:
            event = self.service.events().get(
                calendarId=self.calendar_id,
                eventId=task_id
            ).execute()
            
            description = event.get('description', '')
            if "[COMPLETED]" not in description:
                event['description'] = f"[COMPLETED] {description}"
            
            updated_event = self.service.events().update(
                calendarId=self.calendar_id,
                eventId=task_id,
                body=event
            ).execute()
            
            start = updated_event.get('start', {})
            if 'dateTime' in start:
                dt = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
                task_date = dt.date()
                task_time = dt.time()
            else:
                task_date = datetime.fromisoformat(start['date']).date()
                task_time = None
            
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
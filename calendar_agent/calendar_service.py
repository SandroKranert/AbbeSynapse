import os
from datetime import datetime, date, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/calendar']
CREDENTIALS_FILE = os.getenv('GOOGLE_CALENDAR_CREDENTIALS_FILE', 'credentials.json')
TOKEN_FILE = os.getenv('GOOGLE_CALENDAR_TOKEN_FILE', 'token.json')
CALENDAR_ID = os.getenv('CALENDAR_ID', 'primary')
OAUTH_PORT = int(os.getenv('OAUTH_PORT', '8086'))

def authenticate_calendar():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=OAUTH_PORT)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    return build('calendar', 'v3', credentials=creds)

def get_tasks_for_day(target_date):
    service = authenticate_calendar()
    time_min = datetime.combine(target_date, datetime.min.time()).isoformat() + 'Z'
    time_max = datetime.combine(target_date, datetime.max.time()).isoformat() + 'Z'
    
    events_result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    events = events_result.get('items', [])
    tasks = []
    
    for event in events:
        start = event.get('start', {})
        if 'dateTime' in start:
            dt = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
            task_date = dt.date()
            task_time = dt.time()
        else:
            task_date = datetime.fromisoformat(start['date']).date()
            task_time = None
        
        description = event.get('description', '')
        is_completed = "[COMPLETED]" in description
        clean_description = description.replace("[COMPLETED]", "").strip()
        
        tasks.append({
            'id': event['id'],
            'title': event['summary'],
            'date': task_date,
            'time': task_time,
            'description': clean_description if clean_description else None,
            'is_completed': is_completed
        })
    
    return tasks

def create_task(title, task_date, task_time=None, description=None):
    service = authenticate_calendar()
    
    event = {
        'summary': title,
        'description': description or '',
    }
    
    if task_time:
        start_datetime = datetime.combine(task_date, task_time)
        end_datetime = start_datetime + timedelta(hours=1)
        
        event['start'] = {
            'dateTime': start_datetime.isoformat(),
            'timeZone': 'UTC',
        }
        event['end'] = {
            'dateTime': end_datetime.isoformat(),
            'timeZone': 'UTC',
        }
    else:
        event['start'] = {'date': task_date.isoformat()}
        event['end'] = {'date': (task_date + timedelta(days=1)).isoformat()}
    
    created_event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
    return created_event['id']

def get_tasks_for_range(start_date, end_date):
    service = authenticate_calendar()
    time_min = datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0).isoformat() + 'Z'
    time_max = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59).isoformat() + 'Z'
    
    events_result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy='startTime',
        maxResults=2500
    ).execute()
    
    events = events_result.get('items', [])
    tasks = []
    
    for event in events:
        if not event.get('summary'):
            continue
            
        start = event.get('start', {})
        if 'dateTime' in start:
            dt_str = start['dateTime']
            if 'T' in dt_str:
                dt_str = dt_str.split('T')[0] + 'T' + dt_str.split('T')[1].split('+')[0].split('-')[0].split('Z')[0]
                dt = datetime.fromisoformat(dt_str)
                task_date = dt.date()
                task_time = dt.time()
            else:
                task_date = datetime.fromisoformat(dt_str).date()
                task_time = None
        elif 'date' in start:
            task_date = datetime.fromisoformat(start['date']).date()
            task_time = None
        else:
            continue
        
        description = event.get('description', '')
        is_completed = "[COMPLETED]" in description
        clean_description = description.replace("[COMPLETED]", "").strip()
        
        tasks.append({
            'id': event['id'],
            'title': event.get('summary', 'Untitled'),
            'date': task_date,
            'time': task_time,
            'description': clean_description if clean_description else None,
            'is_completed': is_completed
        })
    
    return tasks

def mark_task_done(task_id):
    service = authenticate_calendar()
    
    event = service.events().get(calendarId=CALENDAR_ID, eventId=task_id).execute()
    description = event.get('description', '')
    
    if "[COMPLETED]" not in description:
        event['description'] = f"[COMPLETED] {description}"
    
    service.events().update(calendarId=CALENDAR_ID, eventId=task_id, body=event).execute()
    return True
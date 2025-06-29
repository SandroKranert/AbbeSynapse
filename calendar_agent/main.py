import os
from datetime import date, datetime, timedelta
from calendar_service import get_tasks_for_day, get_tasks_for_range, create_task, mark_task_done
from openai_service import OpenAIService
from dotenv import load_dotenv

load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def get_today_tasks():
    """Get today's tasks"""
    return get_tasks_for_day(date.today())

def get_tasks_by_date(target_date):
    """Get tasks for specific date"""
    if isinstance(target_date, str):
        target_date = date.fromisoformat(target_date)
    return get_tasks_for_day(target_date)

def add_task(title, task_date, task_time=None, description=None):
    """Add new task"""
    if isinstance(task_date, str):
        task_date = date.fromisoformat(task_date)
    if isinstance(task_time, str):
        task_time = datetime.strptime(task_time, "%H:%M").time()
    return create_task(title, task_date, task_time, description)

def get_tasks_range(start_date=None, end_date=None):
    """Get tasks from today to next 30 days (or custom range)"""
    if start_date is None:
        start_date = date.today()
    if end_date is None:
        end_date = start_date + timedelta(days=30)
    
    if isinstance(start_date, str):
        start_date = date.fromisoformat(start_date)
    if isinstance(end_date, str):
        end_date = date.fromisoformat(end_date)
    
    return get_tasks_for_range(start_date, end_date)

def complete_task(task_id):
    """Mark task as completed"""
    return mark_task_done(task_id)

def chat_with_ai(message):
    """Chat with AI for task management"""
    if not OPENAI_API_KEY:
        return "OpenAI API key not configured"
    
    openai_service = OpenAIService(OPENAI_API_KEY)
    
    calendar_functions = {
        'get_today_tasks': get_today_tasks,
        'get_tasks_range': get_tasks_for_range,
        'create_task': create_task,
        'mark_task_done': mark_task_done
    }
    
    return openai_service.chat(message, calendar_functions)

def main():
    """Main function for testing"""
    print("Calendar Agent - Task Management")
    print("Available functions:")
    print("1. get_today_tasks()")
    print("2. get_tasks_by_date('2024-12-25')")
    print("3. get_tasks_range() - Get tasks from today to next 30 days")
    print("4. add_task('Meeting', '2024-12-25', '14:30', 'Team meeting')")
    print("5. complete_task('task_id')")
    print("6. chat_with_ai('Show me tasks for next week')")
    
    # Example usage
    try:
        # Get tasks
        tasks = get_tasks_range()
        print(f"\n tasks: {len(tasks)} found")
        for task in tasks:
            print(f"- {task['title']} at {task['time'] or 'All day'}")
        
        # Example AI chat (if API key is configured)
        if OPENAI_API_KEY:
            response = chat_with_ai("Show me tasks for next week")
            print(f"\nAI Response: {response}")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure you have credentials.json in the same directory")

if __name__ == "__main__":
    main()
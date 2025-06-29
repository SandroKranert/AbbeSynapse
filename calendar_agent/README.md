# Calendar Agent

Simple Python calendar task manager with Google Calendar integration and AI chat support.

## Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Google Calendar Setup**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create project and enable Google Calendar API
   - Create OAuth2 credentials (Desktop app)
   - Download `credentials.json` to this folder

3. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

4. **First Run**
   ```bash
   python main.py
   ```
   - Browser will open for Google authentication
   - Grant calendar permissions
   - Test functions will run automatically

## Command Examples

### **Interactive Python**
```bash
python
>>> from main import *
>>> tasks = get_today_tasks()
>>> print(len(tasks))
>>> add_task('Test', '2024-12-25')
>>> exit()
```

### **Direct Script Execution**
```bash
# Run main with examples
python main.py

# Custom script
python -c "from main import *; print(len(get_today_tasks()))"
```

## Usage

### **Run the application**
```bash
python main.py
```

### **Import and use functions**
```python
from main import get_today_tasks, get_tasks_range, add_task, complete_task, chat_with_ai

# Get today's tasks
tasks = get_today_tasks()
print(f"Found {len(tasks)} tasks today")

# Get next 30 days tasks
all_tasks = get_tasks_range()
print(f"Found {len(all_tasks)} upcoming tasks")

# Get custom date range
week_tasks = get_tasks_range('2024-12-25', '2024-12-31')

# Add new task
task_id = add_task("Team Meeting", "2024-12-25", "14:30", "Weekly standup")
print(f"Created task: {task_id}")

# Mark task as done
complete_task("your_task_id_here")

# AI chat
response = chat_with_ai("What tasks do I have today?")
print(response)
```

## Functions

### **Task Retrieval**
```python
# Get today's tasks
tasks = get_today_tasks()

# Get tasks for specific date
tasks = get_tasks_by_date('2025-07-01')

# Get tasks range (default: today + 30 days)
tasks = get_tasks_range()

# Get custom date range
tasks = get_tasks_range('2025-06-30', '2025-07-31')
```

### **Task Management**
```python
# Create task (all day)
task_id = add_task('Doctor Appointment', '2025-07-10')

# Create task with time
task_id = add_task('Meeting', '2025-07-02', '14:30', 'Team standup')

# Mark task as completed
complete_task('abc123xyz')
```

### **AI Chat Examples**
```python
# Natural language queries
response = chat_with_ai('What tasks do I have today?')
response = chat_with_ai('Show me next week tasks')
response = chat_with_ai('Create a meeting tomorrow at 2pm')
response = chat_with_ai('Mark task abc123 as done')
```
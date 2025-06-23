# Task-Planner Agent - Calendar API Microservice

## 📋 What is this?
A simple service that connects your AI task planner with Google Calendar. It helps you manage your tasks and events through simple web requests.

## 🚀 Quick Start Guide (For Beginners)

### Step 1: Install Python
1. Download Python 3.10 or newer from [python.org](https://www.python.org/downloads/)
2. During installation, make sure to check "Add Python to PATH"
3. Verify installation by opening Command Prompt (Windows) or Terminal (Mac/Linux) and typing:
   ```
   python --version
   ```

### Step 2: Download this project
1. Download this project as a ZIP file
2. Extract it to a folder on your computer (e.g., Desktop)
3. Open Command Prompt (Windows) or Terminal (Mac/Linux)
4. Navigate to the project folder:
   ```
   # On Windows
   cd C:\Users\YourUsername\Desktop\task-planner-ai-flow
   
   # On Mac/Linux
   cd ~/Desktop/task-planner-ai-flow
   ```

### Step 3: Set up virtual environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On Mac/Linux:
source venv/bin/activate.bat

# Install required packages
pip install -r requirements.txt
pip install flask requests openai
```

### Step 4: Set up Google Calendar API
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click "Create Project" and name it "Task-Planner-Agent"
3. In the search bar, type "Google Calendar API" and click on it
4. Click "Enable" to activate the API
5. Go to "Credentials" in the left menu
6. Click "Create Credentials" and select "OAuth client ID"
7. Select "Desktop app" as the application type
8. Give it a name (e.g., "Task Planner")
9. Click "Create"
10. Download the JSON file
11. Rename the downloaded file to `credentials.json`
12. Create a folder named `credentials` in your project folder
13. Move the `credentials.json` file into the `credentials` folder

### Step 5: Create environment file
1. Create a new file named `.env` in your project folder
2. Copy and paste the following into the file:
   ```
   GOOGLE_CALENDAR_CREDENTIALS_FILE=credentials/credentials.json
   GOOGLE_CALENDAR_TOKEN_FILE=credentials/token.json
   FASTAPI_HOST=0.0.0.0
   FASTAPI_PORT=8000
   DEBUG=True
   ```
3. Save the file

### Step 6: Start the application
```bash
# Make sure your virtual environment is activated (you should see (venv) at the beginning of your command line)
# If not, activate it using the commands from Step 3

# Start the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 7: Complete Google authentication
1. Open your web browser
2. Go to http://localhost:8000/auth/authorize
3. Select your Google account
4. Grant the requested permissions
5. You'll be redirected to a success page

Congratulations! Your Task Planner is now connected to Google Calendar!

## 📱 Using the API

### View API documentation
Open your browser and go to:
- http://localhost:8000/docs

### Basic operations
- **Get today's tasks**: http://localhost:8000/tasks/today
- **Create a new task**: Send a POST request to http://localhost:8000/tasks with task details
- **Mark task as done**: Send a POST request to http://localhost:8000/tasks/{task_id}/done

## 🏗️ Project Structure
```
Task-Planner Agent/
├── app/                     # Main application code
├── credentials/             # Google API credentials
├── requirements.txt         # Required Python packages
└── README.md                # This file
```

## 🐛 Common Problems and Solutions

### "I can't activate the virtual environment"
- Make sure you're in the project directory
- On Windows, you might need to run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
- Try using the full path: `.\venv\Scripts\activate` (Windows) or `source ./venv/bin/activate` (Mac/Linux)

### "Authentication failed"
- Delete the token file: `credentials/token.json`
- Restart the authorization process: http://localhost:8000/auth/authorize

### "API not enabled" error
- Go to Google Cloud Console
- Make sure Google Calendar API is enabled for your project
- Check that your credentials are correctly set up

## 📊 API Endpoints Reference

### Authentication
- `GET /auth/authorize` - Start Google authentication
- `GET /auth/callback` - Handle Google authentication response
- `GET /auth/status` - Check if you're authenticated

### Tasks Management  
- `GET /tasks/today` - Get today's tasks
- `POST /tasks` - Create new task
- `POST /tasks/{task_id}/done` - Mark task as done
- `GET /health` - Check if service is running

## 🔧 Flowise Integration

To connect with Flowise, use these configurations in the tool nodes:

### Tool Node "get_tasks"
```json
{
  "name": "get_tasks",
  "description": "Get today's tasks",
  "url": "http://localhost:8000/tasks/today",
  "method": "GET",
  "headers": {"Content-Type": "application/json"}
}
```

### Tool Node "add_task"  
```json
{
  "name": "add_task",
  "description": "Add a new task",
  "url": "http://localhost:8000/tasks",
  "method": "POST",
  "headers": {"Content-Type": "application/json"},
  "body": {
    "title": "{{title}}",
    "date": "{{date}}",
    "time": "{{time}}",
    "description": "{{description}}"
  }
}
```

### Tool Node "mark_done"
```json
{
  "name": "mark_done", 
  "description": "Mark task as done",
  "url": "http://localhost:8000/tasks/{{task_id}}/done",
  "method": "POST",
  "headers": {"Content-Type": "application/json"}
}
```
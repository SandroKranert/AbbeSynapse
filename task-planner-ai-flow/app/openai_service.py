"""
OpenAI integration for Task-Planner Agent
"""
import json
from typing import Dict, Any
from openai import OpenAI
from fastapi import HTTPException

from app.config import DEBUG

class OpenAIService:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"
        
    def get_function_definitions(self):
        return [
            {
                "name": "get_today_tasks",
                "description": "Get ONLY today's tasks from calendar. Use this ONLY when user specifically asks for 'today' tasks.",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "get_tasks_range", 
                "description": "Get tasks for ANY date range including tomorrow, next week, this week, specific dates, or multiple days. Use this for: 'tomorrow', 'next week', 'this week', 'all tasks', 'upcoming tasks', date ranges, or any time period that is NOT just today.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "start_date": {"type": "string", "description": "Start date YYYY-MM-DD. If not specified, defaults to today."},
                        "end_date": {"type": "string", "description": "End date YYYY-MM-DD. If not specified, defaults to start_date + 30 days."}
                    }
                }
            },
            {
                "name": "create_task",
                "description": "Create a new task",
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "title": {"type": "string", "description": "Task title"},
                        "date": {"type": "string", "description": "Task date YYYY-MM-DD"},
                        "time": {"type": "string", "description": "Task time HH:MM:SS"},
                        "description": {"type": "string", "description": "Task description"}
                    },
                    "required": ["title", "date"]
                }
            },
            {
                "name": "mark_task_done",
                "description": "Mark a task as completed",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "Task ID to mark as done"}
                    },
                    "required": ["task_id"]
                }
            }
        ]
    
    async def chat(self, message: str, calendar_service) -> str:
        from datetime import date, datetime
        current_date = date.today()
        current_datetime = datetime.now()
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": f"You are a helpful task planning assistant. Current date: {current_date.strftime('%Y-%m-%d')} ({current_date.strftime('%A, %B %d, %Y')}). Current time: {current_datetime.strftime('%H:%M:%S')}. IMPORTANT: Use get_today_tasks ONLY for 'today' requests. For ANY other time period (tomorrow, next week, this week, all tasks, upcoming, date ranges), use get_tasks_range. When user asks for 'all tasks' or broad requests, use get_tasks_range without dates to get next 30 days."},
                    {"role": "user", "content": message}
                ],
                functions=self.get_function_definitions(),
                function_call="auto",
                temperature=0.3
            )
            
            choice = response.choices[0]
            
            if choice.finish_reason == "function_call":
                function_call = choice.message.function_call
                function_name = function_call.name
                function_args = json.loads(function_call.arguments)
                
                # Execute the function
                result = await self.execute_function(function_name, function_args, calendar_service)
                
                # Get final response from OpenAI
                final_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": f"You are a helpful task planning assistant. Current date: {current_date.strftime('%Y-%m-%d')} ({current_date.strftime('%A, %B %d, %Y')}). Present the task information in a clear, organized way."},
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": None, "function_call": {"name": function_name, "arguments": function_call.arguments}},
                        {"role": "function", "name": function_name, "content": json.dumps(result)}
                    ],
                    temperature=0.3
                )
                
                return final_response.choices[0].message.content
            else:
                return choice.message.content
                
        except Exception as e:
            if DEBUG:
                raise HTTPException(status_code=500, detail=f"OpenAI Error: {str(e)}")
            else:
                return "I'm having trouble processing your request right now."
    
    async def execute_function(self, function_name: str, args: Dict[str, Any], calendar_service) -> Dict[str, Any]:
        try:
            if function_name == "get_today_tasks":
                from datetime import date
                tasks = await calendar_service.get_tasks_for_day(date.today())
                return {"tasks": [{"id": t.id, "title": t.title, "time": t.time, "description": t.description} for t in tasks]}
            
            elif function_name == "get_tasks_range":
                from datetime import date
                start_date = date.fromisoformat(args.get("start_date")) if args.get("start_date") else date.today()
                end_date = date.fromisoformat(args.get("end_date")) if args.get("end_date") else None
                tasks = await calendar_service.get_tasks_for_range(start_date, end_date)
                return {"tasks": [{"id": t.id, "title": t.title, "date": str(t.date), "time": t.time} for t in tasks]}
            
            elif function_name == "create_task":
                from app.models import TaskCreate
                from datetime import date
                task_data = TaskCreate(
                    title=args["title"],
                    date=date.fromisoformat(args["date"]),
                    time=args.get("time"),
                    description=args.get("description")
                )
                task = await calendar_service.create_task(task_data)
                return {"success": True, "task_id": task.id, "message": f"Task '{task.title}' created successfully"}
            
            elif function_name == "mark_task_done":
                task = await calendar_service.mark_task_done(args["task_id"])
                return {"success": True, "message": f"Task '{task.title}' marked as done"}
            
            else:
                return {"error": f"Unknown function: {function_name}"}
                
        except Exception as e:
            return {"error": str(e)}
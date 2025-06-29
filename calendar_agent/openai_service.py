import json
from datetime import date, datetime
from openai import OpenAI

class OpenAIService:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"
    
    def get_function_definitions(self):
        return [
            {
                "name": "get_today_tasks",
                "description": "Get today's tasks from calendar",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "create_task",
                "description": "Create a new task",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Task title"},
                        "date": {"type": "string", "description": "Task date YYYY-MM-DD"},
                        "time": {"type": "string", "description": "Task time HH:MM"},
                        "description": {"type": "string", "description": "Task description"}
                    },
                    "required": ["title", "date"]
                }
            },
            {
                "name": "get_tasks_range",
                "description": "Get tasks for date range (default: today to next 30 days)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "start_date": {"type": "string", "description": "Start date YYYY-MM-DD (optional)"},
                        "end_date": {"type": "string", "description": "End date YYYY-MM-DD (optional)"}
                    }
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
    
    def chat(self, message, calendar_functions):
        current_date = date.today()
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": f"You are a task planning assistant. Current date: {current_date.strftime('%Y-%m-%d')}"},
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
            
            result = self.execute_function(function_name, function_args, calendar_functions)
            
            final_response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": f"Present task information clearly. Current date: {current_date.strftime('%Y-%m-%d')}"},
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": None, "function_call": {"name": function_name, "arguments": function_call.arguments}},
                    {"role": "function", "name": function_name, "content": json.dumps(result)}
                ],
                temperature=0.3
            )
            
            return final_response.choices[0].message.content
        else:
            return choice.message.content
    
    def execute_function(self, function_name, args, calendar_functions):
        try:
            if function_name == "get_today_tasks":
                tasks = calendar_functions['get_today_tasks']()
                return {"tasks": [{"id": t['id'], "title": t['title'], "time": str(t['time']) if t['time'] else None} for t in tasks]}
            
            elif function_name == "create_task":
                task_date = date.fromisoformat(args["date"])
                task_time = datetime.strptime(args["time"], "%H:%M").time() if args.get("time") else None
                task_id = calendar_functions['create_task'](args["title"], task_date, task_time, args.get("description"))
                return {"success": True, "task_id": task_id, "message": f"Task '{args['title']}' created"}
            
            elif function_name == "get_tasks_range":
                start_date = date.fromisoformat(args["start_date"]) if args.get("start_date") else None
                end_date = date.fromisoformat(args["end_date"]) if args.get("end_date") else None
                tasks = calendar_functions['get_tasks_range'](start_date, end_date)
                return {"tasks": [{"id": t['id'], "title": t['title'], "date": str(t['date']), "time": str(t['time']) if t['time'] else None} for t in tasks]}
            
            elif function_name == "mark_task_done":
                calendar_functions['mark_task_done'](args["task_id"])
                return {"success": True, "message": "Task marked as done"}
            
            else:
                return {"error": f"Unknown function: {function_name}"}
                
        except Exception as e:
            return {"error": str(e)}
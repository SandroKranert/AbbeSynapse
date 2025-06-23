"""
Task-Planner Agent service configuration
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# File paths
BASE_DIR = Path(__file__).resolve().parent.parent
CREDENTIALS_FILE = os.getenv("GOOGLE_CALENDAR_CREDENTIALS_FILE", "credentials/credentials.json")
TOKEN_FILE = os.getenv("GOOGLE_CALENDAR_TOKEN_FILE", "credentials/token.json")

# FastAPI Configuration
FASTAPI_HOST = os.getenv("FASTAPI_HOST", "0.0.0.0")
FASTAPI_PORT = int(os.getenv("FASTAPI_PORT", "8000"))
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

# Google Calendar API
CALENDAR_ID = os.getenv("CALENDAR_ID", "primary")
SCOPES = ["https://www.googleapis.com/auth/calendar"]

# OAuth Redirection
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:8000/auth/callback")
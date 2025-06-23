"""
OAuth authentication management with Google
"""
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from starlette.status import HTTP_401_UNAUTHORIZED

from app.config import SCOPES, CREDENTIALS_FILE, TOKEN_FILE, REDIRECT_URI, BASE_DIR
from app.models import AuthStatus

router = APIRouter(prefix="/auth", tags=["Authentication"])

def get_credentials() -> Optional[Credentials]:
    """
    Get Google credentials or None if not authenticated
    """
    token_path = BASE_DIR / TOKEN_FILE
    
    creds = None
    if token_path.exists():
        try:
            creds = Credentials.from_authorized_user_info(
                json.loads(token_path.read_text()), SCOPES
            )
        except Exception:
            return None
    
    # If credentials are expired but have refresh token
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(GoogleRequest())
            # Save updated credentials
            token_path.write_text(creds.to_json())
        except Exception:
            return None
    
    return creds if creds and creds.valid else None


def require_auth(creds: Optional[Credentials] = Depends(get_credentials)):
    """
    FastAPI dependency to verify authentication
    """
    if not creds:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please authenticate via /auth/authorize",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return creds


@router.get("/authorize")
async def authorize():
    """
    Initiate OAuth authorization flow with Google
    """
    credentials_path = BASE_DIR / CREDENTIALS_FILE
    
    if not credentials_path.exists():
        raise HTTPException(
            status_code=500, 
            detail=f"Credentials file not found: {CREDENTIALS_FILE}"
        )
    
    # Create OAuth flow
    flow = Flow.from_client_secrets_file(
        str(credentials_path),
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    
    # Authorization URL
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'  # Force refresh_token request
    )
    
    # Temporary state storage
    os.environ["OAUTH_STATE"] = state
    
    # Redirect to Google authorization URL
    return RedirectResponse(authorization_url)


@router.get("/callback")
async def callback(code: str, state: str, request: Request):
    """
    OAuth callback after Google authorization
    """
    stored_state = os.environ.get("OAUTH_STATE")
    
    if not stored_state or state != stored_state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")
    
    credentials_path = BASE_DIR / CREDENTIALS_FILE
    
    # Finalize OAuth flow
    flow = Flow.from_client_secrets_file(
        str(credentials_path),
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
        state=state
    )
    
    # Exchange code for token
    flow.fetch_token(code=code)
    credentials = flow.credentials
    
    # Save token
    token_path = BASE_DIR / TOKEN_FILE
    token_path.parent.mkdir(exist_ok=True)
    token_path.write_text(credentials.to_json())
    
    return {"message": "Authentication successful! You can close this window."}


@router.get("/status", response_model=AuthStatus)
async def auth_status():
    """
    Check authentication status
    """
    creds = get_credentials()
    
    if not creds:
        return AuthStatus(
            authenticated=False,
            expires_at=None,
            message="Not authenticated. Use /auth/authorize to connect."
        )
    
    # Calculate expiration date
    expires_at = datetime.now() + timedelta(seconds=creds.expiry.timestamp() - datetime.now().timestamp())
    
    return AuthStatus(
        authenticated=True,
        expires_at=expires_at,
        message="Successfully authenticated"
    )

# Import json already added at the top of the file
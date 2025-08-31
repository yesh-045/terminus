"""
Shared Google OAuth2 authentication system for Gmail and Calendar APIs.
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow, InstalledAppFlow

log = logging.getLogger(__name__)

# Gmail and Calendar API scopes
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose", 
    "https://www.googleapis.com/auth/calendar",
]

# Credential storage location
CREDS_DIR = Path.home() / ".config" / "terminus"
TOKEN_FILE = CREDS_DIR / "google_token.json"
CLIENT_SECRET_FILE = CREDS_DIR / "google_client_secret.json"


class GoogleAuthError(Exception):
    """Raised when Google authentication fails."""
    pass


def get_credentials_path() -> Path:
    """Get the path where Google credentials should be stored."""
    return CLIENT_SECRET_FILE


def has_valid_credentials() -> bool:
    """Check if we have valid Google API credentials."""
    return TOKEN_FILE.exists() and _load_credentials() is not None


def _load_credentials() -> Optional[Credentials]:
    """Load credentials from token file."""
    if not TOKEN_FILE.exists():
        return None
        
    try:
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        
        # Refresh if expired
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            _save_credentials(creds)
            
        return creds if creds and creds.valid else None
    except Exception as e:
        log.debug(f"Failed to load credentials: {e}")
        return None


def _save_credentials(creds: Credentials) -> None:
    """Save credentials to token file."""
    CREDS_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(TOKEN_FILE, 'w') as token:
        token.write(creds.to_json())


def setup_google_auth() -> bool:
    """
    Set up Google authentication. Returns True if successful.
    
    This function should be called during first-time setup or when
    re-authentication is needed.
    """
    if not CLIENT_SECRET_FILE.exists():
        return False
        
    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            str(CLIENT_SECRET_FILE), SCOPES
        )
        
        # Use local server for OAuth flow
        creds = flow.run_local_server(port=0, prompt='select_account')
        
        _save_credentials(creds)
        return True
        
    except Exception as e:
        log.error(f"Google authentication setup failed: {e}")
        return False


def get_authenticated_credentials() -> Credentials:
    """
    Get authenticated Google API credentials.
    
    Returns:
        Credentials: Valid Google API credentials
        
    Raises:
        GoogleAuthError: If authentication fails or credentials are invalid
    """
    creds = _load_credentials()
    
    if not creds:
        if not setup_google_auth():
            raise GoogleAuthError(
                "Google authentication failed. Please ensure you have set up "
                "your Google API credentials properly."
            )
        creds = _load_credentials()
        
    if not creds or not creds.valid:
        raise GoogleAuthError(
            "Invalid Google credentials. Please run the setup process again."
        )
        
    return creds


def create_client_secret_file(client_id: str, client_secret: str) -> bool:
    """
    Create the client secret file from provided credentials.
    
    Args:
        client_id: Google OAuth2 client ID
        client_secret: Google OAuth2 client secret
        
    Returns:
        bool: True if file was created successfully
    """
    try:
        CREDS_DIR.mkdir(parents=True, exist_ok=True)
        
        client_config = {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": ["http://localhost"]
            }
        }
        
        with open(CLIENT_SECRET_FILE, 'w') as f:
            json.dump(client_config, f, indent=2)
            
        return True
        
    except Exception as e:
        log.error(f"Failed to create client secret file: {e}")
        return False


def revoke_credentials() -> bool:
    """
    Revoke Google API credentials and remove local files.
    
    Returns:
        bool: True if credentials were successfully revoked
    """
    try:
        creds = _load_credentials()
        if creds:
            # Revoke the credentials
            import requests
            requests.post('https://oauth2.googleapis.com/revoke',
                         params={'token': creds.token},
                         headers={'content-type': 'application/x-www-form-urlencoded'})
        
        # Remove local files
        if TOKEN_FILE.exists():
            TOKEN_FILE.unlink()
            
        return True
        
    except Exception as e:
        log.error(f"Failed to revoke credentials: {e}")
        return False


def get_authentication_status() -> dict:
    """
    Get the current Google authentication status.
    
    Returns:
        dict: Status information including validity and expiration
    """
    creds = _load_credentials()
    
    if not creds:
        return {
            "authenticated": False,
            "valid": False,
            "expired": None,
            "scopes": SCOPES
        }
    
    return {
        "authenticated": True,
        "valid": creds.valid,
        "expired": creds.expired,
        "expiry": creds.expiry.isoformat() if creds.expiry else None,
        "scopes": SCOPES
    }

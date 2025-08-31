"""
Google API setup and authentication management tool.
"""

import logging
from typing import Optional

from pydantic_ai import RunContext

from ...core.deps import ToolDeps
from .google_auth import (
    has_valid_credentials,
    get_authentication_status,
    setup_google_auth,
    revoke_credentials,
    create_client_secret_file,
    GoogleAuthError
)

log = logging.getLogger(__name__)


async def google_auth_status(ctx: RunContext[ToolDeps]) -> str:
    """
    Check the current Google API authentication status.
    
    Returns:
        Current authentication status and available actions
    """
    try:
        if ctx.deps and ctx.deps.display_tool_status:
            await ctx.deps.display_tool_status("google_auth_status", "Checking Google authentication status")
        
        status = get_authentication_status()
        
        if not status["authenticated"]:
            return """❌ **Google API Not Configured**

To use Gmail and Calendar features:

1. **Get Google API Credentials:**
   - Go to https://console.developers.google.com
   - Create a new project or select existing
   - Enable Gmail API and Calendar API
   - Create OAuth2 credentials (Desktop application)
   - Download the client secret JSON

2. **Configure Terminus:**
   - Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to your config
   - Or run setup again: `terminus` and choose to set up Google API

3. **Complete OAuth:**
   - First Gmail/Calendar command will open browser for authorization"""
        
        if status["valid"]:
            return f"""✅ **Google API Authenticated & Ready**

**Status:** Valid credentials
**Scopes:** Gmail (read/compose), Calendar (full access)
**Expires:** {status.get('expiry', 'Unknown')}

**Available Commands:**
- `list_unread` - Check unread emails
- `summary <email_id>` - Summarize email content  
- `generate_draft <prompt>` - Create email drafts
- `search_email <query>` - Search your emails
- `add_event <title> <time>` - Schedule events
- `check_availability <start> <end>` - Check calendar conflicts
- `block_focus <duration>` - Create focus blocks"""
        
        else:
            return f"""⚠️ **Google API Authentication Expired**

**Status:** Credentials expired on {status.get('expiry', 'Unknown')}

**To fix:** Run any Gmail/Calendar command and you'll be prompted to re-authenticate automatically."""
            
    except Exception as e:
        log.error(f"Error checking Google auth status: {e}")
        return f"Error checking authentication status: {e}"


async def google_auth_setup(ctx: RunContext[ToolDeps], client_id: str = "", client_secret: str = "") -> str:
    """
    Set up Google API authentication with provided credentials.
    
    Args:
        client_id: Google OAuth2 client ID (optional if already configured)
        client_secret: Google OAuth2 client secret (optional if already configured)
        
    Returns:
        Setup result and next steps
    """
    try:
        if ctx.deps.confirm_action:
            confirmed = await ctx.deps.confirm_action(
                "google_auth_setup: Configure Google API",
                "This will set up Google API authentication for Gmail and Calendar features.",
                "Your browser will open for OAuth authorization."
            )
            if not confirmed:
                return "Google API setup cancelled by user."
        
        await ctx.deps.display_tool_status("google_auth_setup", "Setting up Google authentication")
        
        # Create client secret file if credentials provided
        if client_id and client_secret:
            if not create_client_secret_file(client_id, client_secret):
                return "❌ Failed to create client secret file. Check your credentials."
        
        # Attempt OAuth setup
        if setup_google_auth():
            return """✅ **Google API Setup Complete!**

Your browser was used to complete OAuth authorization.
Gmail and Calendar features are now available.

**Test it out:**
- `list_unread 5` - Check your latest emails
- `check_availability today 2pm today 4pm` - Check calendar conflicts
- `add_event "Team meeting" "tomorrow at 10am"` - Schedule an event"""
        
        else:
            return """❌ **Google API Setup Failed**

**Possible issues:**
1. Invalid client credentials
2. Browser authorization was cancelled
3. Network connectivity problems

**To fix:**
1. Verify your Google API credentials
2. Ensure Gmail API and Calendar API are enabled in Google Console
3. Try the setup process again"""
            
    except Exception as e:
        log.error(f"Error in Google auth setup: {e}")
        return f"Setup error: {e}"


async def google_auth_revoke(ctx: RunContext[ToolDeps]) -> str:
    """
    Revoke Google API authentication and remove stored credentials.
    
    Returns:
        Confirmation of credential revocation
    """
    try:
        if ctx.deps.confirm_action:
            confirmed = await ctx.deps.confirm_action(
                "google_auth_revoke: Revoke Google API access",
                "This will permanently revoke Terminus access to your Gmail and Calendar.",
                "You'll need to re-authenticate to use Gmail/Calendar features again."
            )
            if not confirmed:
                return "Credential revocation cancelled by user."
        
        await ctx.deps.display_tool_status("google_auth_revoke", "Revoking Google authentication")
        
        if revoke_credentials():
            return """✅ **Google API Access Revoked**

Terminus no longer has access to your Gmail and Calendar.
All stored authentication tokens have been removed.

To re-enable Gmail/Calendar features, run the setup process again."""
        
        else:
            return "❌ Failed to revoke credentials. They may have already been revoked."
            
    except Exception as e:
        log.error(f"Error revoking Google auth: {e}")
        return f"Revocation error: {e}"

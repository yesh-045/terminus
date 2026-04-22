"""
Integration tools for Terminus CLI.
"""

from .gmail import list_unread, summary, generate_draft, search_email
from .calendar import add_event, check_availability, block_focus
from .google_setup import google_auth_status, google_auth_setup, google_auth_revoke

__all__ = [
    "list_unread",
    "summary", 
    "generate_draft",
    "search_email",
    "add_event",
    "check_availability",
    "block_focus",
    "google_auth_status",
    "google_auth_setup",
    "google_auth_revoke",
]

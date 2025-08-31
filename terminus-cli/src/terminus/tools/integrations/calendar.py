"""
Google Calendar integration tools for Terminus.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from pydantic_ai import RunContext
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ...core.deps import ToolDeps
from .google_auth import get_authenticated_credentials, GoogleAuthError

log = logging.getLogger(__name__)


class CalendarError(Exception):
    """Raised when Calendar API operations fail."""
    pass


def _get_calendar_service():
    """Get authenticated Google Calendar API service."""
    try:
        creds = get_authenticated_credentials()
        return build('calendar', 'v3', credentials=creds)
    except GoogleAuthError as e:
        raise CalendarError(f"Calendar authentication failed: {e}")
    except Exception as e:
        raise CalendarError(f"Failed to create Calendar service: {e}")


def _parse_time_string(time_str: str) -> datetime:
    """Parse various time string formats into datetime objects."""
    import dateutil.parser
    try:
        return dateutil.parser.parse(time_str)
    except Exception:
        # Fallback for relative times like "tomorrow at 2pm"
        from datetime import datetime, timedelta
        import re
        
        now = datetime.now()
        
        # Handle "tomorrow"
        if "tomorrow" in time_str.lower():
            base_date = now + timedelta(days=1)
        # Handle "today"
        elif "today" in time_str.lower():
            base_date = now
        # Handle "next [day]"
        elif "next" in time_str.lower():
            # Simple implementation - add 7 days
            base_date = now + timedelta(days=7)
        else:
            base_date = now
        
        # Extract time if present
        time_match = re.search(r'(\d{1,2}):?(\d{0,2})\s*(am|pm)', time_str.lower())
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2)) if time_match.group(2) else 0
            ampm = time_match.group(3)
            
            if ampm == 'pm' and hour != 12:
                hour += 12
            elif ampm == 'am' and hour == 12:
                hour = 0
                
            return base_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # Default to current time
        return base_date


async def add_event(ctx: RunContext[ToolDeps], title: str, time: str, duration: int = 60) -> str:
    """
    Schedule a new calendar event.
    
    Args:
        title: Event title/description
        time: When to schedule (e.g., "tomorrow at 2pm", "2024-01-15 14:00")
        duration: Duration in minutes (default: 60)
        
    Returns:
        Confirmation with event details and calendar link
    """
    try:
        # Event creation requires confirmation
        if ctx.deps.confirm_action:
            confirmed = await ctx.deps.confirm_action(
                "add_event: Create calendar event",
                f"Event: {title}\nTime: {time}\nDuration: {duration} minutes",
                "This will create a new event in your Google Calendar."
            )
            if not confirmed:
                return "Event creation cancelled by user."
        
        if ctx.deps and ctx.deps.display_tool_status:
            await ctx.deps.display_tool_status("add_event", title=title, time=time, duration=duration)
        
        # Parse the time string
        try:
            start_time = _parse_time_string(time)
        except Exception as e:
            return f"Error parsing time '{time}': {e}. Please use formats like 'tomorrow at 2pm' or '2024-01-15 14:00'"
        
        from datetime import timedelta
        end_time = start_time + timedelta(minutes=duration)
        
        # Check for conflicts first
        conflicts = await check_availability(ctx, start_time.isoformat(), end_time.isoformat())
        if "conflicts found" in conflicts.lower():
            return f"⚠️ Scheduling conflict detected:\n{conflicts}\n\nEvent NOT created. Please choose a different time."
        
        # Create the event
        service = _get_calendar_service()
        
        event = {
            'summary': title,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'UTC',
            },
            'description': f'Event created by Terminus CLI at {datetime.now().strftime("%Y-%m-%d %H:%M")}'
        }
        
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        
        return f"✓ Event created successfully!\n\n**Title:** {title}\n**Start:** {start_time.strftime('%Y-%m-%d %H:%M')}\n**End:** {end_time.strftime('%Y-%m-%d %H:%M')}\n**Duration:** {duration} minutes\n\n**Event ID:** {created_event['id']}\n**Calendar Link:** {created_event.get('htmlLink', 'N/A')}"
        
    except HttpError as e:
        return f"Calendar API error: {e.resp.status} - {e.content.decode()}"
    except CalendarError as e:
        return f"Calendar error: {e}"
    except Exception as e:
        log.error(f"Unexpected error in add_event: {e}")
        return f"Unexpected error: {e}"


async def check_availability(ctx: RunContext[ToolDeps], start: str, end: str) -> str:
    """
    Check availability and detect scheduling conflicts.
    
    Args:
        start: Start time (ISO format or natural language)
        end: End time (ISO format or natural language)
        
    Returns:
        Availability status and any conflicts found
    """
    try:
        if ctx.deps and ctx.deps.display_tool_status:
            await ctx.deps.display_tool_status("check_availability", start=start, end=end)
        
        # Parse time strings if needed
        if not start.endswith('Z') and 'T' not in start:
            start_dt = _parse_time_string(start)
            start = start_dt.isoformat() + 'Z'
        
        if not end.endswith('Z') and 'T' not in end:
            end_dt = _parse_time_string(end)
            end = end_dt.isoformat() + 'Z'
        
        service = _get_calendar_service()
        
        # Query for events in the specified time range
        events_result = service.events().list(
            calendarId='primary',
            timeMin=start,
            timeMax=end,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            return f"✅ You are available from {start} to {end} - no conflicts found."
        
        # Format conflicts
        conflicts = []
        for event in events:
            event_start = event['start'].get('dateTime', event['start'].get('date'))
            event_end = event['end'].get('dateTime', event['end'].get('date'))
            title = event.get('summary', 'Untitled Event')
            
            conflicts.append(f"- **{title}**")
            conflicts.append(f"  From: {event_start}")
            conflicts.append(f"  To: {event_end}")
            conflicts.append("")
        
        return f"⚠️ {len(events)} scheduling conflicts found:\n\n" + "\n".join(conflicts)
        
    except HttpError as e:
        return f"Calendar API error: {e.resp.status} - {e.content.decode()}"
    except CalendarError as e:
        return f"Calendar error: {e}"
    except Exception as e:
        log.error(f"Unexpected error in check_availability: {e}")
        return f"Unexpected error: {e}"


async def block_focus(ctx: RunContext[ToolDeps], duration: int, when: str = "next available") -> str:
    """
    Create a focus time block in the calendar.
    
    Args:
        duration: Duration in minutes
        when: When to schedule the focus block (default: "next available")
        
    Returns:
        Confirmation of focus block creation
    """
    try:
        # Focus block creation requires confirmation
        if ctx.deps.confirm_action:
            confirmed = await ctx.deps.confirm_action(
                "block_focus: Create focus time block",
                f"Duration: {duration} minutes\nWhen: {when}",
                "This will create a focus time block in your Google Calendar."
            )
            if not confirmed:
                return "Focus block creation cancelled by user."
        
        if ctx.deps and ctx.deps.display_tool_status:
            await ctx.deps.display_tool_status("block_focus", duration=duration, when=when)
        
        # Determine the start time
        if when.lower() == "next available":
            # Find next available slot during business hours
            now = datetime.now()
            
            # Start checking from the next hour
            start_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            
            # Look for availability in the next 7 days
            for day_offset in range(7):
                check_date = start_time + timedelta(days=day_offset)
                
                # Check business hours (9 AM to 5 PM)
                for hour in range(9, 17):
                    candidate_start = check_date.replace(hour=hour)
                    candidate_end = candidate_start + timedelta(minutes=duration)
                    
                    # Check if this slot is available
                    availability = await check_availability(
                        ctx, 
                        candidate_start.isoformat(),
                        candidate_end.isoformat()
                    )
                    
                    if "no conflicts found" in availability:
                        start_time = candidate_start
                        break
                else:
                    continue
                break
            else:
                return "Could not find an available slot in the next 7 days during business hours."
        else:
            # Parse the specific time
            try:
                start_time = _parse_time_string(when)
            except Exception as e:
                return f"Error parsing time '{when}': {e}"
        
        end_time = start_time + timedelta(minutes=duration)
        
        # Create the focus block
        service = _get_calendar_service()
        
        event = {
            'summary': f'🎯 Focus Time ({duration}m)',
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'UTC',
            },
            'description': f'Focus time block created by Terminus CLI.\n\nDuration: {duration} minutes\nCreated: {datetime.now().strftime("%Y-%m-%d %H:%M")}',
            'colorId': '10',  # Green color for focus blocks
            'transparency': 'opaque'  # Show as busy
        }
        
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        
        return f"✅ Focus time block created!\n\n**Duration:** {duration} minutes\n**Start:** {start_time.strftime('%Y-%m-%d %H:%M')}\n**End:** {end_time.strftime('%Y-%m-%d %H:%M')}\n\n**Event ID:** {created_event['id']}\n**Calendar Link:** {created_event.get('htmlLink', 'N/A')}\n\n🎯 Your focus time is blocked - notifications and meetings will be avoided during this period."
        
    except HttpError as e:
        return f"Calendar API error: {e.resp.status} - {e.content.decode()}"
    except CalendarError as e:
        return f"Calendar error: {e}"
    except Exception as e:
        log.error(f"Unexpected error in block_focus: {e}")
        return f"Unexpected error: {e}"

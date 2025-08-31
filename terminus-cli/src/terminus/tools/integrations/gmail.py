"""
Gmail integration tools for Terminus.
"""

import logging
from typing import List, Optional

from pydantic_ai import RunContext
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ...core.deps import ToolDeps
from .google_auth import get_authenticated_credentials, GoogleAuthError

log = logging.getLogger(__name__)


class GmailError(Exception):
    """Raised when Gmail API operations fail."""
    pass


def _get_gmail_service():
    """Get authenticated Gmail API service."""
    try:
        creds = get_authenticated_credentials()
        return build('gmail', 'v1', credentials=creds)
    except GoogleAuthError as e:
        raise GmailError(f"Gmail authentication failed: {e}")
    except Exception as e:
        raise GmailError(f"Failed to create Gmail service: {e}")


async def list_unread(ctx: RunContext[ToolDeps], n: int = 10) -> str:
    """
    Fetch top N unread emails from Gmail.
    
    Args:
        n: Number of unread emails to fetch (default: 10, max: 50)
        
    Returns:
        Formatted list of unread emails with sender, subject, and snippet
    """
    if n <= 0 or n > 50:
        return "Error: Number of emails must be between 1 and 50"
    
    try:
        if ctx.deps and ctx.deps.display_tool_status:
            await ctx.deps.display_tool_status("list_unread", count=n)
        
        service = _get_gmail_service()
        
        # Search for unread messages
        results = service.users().messages().list(
            userId='me',
            q='is:unread',
            maxResults=n
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            return "No unread emails found."
        
        email_list = []
        for i, msg in enumerate(messages, 1):
            # Get message details
            message = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='metadata',
                metadataHeaders=['From', 'Subject', 'Date']
            ).execute()
            
            headers = message['payload'].get('headers', [])
            from_header = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            subject_header = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            date_header = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')
            
            # Get snippet
            snippet = message.get('snippet', '')[:100] + ('...' if len(message.get('snippet', '')) > 100 else '')
            
            email_list.append(f"{i}. **From:** {from_header}")
            email_list.append(f"   **Subject:** {subject_header}")
            email_list.append(f"   **Date:** {date_header}")
            email_list.append(f"   **Preview:** {snippet}")
            email_list.append(f"   **ID:** {msg['id']}")
            email_list.append("")
        
        return f"Found {len(messages)} unread emails:\n\n" + "\n".join(email_list)
        
    except HttpError as e:
        return f"Gmail API error: {e.resp.status} - {e.content.decode()}"
    except GmailError as e:
        return f"Gmail error: {e}"
    except Exception as e:
        log.error(f"Unexpected error in list_unread: {e}")
        return f"Unexpected error: {e}"


async def summary(ctx: RunContext[ToolDeps], msg_id: str) -> str:
    """
    Generate a concise summary of an email using LLM.
    
    Args:
        msg_id: Gmail message ID to summarize
        
    Returns:
        AI-generated summary of the email content
    """
    try:
        # This operation reads email content, so require confirmation
        if ctx.deps and ctx.deps.confirm_action:
            confirmed = await ctx.deps.confirm_action(
                "summary: Generate email summary",
                f"This will read and analyze the content of email ID: {msg_id}",
                "The email content will be processed by the AI model to generate a summary."
            )
            if not confirmed:
                return "Email summary cancelled by user."
        
        if ctx.deps and ctx.deps.display_tool_status:
            await ctx.deps.display_tool_status("summary", message_id=msg_id)
        
        service = _get_gmail_service()
        
        # Get full message content
        message = service.users().messages().get(
            userId='me',
            id=msg_id,
            format='full'
        ).execute()
        
        # Extract text content with better handling
        def extract_text(payload):
            text_content = ""
            if 'parts' in payload:
                for part in payload['parts']:
                    text_content += extract_text(part)
            elif payload.get('mimeType') in ['text/plain', 'text/html']:
                data = payload.get('body', {}).get('data')
                if data:
                    import base64
                    try:
                        decoded_text = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                        # If it's HTML, strip tags for basic text extraction
                        if payload.get('mimeType') == 'text/html':
                            import re
                            # Basic HTML tag removal
                            decoded_text = re.sub(r'<[^>]+>', '', decoded_text)
                            # Clean up extra whitespace
                            decoded_text = re.sub(r'\s+', ' ', decoded_text)
                        text_content = decoded_text
                    except Exception as e:
                        log.error(f"Error decoding email content: {e}")
            return text_content
        
        email_text = extract_text(message['payload'])
        
        if not email_text.strip():
            # Better error reporting for debugging
            payload_info = {
                'mimeType': message['payload'].get('mimeType'),
                'has_parts': 'parts' in message['payload'],
                'has_body_data': bool(message['payload'].get('body', {}).get('data'))
            }
            log.error(f"Could not extract text content. Payload info: {payload_info}")
            return f"Error: Could not extract text content from email. Email format: {payload_info['mimeType']}, Has parts: {payload_info['has_parts']}, Has body data: {payload_info['has_body_data']}"
        
        # Get headers for context
        headers = message['payload'].get('headers', [])
        from_header = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
        subject_header = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        
        # Create a simple summary without using the agent (to avoid circular dependencies)
        # Extract first few sentences for a quick summary
        lines = email_text.split('\n')
        content_lines = [line.strip() for line in lines if line.strip() and not line.startswith('>')]
        
        # Get first paragraph or up to 300 characters
        summary_text = ""
        char_count = 0
        for line in content_lines[:10]:  # First 10 non-empty lines
            if char_count + len(line) > 300:
                break
            summary_text += line + " "
            char_count += len(line)
        
        if not summary_text.strip():
            summary_text = "Email content could not be summarized."
        
        return f"**Email Summary**\n\n**From:** {from_header}\n**Subject:** {subject_header}\n\n**Content Preview:**\n{summary_text.strip()[:300]}{'...' if len(summary_text) > 300 else ''}\n\n**Full Length:** {len(email_text)} characters"
        
    except HttpError as e:
        return f"Gmail API error: {e.resp.status} - {e.content.decode()}"
    except GmailError as e:
        return f"Gmail error: {e}"
    except Exception as e:
        log.error(f"Unexpected error in summary: {e}")
        return f"Unexpected error: {e}"


async def generate_draft(ctx: RunContext[ToolDeps], prompt: str) -> str:
    """
    Create an email draft from a natural language prompt using LLM.
    
    Args:
        prompt: Natural language description of the email to create
        
    Returns:
        Confirmation that draft was created with draft ID
    """
    try:
        # Draft creation requires confirmation
        if ctx.deps.confirm_action:
            confirmed = await ctx.deps.confirm_action(
                "generate_draft: Create email draft",
                f"This will create an email draft based on: {prompt[:100]}...",
                "A new draft email will be created in your Gmail account."
            )
            if not confirmed:
                return "Draft creation cancelled by user."
        
        if ctx.deps and ctx.deps.display_tool_status:
            await ctx.deps.display_tool_status("generate_draft", prompt=prompt[:50] + "...")
        
        # Use AI to generate email content
        from terminus.agent import get_or_create_agent
        
        draft_prompt = f"""Generate a professional email based on this request: {prompt}

Please provide:
1. An appropriate subject line
2. The email body text
3. Appropriate salutation and closing

Format your response as:
SUBJECT: [subject line]
BODY:
[email body]

Keep it professional, clear, and concise."""

        agent = get_or_create_agent()
        result = await agent.run(draft_prompt, message_history=[])
        
        # Parse the AI response
        ai_response = result.data
        lines = ai_response.split('\n')
        
        subject = ""
        body = ""
        body_started = False
        
        for line in lines:
            if line.startswith('SUBJECT:'):
                subject = line.replace('SUBJECT:', '').strip()
            elif line.startswith('BODY:'):
                body_started = True
            elif body_started:
                body += line + '\n'
        
        if not subject:
            subject = "Email generated by Terminus"
        
        body = body.strip()
        
        # Create draft in Gmail
        service = _get_gmail_service()
        
        message = {
            'message': {
                'raw': _create_message('', '', subject, body)
            }
        }
        
        draft = service.users().drafts().create(userId='me', body=message).execute()
        
        return f"✓ Email draft created successfully!\n\n**Subject:** {subject}\n\n**Body Preview:**\n{body[:200]}...\n\n**Draft ID:** {draft['id']}\n\nYou can find this draft in your Gmail drafts folder."
        
    except HttpError as e:
        return f"Gmail API error: {e.resp.status} - {e.content.decode()}"
    except GmailError as e:
        return f"Gmail error: {e}"
    except Exception as e:
        log.error(f"Unexpected error in generate_draft: {e}")
        return f"Unexpected error: {e}"


async def search_email(ctx: RunContext[ToolDeps], query: str) -> str:
    """
    Search emails by sender, subject, or content.
    
    Args:
        query: Search query (e.g., "from:john@example.com", "subject:meeting", "budget report")
        
    Returns:
        List of matching emails with basic information
    """
    try:
        if ctx.deps and ctx.deps.display_tool_status:
            await ctx.deps.display_tool_status("search_email", query=query)
        
        service = _get_gmail_service()
        
        # Search for messages
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=20  # Limit to 20 results
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            return f"No emails found matching query: {query}"
        
        email_list = []
        for i, msg in enumerate(messages, 1):
            # Get message details
            message = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='metadata',
                metadataHeaders=['From', 'Subject', 'Date']
            ).execute()
            
            headers = message['payload'].get('headers', [])
            from_header = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            subject_header = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            date_header = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')
            
            # Get snippet
            snippet = message.get('snippet', '')[:100] + ('...' if len(message.get('snippet', '')) > 100 else '')
            
            email_list.append(f"{i}. **From:** {from_header}")
            email_list.append(f"   **Subject:** {subject_header}")
            email_list.append(f"   **Date:** {date_header}")
            email_list.append(f"   **Preview:** {snippet}")
            email_list.append(f"   **ID:** {msg['id']}")
            email_list.append("")
        
        return f"Found {len(messages)} emails matching '{query}':\n\n" + "\n".join(email_list)
        
    except HttpError as e:
        return f"Gmail API error: {e.resp.status} - {e.content.decode()}"
    except GmailError as e:
        return f"Gmail error: {e}"
    except Exception as e:
        log.error(f"Unexpected error in search_email: {e}")
        return f"Unexpected error: {e}"


def _create_message(to: str, from_addr: str, subject: str, message_text: str) -> str:
    """Create a message for Gmail API in base64 format."""
    import base64
    import email.mime.text
    
    message = email.mime.text.MIMEText(message_text)
    message['to'] = to
    message['from'] = from_addr
    message['subject'] = subject
    
    return base64.urlsafe_b64encode(message.as_bytes()).decode()

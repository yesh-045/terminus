"""
Persistent session management for Terminus CLI.
Handles session saving, loading, and restoration across restarts.
"""

import json
import logging
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from terminus.core.session import session

log = logging.getLogger(__name__)


class SessionPersistence:
    """Manages persistent session storage and restoration."""
    
    def __init__(self):
        self.session_dir = Path.home() / ".config" / "terminus" / "sessions"
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.current_session_file = self.session_dir / "current.json"
        self.history_file = self.session_dir / "history.json"
        
    def save_session(self, session_name: Optional[str] = None) -> str:
        """Save current session to disk."""
        try:
            session_data = {
                "timestamp": datetime.now().isoformat(),
                "model": session.current_model,
                "working_directory": str(session.working_directory),
                "confirmation_enabled": session.confirmation_enabled,
                "disabled_confirmations": list(session.disabled_confirmations),
                "message_count": len(session.messages),
                "session_name": session_name or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
            
            # Save current session
            with open(self.current_session_file, "w") as f:
                json.dump(session_data, f, indent=2)
                
            # Add to history
            self._add_to_history(session_data)
            
            return session_data["session_name"]
            
        except Exception as e:
            log.error(f"Failed to save session: {e}")
            raise
            
    def load_session(self, session_name: Optional[str] = None) -> bool:
        """Load session from disk."""
        try:
            if session_name:
                # Load specific session from history
                session_data = self._load_from_history(session_name)
            else:
                # Load current session
                if not self.current_session_file.exists():
                    return False
                    
                with open(self.current_session_file, "r") as f:
                    session_data = json.load(f)
                    
            if session_data:
                self._restore_session(session_data)
                return True
                
            return False
            
        except Exception as e:
            log.error(f"Failed to load session: {e}")
            return False
            
    def _restore_session(self, session_data: Dict[str, Any]):
        """Restore session state from data."""
        # Restore basic settings
        session.current_model = session_data.get("model", session.current_model)
        session.confirmation_enabled = session_data.get("confirmation_enabled", True)
        session.disabled_confirmations = set(session_data.get("disabled_confirmations", []))
        
        # Restore working directory
        working_dir = session_data.get("working_directory")
        if working_dir and Path(working_dir).exists():
            session.working_directory = Path(working_dir)
            
    def _add_to_history(self, session_data: Dict[str, Any]):
        """Add session to history."""
        try:
            history = []
            if self.history_file.exists():
                with open(self.history_file, "r") as f:
                    history = json.load(f)
                    
            # Add new session
            history.append(session_data)
            
            # Keep only last 50 sessions
            history = history[-50:]
            
            with open(self.history_file, "w") as f:
                json.dump(history, f, indent=2)
                
        except Exception as e:
            log.error(f"Failed to update session history: {e}")
            
    def _load_from_history(self, session_name: str) -> Optional[Dict[str, Any]]:
        """Load specific session from history."""
        try:
            if not self.history_file.exists():
                return None
                
            with open(self.history_file, "r") as f:
                history = json.load(f)
                
            # Find session by name
            for session_data in reversed(history):  # Most recent first
                if session_data.get("session_name") == session_name:
                    return session_data
                    
            return None
            
        except Exception as e:
            log.error(f"Failed to load session from history: {e}")
            return None
            
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all saved sessions."""
        try:
            if not self.history_file.exists():
                return []
                
            with open(self.history_file, "r") as f:
                history = json.load(f)
                
            return list(reversed(history))  # Most recent first
            
        except Exception as e:
            log.error(f"Failed to list sessions: {e}")
            return []
            
    def delete_session(self, session_name: str) -> bool:
        """Delete a saved session."""
        try:
            if not self.history_file.exists():
                return False
                
            with open(self.history_file, "r") as f:
                history = json.load(f)
                
            # Remove session
            original_count = len(history)
            history = [s for s in history if s.get("session_name") != session_name]
            
            if len(history) < original_count:
                with open(self.history_file, "w") as f:
                    json.dump(history, f, indent=2)
                return True
                
            return False
            
        except Exception as e:
            log.error(f"Failed to delete session: {e}")
            return False
            
    def auto_save(self):
        """Automatically save current session."""
        try:
            # Only auto-save if there's meaningful conversation content
            # Skip if no messages or only system/setup messages
            if len(session.messages) < 2:
                return
                
            # Skip if last message was very recent (avoid duplicate saves)
            if hasattr(self, '_last_auto_save_time'):
                from datetime import datetime, timedelta
                if datetime.now() - self._last_auto_save_time < timedelta(minutes=1):
                    return
                    
            # Check if session has meaningful content (actual user interactions)
            user_messages = [msg for msg in session.messages if msg.get('role') == 'user']
            if len(user_messages) > 0:
                self.save_session("auto_save")
                self._last_auto_save_time = datetime.now()
        except Exception as e:
            log.error(f"Auto-save failed: {e}")
            
    def auto_restore(self) -> bool:
        """Automatically restore last session on startup."""
        try:
            return self.load_session()
        except Exception as e:
            log.error(f"Auto-restore failed: {e}")
            return False
            
    def cleanup_sessions(self) -> int:
        """Clean up unnecessary auto-save and status check sessions."""
        try:
            if not self.history_file.exists():
                return 0
                
            with open(self.history_file, "r") as f:
                history = json.load(f)
                
            original_count = len(history)
            
            # Remove sessions with 0 messages and auto-generated names
            cleaned_history = []
            for session_data in history:
                session_name = session_data.get("session_name", "")
                msg_count = session_data.get("message_count", 0)
                
                # Keep sessions that:
                # 1. Have actual messages (>0)
                # 2. Are not auto-saves with 0 messages
                # 3. Are not status checks
                should_keep = (
                    msg_count > 0 or 
                    (not session_name.startswith("auto_save") and 
                     not session_name.startswith("current_status_check") and
                     not session_name.startswith("exit_session"))
                )
                
                if should_keep:
                    cleaned_history.append(session_data)
                    
            if len(cleaned_history) < original_count:
                with open(self.history_file, "w") as f:
                    json.dump(cleaned_history, f, indent=2)
                    
            return original_count - len(cleaned_history)
            
        except Exception as e:
            log.error(f"Failed to cleanup sessions: {e}")
            return 0
            
    def clear_all_sessions(self) -> int:
        """Clear all saved sessions."""
        try:
            if not self.history_file.exists():
                return 0
                
            with open(self.history_file, "r") as f:
                history = json.load(f)
                
            session_count = len(history)
            
            # Clear history file
            with open(self.history_file, "w") as f:
                json.dump([], f, indent=2)
                
            # Also clear current session file
            if self.current_session_file.exists():
                self.current_session_file.unlink()
                
            return session_count
            
        except Exception as e:
            log.error(f"Failed to clear sessions: {e}")
            return 0


# Global persistence manager
persistence = SessionPersistence()

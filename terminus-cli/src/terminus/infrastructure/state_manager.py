import json
import logging
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

log = logging.getLogger(__name__)

@dataclass
class ContextEntry:
    """A single context entry representing a command and its result."""
    timestamp: str
    command: str
    working_directory: str
    success: bool
    summary: Optional[str] = None  # Brief summary of what happened
    tag: Optional[str] = None      # Associated tag if any

@dataclass
class ProjectState:
    """State for a tagged project."""
    tag: str
    working_directory: str
    created_at: str
    last_accessed: str
    context_entries: List[ContextEntry] = field(default_factory=list)
    notes: str = ""

@dataclass
class StateData:
    """Complete application state."""
    current_tag: Optional[str] = None
    recent_context: List[ContextEntry] = field(default_factory=list)
    project_states: Dict[str, ProjectState] = field(default_factory=dict)
    command_history: List[str] = field(default_factory=list)
    fuzzy_patterns: Dict[str, str] = field(default_factory=dict)  # user patterns -> tool calls

class StateManager:
    """Manages application state, context, and persistence."""
    
    MAX_CONTEXT_ENTRIES = 10
    MAX_COMMAND_HISTORY = 50
    
    def __init__(self):
        self.state_file = Path.home() / ".terminus" / "state.json"
        self.state_file.parent.mkdir(exist_ok=True)
        self.data = StateData()
        self._load_state()
    
    def _load_state(self):
        """Load state from persistent storage."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
                    
                # Convert dict back to dataclass
                self.data.current_tag = raw_data.get('current_tag')
                self.data.command_history = raw_data.get('command_history', [])
                self.data.fuzzy_patterns = raw_data.get('fuzzy_patterns', {})
                
                # Rebuild context entries
                self.data.recent_context = [
                    ContextEntry(**entry) for entry in raw_data.get('recent_context', [])
                ]
                
                # Rebuild project states
                for tag, state_dict in raw_data.get('project_states', {}).items():
                    context_entries = [
                        ContextEntry(**entry) for entry in state_dict.get('context_entries', [])
                    ]
                    self.data.project_states[tag] = ProjectState(
                        tag=state_dict['tag'],
                        working_directory=state_dict['working_directory'],
                        created_at=state_dict['created_at'],
                        last_accessed=state_dict['last_accessed'],
                        context_entries=context_entries,
                        notes=state_dict.get('notes', '')
                    )
                    
                log.debug(f"Loaded state with {len(self.data.project_states)} projects")
            except Exception as e:
                log.error(f"Failed to load state: {e}")
                self.data = StateData()
    
    def _save_state(self):
        """Save state to persistent storage."""
        try:
            # Convert dataclass to dict for JSON serialization
            state_dict = {
                'current_tag': self.data.current_tag,
                'recent_context': [asdict(entry) for entry in self.data.recent_context],
                'project_states': {
                    tag: {
                        **asdict(state),
                        'context_entries': [asdict(entry) for entry in state.context_entries]
                    } 
                    for tag, state in self.data.project_states.items()
                },
                'command_history': self.data.command_history,
                'fuzzy_patterns': self.data.fuzzy_patterns
            }
            
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state_dict, f, indent=2, ensure_ascii=False)
            log.debug("State saved successfully")
        except Exception as e:
            log.error(f"Failed to save state: {e}")
    
    def add_context_entry(self, command: str, working_directory: str, success: bool, 
                         summary: Optional[str] = None):
        """Add a new context entry."""
        entry = ContextEntry(
            timestamp=datetime.now().isoformat(),
            command=command,
            working_directory=working_directory,
            success=success,
            summary=summary,
            tag=self.data.current_tag
        )
        
        # Add to recent context (limited size)
        self.data.recent_context.append(entry)
        if len(self.data.recent_context) > self.MAX_CONTEXT_ENTRIES:
            self.data.recent_context.pop(0)
        
        # Add to current project if tagged
        if self.data.current_tag and self.data.current_tag in self.data.project_states:
            project = self.data.project_states[self.data.current_tag]
            project.context_entries.append(entry)
            project.last_accessed = datetime.now().isoformat()
            if len(project.context_entries) > self.MAX_CONTEXT_ENTRIES:
                project.context_entries.pop(0)
        
        # Add to command history
        self.data.command_history.append(command)
        if len(self.data.command_history) > self.MAX_COMMAND_HISTORY:
            self.data.command_history.pop(0)
            
        self._save_state()
    
    def create_tag(self, tag: str, working_directory: str, notes: str = "") -> bool:
        """Create a new project tag."""
        if tag in self.data.project_states:
            return False
        
        self.data.project_states[tag] = ProjectState(
            tag=tag,
            working_directory=working_directory,
            created_at=datetime.now().isoformat(),
            last_accessed=datetime.now().isoformat(),
            notes=notes
        )
        self._save_state()
        return True
    
    def switch_to_tag(self, tag: str) -> Optional[ProjectState]:
        """Switch to a project tag."""
        if tag not in self.data.project_states:
            return None
            
        self.data.current_tag = tag
        project = self.data.project_states[tag]
        project.last_accessed = datetime.now().isoformat()
        self._save_state()
        return project
    
    def remove_tag(self, tag: str) -> bool:
        """Remove a project tag."""
        if tag not in self.data.project_states:
            return False
            
        if self.data.current_tag == tag:
            self.data.current_tag = None
            
        del self.data.project_states[tag]
        self._save_state()
        return True
    
    def get_recent_context(self) -> List[ContextEntry]:
        """Get recent context entries."""
        return self.data.recent_context.copy()
    
    def get_current_project(self) -> Optional[ProjectState]:
        """Get current project state if any."""
        if self.data.current_tag:
            return self.data.project_states.get(self.data.current_tag)
        return None
    
    def get_all_tags(self) -> List[str]:
        """Get all available project tags."""
        return list(self.data.project_states.keys())
    
    def add_fuzzy_pattern(self, pattern: str, tool_call: str):
        """Learn a new fuzzy pattern mapping."""
        self.data.fuzzy_patterns[pattern.lower()] = tool_call
        self._save_state()
    
    def find_fuzzy_match(self, user_input: str) -> Optional[str]:
        """Find a fuzzy match for user input."""
        user_lower = user_input.lower()
        
        # Exact match first
        if user_lower in self.data.fuzzy_patterns:
            return self.data.fuzzy_patterns[user_lower]
        
        # Partial matches
        for pattern, tool_call in self.data.fuzzy_patterns.items():
            if pattern in user_lower or user_lower in pattern:
                return tool_call
                
        return None
    
    def get_command_suggestions(self, partial_input: str) -> List[str]:
        """Get command suggestions based on history."""
        partial_lower = partial_input.lower()
        suggestions = []
        
        # Look through command history for matches
        for cmd in reversed(self.data.command_history):
            if partial_lower in cmd.lower() and cmd not in suggestions:
                suggestions.append(cmd)
                if len(suggestions) >= 5:
                    break
        
        return suggestions
    
    def get_stats(self) -> Dict[str, Any]:
        """Get state statistics."""
        return {
            'total_commands': len(self.data.command_history),
            'total_projects': len(self.data.project_states),
            'current_tag': self.data.current_tag,
            'recent_context_size': len(self.data.recent_context),
            'fuzzy_patterns': len(self.data.fuzzy_patterns),
            'state_file_size': self.state_file.stat().st_size if self.state_file.exists() else 0
        }

# Global state manager instance
state_manager = StateManager()

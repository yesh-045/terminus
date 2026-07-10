import logging
import re
from difflib import SequenceMatcher
from typing import List, Optional, Tuple

from .state_manager import state_manager

log = logging.getLogger(__name__)

class NaturalLanguageProcessor:
    """Processes natural language inputs and maps them to tool calls or suggestions."""
    
    def __init__(self):
        # Common patterns for natural language commands
        self.command_patterns = {
            # File operations
            r'\b(?:show|list|find|see)\s+.*(?:files?|\.py|\.js|\.ts|\.md|\.txt)': 'find_files',
            r'\b(?:show|list)\s+(?:all|the)?\s*(?:python|py)\s+files?': 'find *.py',
            r'\b(?:show|list)\s+(?:all|the)?\s*(?:javascript|js)\s+files?': 'find *.js',
            r'\b(?:show|list)\s+(?:all|the)?\s*(?:typescript|ts)\s+files?': 'find *.ts',
            r'\b(?:show|list)\s+(?:all|the)?\s*(?:markdown|md)\s+files?': 'find *.md',
            r'\b(?:list|show)\s+(?:the\s+)?(?:folders?|directories|files?)\s*(?:here|now)?(?:\s+in\s+(?:the\s+)?)?(?:current|this)?\s*(?:directory|folder)?\b': 'list_directory',
            r'\b(?:show|list)\s+.*(?:in|from)\s+(?:this|current)?\s*(?:directory|folder)': 'list_directory',
            r'\b(?:what\'?s|show)\s+(?:in|inside)?\s*(?:this|current)?\s*(?:directory|folder)': 'list_directory',
            r'\b(?:navigate to|go to|cd)\s+.+': 'change_directory',
            r'\bwhere\s+am\s+i\b': 'get_current_directory',
            r'\b(?:what(?:\'?s| is)\s+)?(?:my\s+)?current\s+(?:directory|folder|location)\b': 'get_current_directory',
            r'\bpwd\b': 'get_current_directory',
            
            # Search operations  
            r'\b(?:search|find|grep|look)\s+for\s+["\']?([^"\']+)["\']?': 'search_text',
            r'\b(?:find|search)\s+.*(?:todo|fixme|hack)': 'search_todos',
            r'\b(?:show|find|list)\s+.*(?:todo|fixme)s?': 'search_todos',
            
            # Git operations
            r'\b(?:git\s+)?status\b': 'git_status_enhanced',
            r'\b(?:git\s+)?(?:add|stage)\b': 'git_add',
            r'\b(?:git\s+)?commit\b': 'git_commit',
            r'\bwhat\s+changed\b': 'git_status_enhanced',
            r'\b(?:show|check)\s+git\s+status': 'git_status_enhanced',

            # Project analysis
            r'\b(?:analyze|examine|understand|explain)\s+(?:this\s+)?project': 'analyze_project_structure',
            r'\b(?:project|code)\s+(?:structure|overview|analysis)': 'analyze_project_structure',
            r'\b(?:summarize|explain)\s+(?:this\s+)?code': 'summarize_code',

            # System operations
            r'\b(?:system|machine)\s+(?:info|information)': 'system_info',
            r'\b(?:largest|biggest|large)\s+(?:folders?|directories)\b': 'quick_stats',
            r'\b(?:large|big)\s+files?': 'find_large_files',
            r'\b(?:clean|cleanup|remove)\s+.*(?:temp|temporary|cache)': 'clean_temp_files',
            r'\b(?:disk|storage)\s+(?:usage|space)': 'quick_stats',

            # Desktop automation (MUST match before generic clean patterns)
            r'\b(?:clean|organize|clear|tidy)\s+(?:my\s+)?downloads?(?:\s+folder)?\b': 'clean_downloads',
            r'\bdownloads?\s+(?:clean|organize|folder)\b': 'clean_downloads',
            r'\b(?:archive|zip)\s+(?:inactive|old|unused)\s+(?:projects?|folders?)\b': 'archive_inactive_projects',
            r'\b(?:find|remove|delete|clean)\s+(?:duplicate|dup)\s+screenshots?\b': 'remove_duplicate_screenshots',
            r'\bduplicate\s+screenshots?\b': 'remove_duplicate_screenshots',
            r'\b(?:list|show|find)\s+(?:running\s+)?(?:processes?|tasks?)\b': 'manage_processes',
            r'\b(?:kill|terminate|stop)\s+(?:process|pid|task)\b': 'manage_processes',

            # Help and documentation
            r'\b(?:help|commands|what\s+can\s+you\s+do)': 'quick_help',
            r'\b(?:available|all)\s+(?:commands|tools)': 'list_all_commands',
            r'\b(?:examples|how\s+to)': 'command_examples',
        }

        # Color-coded operation types
        self.operation_colors = {
            'safe': ['find', 'list', 'show', 'search', 'analyze', 'status', 'help'],
            'destructive': ['delete', 'remove', 'clean', 'commit', 'write', 'update'],
            'neutral': ['change', 'switch', 'move', 'copy', 'create']
        }
        
        # Initialize with some basic fuzzy patterns
        self._init_basic_patterns()
    
    def _init_basic_patterns(self):
        """Initialize basic fuzzy patterns."""
        basic_patterns = {
            'show me all python files': 'find *.py',
            'list python files': 'find *.py',
            'find py files': 'find *.py',
            'show javascript files': 'find *.js',
            'list js files': 'find *.js',
            'what files are here': 'list_directory',
            'show current directory': 'list_directory',
            'list directory contents': 'list_directory',
            'where am i': 'get_current_directory',
            'current directory': 'get_current_directory',
            'git status': 'git_status_enhanced',
            'show git status': 'git_status_enhanced',
        }
        
        # Initialize with some basic fuzzy patterns
        self._init_basic_patterns()
    
    def _init_basic_patterns(self):
        """Initialize basic fuzzy patterns."""
        basic_patterns = {
            'show me all python files': 'find *.py',
            'list python files': 'find *.py',
            'find py files': 'find *.py',
            'show javascript files': 'find *.js',
            'list js files': 'find *.js',
            'what files are here': 'list_directory',
            'show current directory': 'list_directory',
            'list directory contents': 'list_directory',
            'where am i': 'get_current_directory',
            'current directory': 'get_current_directory',
            'git status': 'git_status_enhanced',
            'show git status': 'git_status_enhanced',
            'what changed': 'git_status_enhanced',
            'analyze project': 'analyze_project_structure',
            'project structure': 'analyze_project_structure',
            'find todos': 'search_todos',
            'show todos': 'search_todos',
            'help': 'quick_help',
            'what commands': 'list_all_commands',
            # Desktop automation fuzzy matches
            'clean my downloads': 'clean_downloads',
            'clean downloads': 'clean_downloads',
            'clean downloads folder': 'clean_downloads',
            'organize downloads': 'clean_downloads',
            'organize my downloads': 'clean_downloads',
            'tidy downloads': 'clean_downloads',
            'clean up downloads': 'clean_downloads',
            'remove duplicate screenshots': 'remove_duplicate_screenshots',
            'find duplicate screenshots': 'remove_duplicate_screenshots',
            'delete duplicate screenshots': 'remove_duplicate_screenshots',
            'archive inactive projects': 'archive_inactive_projects',
            'archive old projects': 'archive_inactive_projects',
            'zip old projects': 'archive_inactive_projects',
            'list running processes': 'manage_processes',
            'show running processes': 'manage_processes',
            'show processes': 'manage_processes',
            'list processes': 'manage_processes',
        }
        
        for pattern, command in basic_patterns.items():
            state_manager.add_fuzzy_pattern(pattern, command)
    
    def process_input(self, user_input: str) -> Optional[Tuple[str, str, str]]:
        """
        Process natural language input and return (command, description, color).
        
        Returns:
            Tuple of (command_suggestion, description, color_category) or None
        """
        user_input_lower = user_input.lower().strip()
        
        # First, check for exact fuzzy matches
        fuzzy_match = state_manager.find_fuzzy_match(user_input_lower)
        if fuzzy_match:
            return fuzzy_match, "Using a close match", self._get_operation_color(fuzzy_match)
        
        # Then, check pattern matches
        for pattern, command in self.command_patterns.items():
            if re.search(pattern, user_input_lower):
                # Handle search patterns that extract search terms
                if 'search_text' in command:
                    match = re.search(r'\b(?:search|find|grep|look)\s+for\s+["\']?([^"\']+)["\']?', user_input_lower)
                    if match:
                        search_term = match.group(1)
                        actual_command = f"grep '{search_term}'"
                        return actual_command, f"Search for '{search_term}'", 'safe'
                
                return command, "Matched your request", self._get_operation_color(command)
        
        # Check for partial matches in command history only when the input
        # looks like an actionable command request. This avoids hijacking
        # normal conversation turns like "hello".
        if self._looks_like_command_request(user_input_lower):
            suggestions = state_manager.get_command_suggestions(user_input[:50])
            if suggestions:
                best_match = suggestions[0]
                similarity = SequenceMatcher(a=user_input_lower, b=best_match.lower()).ratio()
                if similarity >= 0.9:
                    return best_match, "Using a similar command", self._get_operation_color(best_match)
        
        return None

    def _looks_like_command_request(self, text: str) -> bool:
        """Heuristic: decide if input is likely an actionable command request."""
        if not text or len(text.strip()) < 4:
            return False

        action_keywords = (
            "show", "list", "find", "search", "grep", "read", "open",
            "current", "directory", "folder", "file", "files",
            "navigate", "go to", "cd", "change", "switch",
            "git", "status", "analyze", "help", "command",
        )
        return any(keyword in text for keyword in action_keywords)
    
    def _get_operation_color(self, command: str) -> str:
        """Determine the color category for an operation."""
        command_lower = command.lower()
        
        for color, keywords in self.operation_colors.items():
            if any(keyword in command_lower for keyword in keywords):
                return color
        
        return 'neutral'
    
    def get_suggestions_for_partial(self, partial_input: str) -> List[str]:
        """Get suggestions for partial input."""
        suggestions = []
        partial_lower = partial_input.lower()
        
        # Pattern-based suggestions
        for pattern, command in self.command_patterns.items():
            # Extract readable part from regex pattern for suggestion
            readable_pattern = self._make_pattern_readable(pattern)
            if partial_lower in readable_pattern.lower():
                suggestions.append(f"{readable_pattern} → {command}")
        
        # History-based suggestions
        history_suggestions = state_manager.get_command_suggestions(partial_input)
        suggestions.extend(history_suggestions[:3])
        
        return suggestions[:5]  # Limit to top 5 suggestions
    
    def _make_pattern_readable(self, regex_pattern: str) -> str:
        """Convert a regex pattern to a readable suggestion."""
        # Simplified conversion - just extract key words
        pattern = regex_pattern.replace('\\b', '').replace('.*', '...')
        pattern = re.sub(r'\["\'\]?\([^)]+\)\["\'\]?', '"text"', pattern)
        pattern = re.sub(r'\?.*?:', '', pattern)
        pattern = re.sub(r'[\[\](){}*+?|^$]', '', pattern)
        return ' '.join(pattern.split())
    
    def learn_from_successful_command(self, user_input: str, successful_command: str):
        """Learn from a successful command execution."""
        user_input_clean = user_input.lower().strip()
        
        # Don't learn from commands that are already slash commands or very short
        if len(user_input_clean) < 10 or user_input_clean.startswith('/'):
            return
        
        # Add to fuzzy patterns for future matching
        state_manager.add_fuzzy_pattern(user_input_clean, successful_command)
        log.debug(f"Learned pattern: '{user_input_clean}' → '{successful_command}'")
    
    def suggest_natural_language_alternatives(self, failed_command: str) -> List[str]:
        """Suggest natural language alternatives for a failed command."""
        suggestions = []
        
        # Common command translations
        translations = {
            'ls': 'show files in current directory',
            'pwd': 'where am i',
            'find . -name "*.py"': 'show me all python files',
            'git status': 'what changed',
            'grep': 'search for text in files',
            'cat': 'show file contents',
            'mkdir': 'create directory',
            'rm': 'delete file',
        }
        
        # Check if the failed command has a natural language alternative
        failed_lower = failed_command.lower().strip()
        for cmd, natural in translations.items():
            if cmd in failed_lower:
                suggestions.append(f"Try: '{natural}'")
        
        # General suggestions
        suggestions.extend([
            "Use natural language like 'show me all python files'",
            "Try '/help' to see available commands",
            "Ask 'what can you do' for capabilities"
        ])
        
        return suggestions[:3]

# Global instance
nl_processor = NaturalLanguageProcessor()

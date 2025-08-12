from pydantic_ai import Tool

# Filesystem tools
from terminus.tools.filesystem.find import find
from terminus.tools.filesystem.grep import grep
from terminus.tools.filesystem.list import list_directory
from terminus.tools.filesystem.read_file import read_file
from terminus.tools.filesystem.update_file import update_file
from terminus.tools.filesystem.write_file import write_file
from terminus.tools.filesystem.directory import change_directory, get_current_directory, run_in_directory
from terminus.tools.filesystem.file_discovery import find_by_extension, list_extensions

# Development tools  
from terminus.tools.development.code_analysis import summarize_code, analyze_project_structure
from terminus.tools.development.dev_workflow import (
    package_info,
    search_todos,
)
from terminus.tools.development.project_automation import generate_project_readme, analyze_code_for_refactoring

# System tools
from terminus.tools.system.run_command import run_command
from terminus.tools.system.system_utilities import (
    system_info,
    quick_stats,
    create_project_template,
    find_large_files,
    clean_temp_files,
)

# Help tools
from terminus.tools.help.help_system import (
    list_all_commands,
    command_examples,
    quick_help,
)

# Integration tools
from terminus.tools.integrations.gmail import list_unread, summary, generate_draft, search_email
from terminus.tools.integrations.calendar import add_event, check_availability, block_focus
from terminus.tools.integrations.google_setup import google_auth_status, google_auth_setup, google_auth_revoke


def create_tools():
    """Create Tool instances for all tools."""
    return [
        Tool(read_file),
        Tool(write_file),
        Tool(update_file),
        Tool(run_command),
        Tool(find),
        Tool(grep),
        Tool(list_directory),
        # New session-aware tools
        Tool(change_directory),
        Tool(get_current_directory),
        Tool(run_in_directory),
        Tool(find_by_extension),
        Tool(list_extensions),
        Tool(summarize_code),
        Tool(analyze_project_structure),
        # System utilities
        Tool(system_info),
        Tool(quick_stats),
        Tool(create_project_template),
        Tool(find_large_files),
        Tool(clean_temp_files),
        # Development workflow
        Tool(package_info),
        Tool(search_todos),
        # Help and documentation
        Tool(list_all_commands),
        Tool(command_examples),
        Tool(quick_help),
        # Gmail tools
        Tool(list_unread),
        Tool(summary),
        Tool(generate_draft),
        Tool(search_email),
        # Calendar tools
        Tool(add_event),
        Tool(check_availability),
        Tool(block_focus),
        # Google API setup tools
        Tool(google_auth_status),
        Tool(google_auth_setup),
        Tool(google_auth_revoke),
        # Project automation tools
        Tool(generate_project_readme),
        Tool(analyze_code_for_refactoring),
    ]

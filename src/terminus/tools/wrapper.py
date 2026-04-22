from pydantic_ai import Tool

# Import file operation tools
from terminus.tools.file_ops import (
    read_file,
    write_file,
    update_file,
    find,
    grep,
    list_directory,
    change_directory,
    get_current_directory,
    run_in_directory,
    find_by_extension,
    list_extensions,
)

# Import development tools
from terminus.tools.dev_tools import (
    git_add,
    git_commit,
    git_status_enhanced,
    package_info,
    quick_commit,
    search_todos,
    generate_project_readme,
    analyze_code_for_refactoring,
    run_command,
    system_info,
    quick_stats,
    create_project_template,
    find_large_files,
    clean_temp_files,
    list_all_commands,
    command_examples,
    quick_help,
)

# Import analysis tools
from terminus.tools.analysis import (
    summarize_code,
    analyze_project_structure,
    suggest_refactor,
    review_code,
    find_complex_functions,
    find_code_duplicates,
)

# Import integration tools
from terminus.tools.integrations import (
    list_unread,
    summary,
    generate_draft,
    search_email,
    add_event,
    check_availability,
    block_focus,
    google_auth_status,
    google_auth_setup,
    google_auth_revoke,
)


def create_tools():
    """Create Tool instances for all tools."""
    return [
        Tool(read_file),
        Tool(write_file),
        Tool(update_file),
        Tool(run_command),
        Tool(git_add),
        Tool(git_commit),
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
        Tool(git_status_enhanced),
        Tool(package_info),
        Tool(quick_commit),
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
        # Code review tools
        Tool(suggest_refactor),
        Tool(review_code),
        Tool(find_complex_functions),
        Tool(find_code_duplicates),
    ]

"""Status message functions."""

from rich.console import Console
from rich.padding import Padding
from rich.pretty import Pretty
from rich.table import Table
from rich.text import Text

from terminus.constants import APP_NAME, APP_VERSION
from terminus.core.session import session
from terminus.ui import panels
from terminus.ui.colors import colors

console = Console()


def info(message: str):
    """Display an info message."""
    panels._prepare_to_print("status")
    console.print(f"• {message}", style=colors.primary)
    panels._last_output = "status"


def thinking(message: str):
    """Display an agent thinking message with proper indentation for multi-line content."""
    panels._prepare_to_print("status")
    lines = message.strip().split("\n")
    if lines:
        console.print(f"› {lines[0]}", style=colors.muted)
        for line in lines[1:]:
            console.print(f"  {line}", style=colors.muted)
    panels._last_output = "status"


def error(message: str, detail: str = None):
    """Display an error message."""
    panels._prepare_to_print("status")
    if detail:
        console.print(f"✗ {message}: {detail}", style=colors.error)
    else:
        console.print(f"✗ {message}", style=colors.error)
    panels._last_output = "status"


def warning(message: str):
    """Display a warning message."""
    panels._prepare_to_print("status")
    console.print(f"⚠ {message}", style=colors.warning)
    panels._last_output = "status"


def success(message: str):
    """Display a success message."""
    panels._prepare_to_print("status")
    console.print(f"✓ {message}", style=colors.success)
    panels._last_output = "status"


def bullet(message: str):
    """Display a bullet point message."""
    panels._prepare_to_print("status")
    console.print(f"  - {message}", style=colors.muted)
    panels._last_output = "status"


def muted(message: str, spaces: int = 0):
    """Display a muted message."""
    panels._prepare_to_print("status")
    console.print(f"{' ' * spaces}{message}", style=colors.muted)
    panels._last_output = "status"


def agent(content: str, has_footer: bool = False):
    """Display agent response."""
    # Just use the display_agent_panel function from panels
    panels.display_agent_panel(content, has_footer)


def line():
    """Print a blank line."""
    console.print()


def dump(data):
    """Display data in a pretty format."""
    console.print(Pretty(data))


def help():
    """Display comprehensive help information."""
    # Create main help table
    help_table = Table(show_header=False, box=None, padding=(0, 2, 0, 0))
    help_table.add_column("Command", style=colors.primary, no_wrap=True)
    help_table.add_column("Description", style="white")

    # Slash commands section
    slash_commands = [
        ("/help", "Show this comprehensive help guide"),
        ("/yolo", "Toggle tool confirmation prompts (DANGEROUS: auto-approves all actions)"),
        ("/clear", "Clear conversation history and start fresh"),
        ("/dump", "Show detailed message history for debugging"),
        ("exit", "Exit the application gracefully"),
    ]

    for cmd, desc in slash_commands:
        help_table.add_row(cmd, desc)
    
    # AI Tools section header
    help_table.add_row("", "")  # Spacer
    help_table.add_row(Text("AI-POWERED TOOLS", style=f"bold {colors.accent}"), 
                       Text("Ask the AI to use these tools naturally:", style=colors.muted))
    help_table.add_row("", "")  # Spacer
    
    # Key AI tool categories with examples
    ai_examples = [
        ("File Operations", '"read the config file" → Uses read_file, write_file, update_file'),
        ("Search & Analysis", '"find all TODO comments" → Uses search_todos, grep, find_by_extension'),
        ("Git Workflow", '"show git status" → Uses git_status_enhanced, quick_commit'),
        ("Code Intelligence", '"analyze this project" → Uses summarize_code, analyze_project_structure'),
        ("System Utilities", '"clean up temp files" → Uses clean_temp_files, find_large_files'),
        ("Get More Help", '"show all commands" → Uses list_all_commands, command_examples'),
    ]
    
    for category, example in ai_examples:
        help_table.add_row(Text(category, style=colors.success), 
                          Text(example, style=colors.muted))
    
    # Enhanced footer with tips
    help_table.add_row("", "")  # Spacer
    help_table.add_row(Text("PRO TIPS", style=f"bold {colors.info}"), "")
    help_table.add_row("", Text('• Ask: "what tools are available?" for complete command list', style=colors.muted))
    help_table.add_row("", Text('• Ask: "show examples for git workflow" for practical usage', style=colors.muted))
    help_table.add_row("", Text('• Ask: "help with file operations" for specific guidance', style=colors.muted))
    help_table.add_row("", Text('• Use /yolo to skip confirmations (careful!)', style=colors.muted))
    help_table.add_row("", Text(f'• Total tools available: 34+ commands', style=f"bold {colors.accent}"))

    panels.display_info_panel(help_table, "Terminus CLI - Complete Help Guide")


def version():
    """Display version information."""
    console.print(f"{APP_NAME} v{APP_VERSION}", style=colors.muted)


def update_available(latest_version: str):
    """Display update available message."""
    muted(f"Update available: {APP_VERSION} → {latest_version}")


def usage():
    """Display usage information."""
    console.print(f"Usage: {APP_NAME} [OPTIONS]", style=colors.primary)
    console.print("Run the CLI to start an interactive session.", style=colors.muted)


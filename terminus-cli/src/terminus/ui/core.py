"""Core UI functions including banner and spinner management."""

import asyncio
import random

from rich.console import Console
from rich.padding import Padding

from terminus.constants import APP_VERSION
from terminus.core.session import session
from terminus.ui.colors import colors

console = Console()

BANNER = """
████████╗███████╗██████╗ ███╗   ███╗██╗███╗   ██╗██╗   ██╗███████╗
╚══██╔══╝██╔════╝██╔══██╗████╗ ████║██║████╗  ██║██║   ██║██╔════╝
   ██║   █████╗  ██████╔╝██╔████╔██║██║██╔██╗ ██║██║   ██║███████╗
   ██║   ██╔══╝  ██╔══██╗██║╚██╔╝██║██║██║╚██╗██║██║   ██║╚════██║
   ██║   ███████╗██║  ██║██║ ╚═╝ ██║██║██║ ╚████║╚██████╔╝███████║
   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝"""

THINKING_MESSAGES = [
"Compiling situational logic...",

"Cross-referencing session memory...",

"Interpolating command structure...",

"Distilling semantic core...",

"Assembling deterministic route...",

"Indexing execution context...",

"Resolving latent conditions...",

"Reducing ambiguity space...",

"Synthesizing intent vectors...",

"Mapping command topology...",

"Modeling procedural outcome...",

"Validating scope constraints...",

"Reconstructing directive chain...",

"Identifying operative primitives...",

"Initiating zero-state resolve...",

"Projecting response envelope...",

"Caching transient states...",

"Detecting input variance...",

"Stabilizing interface flux...",

"Decrypting execution symbolics..."
]


# Style definitions with modern color palette
class SpinnerStyle:
    DEFAULT = f"[bold {colors.primary}]{{}}[/bold {colors.primary}]"
    MUTED = f"[{colors.muted}]{{}}[/{colors.muted}]"
    WARNING = f"[{colors.warning}]{{}}[/{colors.warning}]"
    ERROR = f"[{colors.error}]{{}}[/{colors.error}]"
    SUCCESS = f"[{colors.success}]{{}}[/{colors.success}]"
    INFO = f"[{colors.info}]{{}}[/{colors.info}]"
    PROCESSING = f"[{colors.processing}]{{}}[/{colors.processing}]"
    HIGHLIGHT = f"[{colors.highlight}]{{}}[/{colors.highlight}]"


def get_thinking_message() -> str:
    """Get a random thinking message."""
    return random.choice(THINKING_MESSAGES)


async def _rotate_thinking_messages(style: str, interval: float = 5.0):
    """Rotate thinking messages at specified interval."""
    while True:
        try:
            await asyncio.sleep(interval)
            if session.spinner:
                message = get_thinking_message()
                formatted_message = style.format(message)
                session.spinner.update(formatted_message)
        except asyncio.CancelledError:
            break
        except Exception:
            break


def banner():
    """Display the enhanced application banner with modern styling."""
    from terminus.ui import panels

    console.clear()
    
    # Solid banner with primary color, no gradients
    banner_lines = BANNER.split('\n')
    for line in banner_lines:
        banner_padding = Padding(line, (0, 0, 0, 2))
        console.print(banner_padding, style=colors.primary)
    
    # Enhanced version display
    version_line = f"v{APP_VERSION} - Agentic CLI"
    version_padding = Padding(version_line, (1, 0, 1, 2))
    console.print(version_padding, style=colors.accent)
    
    panels._last_output = None  # Reset context after banner


def start_spinner(message: str = "", style: str = SpinnerStyle.DEFAULT):
    """Start the spinner with a message."""
    if message == "":
        message = get_thinking_message()
    formatted_message = style.format(message)
    session.spinner = console.status(formatted_message, spinner="dots")
    session.spinner.start()

    # Start rotation task
    if session.spinner_rotation_task:
        session.spinner_rotation_task.cancel()
    session.spinner_rotation_task = asyncio.create_task(_rotate_thinking_messages(style))


def stop_spinner():
    """Stop the spinner."""
    if session.spinner:
        session.spinner.stop()
        session.spinner = None

    if session.spinner_rotation_task:
        session.spinner_rotation_task.cancel()
        session.spinner_rotation_task = None

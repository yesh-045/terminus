"""Command handlers for terminus CLI slash commands."""

import asyncio
import logging
import os
import platform
import sys
from datetime import datetime
from pathlib import Path

from terminus import ui
from terminus.session import session

log = logging.getLogger(__name__)


async def handle_dump():
    """Handle /dump command - show message history."""
    ui.dump(session.messages)


async def handle_history():
    """Handle /history command - show conversation history."""
    if not session.messages:
        ui.info("No conversation history")
        return
    
    # Filter to only show actual user questions (not system prompts)
    user_questions = []
    for msg in session.messages:
        # Handle ModelRequest objects
        if hasattr(msg, 'parts'):
            for part in msg.parts:
                if hasattr(part, 'content') and hasattr(part, '__class__'):
                    content = part.content
                    part_type = part.__class__.__name__
                    
                    # Only include UserPromptPart that are genuine user queries
                    if 'User' in part_type:
                        # Filter out system prompts by checking for system-like content
                        system_indicators = [
                            "you are **terminus**",
                            "understanding user intent",
                            "action requests",
                            "lightweight cli assistant",
                            "built-in tools",
                            "response style",
                            len(content) > 500  # System prompts are typically very long
                        ]
                        
                        # If any system indicator is found, skip this message
                        is_system = any(
                            indicator if isinstance(indicator, bool) 
                            else indicator.lower() in content.lower()
                            for indicator in system_indicators
                        )
                        
                        if not is_system and content.strip():
                            user_questions.append(content.strip())
    
    if not user_questions:
        ui.info("No user questions in history")
        return
    
    ui.info(f"User Questions ({len(user_questions)})")
    for i, question in enumerate(user_questions, 1):
        # Show first 150 characters of content for better readability
        preview = question[:150] + "..." if len(question) > 150 else question
        ui.bullet(f"{i}. {preview}")


async def handle_yolo():
    """Handle /yolo command - toggle confirmation mode."""
    session.confirmation_enabled = not session.confirmation_enabled

    # Clear disabled confirmations when toggling
    if session.confirmation_enabled:
        session.disabled_confirmations.clear()

    status = "disabled (YOLO mode)" if not session.confirmation_enabled else "enabled"
    ui.info(f"Tool confirmations {status}")


async def handle_clear():
    """Handle /clear command - clear conversation history and screen."""
    # Clear the conversation history
    session.messages.clear()

    # Clear the screen and redisplay the banner
    ui.banner()

    # Show success message
    ui.success("Conversation history cleared")


async def handle_status():
    """Handle /status command - show system status."""
    ui.info("System Status")
    ui.bullet(f"Model: {session.current_model}")
    ui.bullet(f"Messages in history: {len(session.messages)}")
    ui.bullet(f"Confirmations: {'disabled (YOLO mode)' if not session.confirmation_enabled else 'enabled'}")
    ui.bullet(f"Debug mode: {'enabled' if session.debug_enabled else 'disabled'}")
    ui.bullet(f"Platform: {platform.system()} {platform.release()}")
    ui.bullet(f"Python: {sys.version.split()[0]}")
    ui.bullet(f"Working directory: {os.getcwd()}")


async def handle_version():
    """Handle /version command - show version info."""
    from terminus.constants import APP_NAME, APP_VERSION
    ui.info(f"{APP_NAME} version {APP_VERSION}")
    ui.bullet(f"Python: {sys.version.split()[0]}")
    ui.bullet(f"Platform: {platform.system()} {platform.release()}")


async def handle_pwd():
    """Handle /pwd command - show current directory."""
    current_dir = os.getcwd()
    ui.info(f"Current directory: {current_dir}")


async def handle_ls(args: list[str]):
    """Handle /ls command - list directory contents."""
    path = args[0] if args else "."
    try:
        path_obj = Path(path).resolve()
        if not path_obj.exists():
            ui.warning(f"Path does not exist: {path}")
            return
        
        if path_obj.is_file():
            ui.info(f"File: {path_obj}")
            stat = path_obj.stat()
            ui.bullet(f"Size: {stat.st_size} bytes")
            ui.bullet(f"Modified: {datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
            return
        
        ui.info(f"Contents of: {path_obj}")
        items = list(path_obj.iterdir())
        if not items:
            ui.bullet("(empty directory)")
            return
        
        # Sort: directories first, then files
        items.sort(key=lambda x: (x.is_file(), x.name.lower()))
        
        for item in items:
            if item.is_dir():
                ui.bullet(f"{item.name}/")
            else:
                size = item.stat().st_size
                if size > 1024 * 1024:
                    size_str = f"{size / (1024*1024):.1f}MB"
                elif size > 1024:
                    size_str = f"{size / 1024:.1f}KB"
                else:
                    size_str = f"{size}B"
                ui.bullet(f"{item.name} ({size_str})")
                
    except Exception as e:
        ui.error("Directory listing failed", str(e))


async def handle_cd(args: list[str]):
    """Handle /cd command - change directory."""
    if not args:
        # Go to home directory
        target = Path.home()
    else:
        target = Path(args[0]).resolve()
    
    try:
        if not target.exists():
            ui.warning(f"Directory does not exist: {target}")
            return
        
        if not target.is_dir():
            ui.warning(f"Not a directory: {target}")
            return
        
        os.chdir(target)
        ui.success(f"Changed directory to: {target}")
        
    except Exception as e:
        ui.error("Failed to change directory", str(e))


async def handle_model(args: list[str]):
    """Handle /model command - show or change current model."""
    if not args:
        ui.info(f"Current model: {session.current_model}")
        ui.bullet("Available models:")
        ui.bullet("• gpt-4o")
        ui.bullet("• gpt-4")
        ui.bullet("• claude-3-5-sonnet-20241022") 
        ui.bullet("• claude-3-5-haiku-20241022")
        ui.bullet("Use '/model <model_name>' to switch")
        return
    
    new_model = args[0]
    old_model = session.current_model
    session.current_model = new_model
    ui.success(f"Switched model from {old_model} to {new_model}")


async def handle_time():
    """Handle /time command - show current time."""
    now = datetime.now()
    ui.info(f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    ui.bullet(f"Timezone: {now.astimezone().tzname()}")
    ui.bullet(f"Unix timestamp: {int(now.timestamp())}")


async def handle_help():
    """Handle /help command - show available commands."""
    ui.info("Available Commands")
    ui.bullet("/help - Show this help message")
    ui.bullet("/status - Show system status")
    ui.bullet("/version - Show version information")
    ui.bullet("/history - Show conversation history")
    ui.bullet("/clear - Clear conversation history")
    ui.bullet("/dump - Show conversation history")
    ui.bullet("/yolo - Toggle confirmation mode")


async def handle_debug_test(args: list[str]):
    """Handle /test command - trigger various UI states for testing (debug mode only)."""
    if not args:
        ui.info("Available test triggers:")
        ui.bullet("error - Trigger an error panel")
        ui.bullet("warning - Show a warning message")
        ui.bullet("success - Show a success message")
        ui.bullet("spinner - Test spinner behavior")
        ui.bullet("panel - Show various panel types")
        ui.bullet("confirm - Show confirmation dialog")
        return

    test_type = args[0].lower()

    if test_type == "error":
        try:
            raise ValueError("This is a test error to demonstrate error handling")
        except Exception as e:
            from terminus.utils.error import handle_error
            await handle_error(e, ui.display_error_panel)

    elif test_type == "warning":
        ui.warning("This is a test warning message")

    elif test_type == "success":
        ui.success("This is a test success message!")

    elif test_type == "spinner":
        ui.start_spinner("Testing spinner...", ui.SpinnerStyle.DEFAULT)
        await asyncio.sleep(2)
        ui.stop_spinner()
        ui.info("Spinner test completed")

    elif test_type == "panel":
        ui.display_info_panel("This is an info panel", "Information")
        ui.line()
        ui.display_tool_panel("Tool output goes here", "Test Tool", "Footer text")
        ui.line()
        ui.display_confirmation_panel("Are you sure you want to proceed?")

    elif test_type == "confirm":
        from terminus.agent import _create_confirmation_callback
        confirm = _create_confirmation_callback()
        result = await confirm(
            "Test Action: Delete File", "This would delete important.txt", "File: important.txt"
        )
        ui.info(f"Confirmation result: {result}")

    else:
        ui.warning(f"Unknown test type: {test_type}")


async def handle_command(user_input: str) -> bool:
    """Handle slash commands. Returns True if command was handled."""
    if not user_input.startswith("/"):
        return False

    parts = user_input.split()
    command = parts[0]
    args = parts[1:] if len(parts) > 1 else []

    handlers = {
        "/dump": handle_dump,
        "/history": handle_history,
        "/yolo": handle_yolo,
        "/clear": handle_clear,
        "/help": handle_help,
        "/status": handle_status,
        "/version": handle_version,
    }

    if session.debug_enabled:
        handlers["/test"] = lambda: handle_debug_test(args)

    handler = handlers.get(command)
    if handler:
        await handler()
        return True

    # If command not found, show helpful message
    ui.warning(f"Unknown command: {command}")
    ui.bullet("Type /help to see available commands")
    return True

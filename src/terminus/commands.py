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
from terminus.models import model_manager
from terminus.persistence import persistence

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


async def handle_models():
    """Handle /models command - show available AI models."""
    await model_manager.initialize()
    models = model_manager.list_models()
    current = model_manager.get_current_model()
    
    if not models:
        ui.warning("No AI models available")
        return
        
    ui.info("Available AI Models")
    
    for model in models:
        status = "✓" if model.available else "✗"
        local_badge = " [LOCAL]" if model.local else " [API]"
        current_badge = " [CURRENT]" if current and model.name == current.name else ""
        
        ui.bullet(f"{status} {model.display_name}{local_badge}{current_badge}")
        
    if current:
        ui.info(f"Current model: {current.display_name}")


async def handle_switch_model(args: list[str]):
    """Handle /switch command - switch AI model."""
    if not args:
        ui.warning("Usage: /switch <model_name>")
        ui.info("Use /models to see available models")
        return
        
    model_name = args[0]
    
    # Allow partial matching
    await model_manager.initialize()
    models = model_manager.list_models()
    
    # Find exact match first
    exact_match = next((m for m in models if m.name == model_name), None)
    if exact_match:
        success = await model_manager.switch_model(exact_match.name)
        if success:
            # Double-check synchronization
            ui.info(f"Session model: {session.current_model}")
            ui.info(f"Manager model: {model_manager.current_model}")
        return
        
    # Find partial matches
    partial_matches = [m for m in models if model_name.lower() in m.name.lower() or model_name.lower() in m.display_name.lower()]
    
    if len(partial_matches) == 1:
        success = await model_manager.switch_model(partial_matches[0].name)
        if success:
            # Double-check synchronization
            ui.info(f"Session model: {session.current_model}")
            ui.info(f"Manager model: {model_manager.current_model}")
    elif len(partial_matches) > 1:
        ui.warning(f"Multiple models match '{model_name}':")
        for model in partial_matches:
            ui.bullet(f"{model.name} ({model.display_name})")
    else:
        ui.error(f"No model found matching '{model_name}'")
        ui.info("Use /models to see available models")


async def handle_offline():
    """Handle /offline command - switch to offline mode."""
    await model_manager.initialize()
    success = await model_manager.auto_fallback()
    
    if success:
        ui.success("Switched to offline mode with local models")
    else:
        ui.warning("No local models available for offline mode")
        ui.info("Install Ollama and pull models to enable offline mode")


async def handle_sessions(args: list[str] = None):
    """Handle /sessions command - list saved sessions or clear with --clear flag."""
    args = args or []
    
    # Handle --clear flag
    if "--clear" in args:
        try:
            cleared_count = persistence.clear_all_sessions()
            if cleared_count > 0:
                ui.success(f"Cleared {cleared_count} saved sessions")
            else:
                ui.info("No sessions to clear")
        except Exception as e:
            ui.error(f"Failed to clear sessions: {e}")
        return
    
    # Default behavior - list sessions
    sessions = persistence.list_sessions()
    
    if not sessions:
        ui.info("No saved sessions")
        return
        
    ui.info(f"Saved Sessions ({len(sessions)})")
    
    for i, session_data in enumerate(sessions, 1):
        timestamp = session_data.get("timestamp", "Unknown")
        name = session_data.get("session_name", "Unnamed")
        model = session_data.get("model", "Unknown")
        msg_count = session_data.get("message_count", 0)
        
        # Format timestamp
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(timestamp)
            time_str = dt.strftime("%Y-%m-%d %H:%M")
        except:
            time_str = timestamp
            
        ui.bullet(f"{i}. {name} - {time_str} ({msg_count} messages, {model})")
    
    ui.info("Use '/sessions --clear' to clear all sessions")


async def handle_save_session(args: list[str]):
    """Handle /save command - save current session."""
    session_name = args[0] if args else None
    
    try:
        saved_name = persistence.save_session(session_name)
        ui.success(f"Session saved as: {saved_name}")
    except Exception as e:
        ui.error(f"Failed to save session: {e}")


async def handle_load_session(args: list[str]):
    """Handle /load command - load saved session."""
    if not args:
        ui.warning("Usage: /load <session_name>")
        ui.info("Use /sessions to see available sessions")
        return
        
    session_name = args[0]
    
    try:
        success = persistence.load_session(session_name)
        if success:
            ui.success(f"Loaded session: {session_name}")
        else:
            ui.error(f"Session not found: {session_name}")
    except Exception as e:
        ui.error(f"Failed to load session: {e}")


async def handle_cleanup_sessions():
    """Handle /cleanup command - clean up unnecessary sessions."""
    try:
        deleted_count = persistence.cleanup_sessions()
        if deleted_count > 0:
            ui.success(f"Cleaned up {deleted_count} unnecessary sessions")
        else:
            ui.info("No sessions to clean up")
    except Exception as e:
        ui.error(f"Failed to cleanup sessions: {e}")


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
    ui.bullet(f"Session Model: {session.current_model}")
    
    # Check model manager state
    current_model_info = model_manager.get_current_model()
    if current_model_info:
        ui.bullet(f"Model Manager: {current_model_info.display_name}")
        ui.bullet(f"Model Manager Current: {model_manager.current_model}")
    else:
        ui.bullet("Model Manager: Not initialized")
        
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
    ui.bullet("/models - List available AI models")
    ui.bullet("/switch <model> - Switch AI model")
    ui.bullet("/offline - Switch to offline mode")
    ui.bullet("/sessions [--clear] - List saved sessions or clear all")
    ui.bullet("/save [name] - Save current session")
    ui.bullet("/load <name> - Load saved session")
    ui.bullet("/cleanup - Clean up unnecessary sessions")
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
        "/models": handle_models,
        "/switch": lambda: handle_switch_model(args),
        "/offline": handle_offline,
        "/sessions": lambda: handle_sessions(args),
        "/save": lambda: handle_save_session(args),
        "/load": lambda: handle_load_session(args),
        "/cleanup": handle_cleanup_sessions,
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

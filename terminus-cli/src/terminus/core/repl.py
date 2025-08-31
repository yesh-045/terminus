import asyncio
import logging
import signal

from terminus import ui
from .agent import get_or_create_agent, process_request
from .commands import handle_command
from .session import session
from ..infrastructure.state_manager import state_manager
from ..utils.error import ErrorContext
from ..utils.input import create_multiline_prompt_session, get_multiline_input
from ..infrastructure.models import model_manager
from ..infrastructure.persistence import persistence

log = logging.getLogger(__name__)


def _setup_signal_handler(loop):
    """Set up SIGINT handler for graceful cancellation."""

    def signal_handler(signum, frame):
        session.sigint_received = True
        if session.current_task and not session.current_task.done():
            loop.call_soon_threadsafe(session.current_task.cancel)
        else:
            raise KeyboardInterrupt()

    signal.signal(signal.SIGINT, signal_handler)
    return signal_handler


def _restore_default_signal_handler():
    """Restore the default SIGINT handler."""
    signal.signal(signal.SIGINT, signal.default_int_handler)


def _should_exit(user_input: str) -> bool:
    """Check if user wants to exit."""
    return user_input.lower() in ["exit", "quit"]


class Repl:
    """Manages the application's Read-Eval-Print Loop and session state."""

    def __init__(self):
        """Initializes the REPL manager with an agent and signal handler."""
        self.loop = asyncio.get_event_loop()
        self.signal_handler = _setup_signal_handler(self.loop)

    async def _handle_user_request(self, user_input: str):
        """Process a user request with proper exception handling."""
        log.debug(f"Handling user request: {user_input.replace('\n', ' ')[:100]}...")
        
        # Enhanced spinner with more dynamic messages
        thinking_messages = [
            "Thinking...",
            "Analyzing request...",
            "Processing...",
            "Working on it..."
        ]
        ui.start_spinner(ui.get_thinking_message())
        session.sigint_received = False

        request_task = asyncio.create_task(process_request(user_input))
        session.current_task = request_task

        ctx = ErrorContext("request", ui)
        success = False
        response_summary = None

        try:
            resp = await request_task
            ui.stop_spinner()
            if resp:
                ui.agent(resp)
                success = True
                # Create a brief summary of the response for context
                response_summary = resp[:100] + "..." if len(resp) > 100 else resp
                
        except asyncio.CancelledError as e:
            ui.stop_spinner()
            await ctx.handle(e)
            response_summary = "Request cancelled"
            
        except KeyboardInterrupt:
            ui.stop_spinner()
            if not request_task.done():
                request_task.cancel()
                try:
                    await request_task
                except asyncio.CancelledError:
                    pass
            ui.warning("Request interrupted")
            response_summary = "Request interrupted"
            
        except Exception as e:
            ui.stop_spinner()
            await ctx.handle(e)
            response_summary = f"Error: {str(e)[:50]}..."
            
            # Add command suggestions after errors
            self._suggest_commands_after_error(user_input, e)
            
        finally:
            session.current_task = None
            
            # Add context entry to state manager
            try:
                state_manager.add_context_entry(
                    command=user_input,
                    working_directory=session.get_cwd(),
                    success=success,
                    summary=response_summary
                )
            except Exception as e:
                log.debug(f"Failed to add context entry: {e}")
    
    def _suggest_commands_after_error(self, user_input: str, error: Exception):
        """Suggest helpful commands after an error occurs."""
        error_str = str(error).lower()
        suggestions = []
        
        if "file not found" in error_str or "no such file" in error_str:
            suggestions.append("/help - See available commands")
            suggestions.append("Try: 'list files in current directory'")
            
        elif "permission denied" in error_str:
            suggestions.append("Check file permissions")
            suggestions.append("/config - Check configuration")
            
        elif "api" in error_str or "key" in error_str:
            suggestions.append("/config key <your_key> - Update API key")
            suggestions.append("/models - Check available models")
            
        elif "model" in error_str or "gemini" in error_str:
            suggestions.append("/models - List available models")
            suggestions.append("/offline - Switch to local models")
        
        # Fuzzy matching suggestions based on user input
        fuzzy_suggestions = state_manager.get_command_suggestions(user_input[:50])
        if fuzzy_suggestions:
            suggestions.extend([f"Similar: {cmd[:60]}..." for cmd in fuzzy_suggestions[:2]])
        
        if suggestions:
            ui.line()
            ui.info("💡 Suggestions")
            for suggestion in suggestions[:3]:  # Limit to 3 suggestions
                ui.bullet(suggestion)

    async def run(self):
        """Runs the main read-eval-print loop."""
        
        # Initialize enhanced features
        try:
            await model_manager.initialize()
            persistence.auto_restore()
            log.debug("Enhanced features initialized")
        except Exception as e:
            log.error(f"Failed to initialize enhanced features: {e}")
        
        ui.info(f"Using model {session.current_model}")
        ui.success("Welcome to Terminus — ready to go.")
        prompt_session = create_multiline_prompt_session()

        while True:
            ui.line()

            try:
                user_input = await get_multiline_input(prompt_session)
            except (EOFError, KeyboardInterrupt):
                break

            ui.line()
            ui.reset_output_context()

            if not user_input:
                continue

            if _should_exit(user_input):
                break

            if await handle_command(user_input):
                # Don't auto-save after slash commands - they don't generate meaningful conversation
                continue

            await self._handle_user_request(user_input)
            signal.signal(signal.SIGINT, self.signal_handler)
            
            # Auto-save session after actual AI interactions (not slash commands)
            try:
                persistence.auto_save()
            except Exception as e:
                log.debug(f"Auto-save failed: {e}")

        _restore_default_signal_handler()
        
        # Final save before exit (only if session has meaningful content)
        try:
            user_messages = [msg for msg in session.messages if msg.get('role') == 'user']
            if len(user_messages) > 0:
                persistence.save_session("exit_session")
        except Exception as e:
            log.debug(f"Exit save failed: {e}")
            
        ui.info("Thanks for all the fish.")

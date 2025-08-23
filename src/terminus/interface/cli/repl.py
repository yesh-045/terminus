import asyncio
import logging
import signal

from terminus import ui
from terminus.core.agent import get_or_create_agent, process_request
from terminus.interface.cli.commands import handle_command
from terminus.core.session import session
from terminus.utils.error import ErrorContext
from terminus.utils.input import create_multiline_prompt_session, get_multiline_input
from terminus.infrastructure.models.models import model_manager
from terminus.core.persistence import persistence

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
        ui.start_spinner(ui.get_thinking_message())
        session.sigint_received = False

        request_task = asyncio.create_task(process_request(user_input))
        session.current_task = request_task

        ctx = ErrorContext("request", ui)

        try:
            resp = await request_task
            ui.stop_spinner()
            if resp:
                ui.agent(resp)
        except asyncio.CancelledError as e:
            await ctx.handle(e)
        except KeyboardInterrupt:
            ui.stop_spinner()
            if not request_task.done():
                request_task.cancel()
                try:
                    await request_task
                except asyncio.CancelledError:
                    pass
            ui.warning("Request interrupted")
        except Exception as e:
            await ctx.handle(e)
        finally:
            session.current_task = None

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

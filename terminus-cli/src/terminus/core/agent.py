import logging
import os
from pathlib import Path
from typing import Any, Optional

from pydantic_ai import Agent, CallToolsNode
from pydantic_ai.messages import (
    ModelRequest,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)

from terminus import ui
from ..constants import DEFAULT_MODEL
from .deps import ToolDeps
from ..infrastructure.natural_language import nl_processor
from .session import session
from ..tools import TOOLS
from ..utils.error import ErrorContext
from ..utils.guide import get_guide

log = logging.getLogger(__name__)

# Configure Ollama to work with OpenAI-compatible API
def _setup_ollama_config():
    """Set up environment variables for Ollama OpenAI compatibility."""
    # Ollama's OpenAI-compatible API endpoint
    os.environ["OPENAI_BASE_URL"] = "http://localhost:11434/v1"
    # Dummy API key (Ollama doesn't require authentication)
    if "OPENAI_API_KEY" not in os.environ:
        os.environ["OPENAI_API_KEY"] = "ollama"
    # Force function calling for OpenAI models
    os.environ["OPENAI_FORCE_FUNCTION_CALLING"] = "true"


def _convert_model_name_for_pydantic_ai(model_name: str) -> str:
    """Convert our model names to pydantic-ai compatible format."""
    if model_name.startswith("ollama:"):
        # For Ollama models, we'll use OpenAI compatibility mode
        # This requires Ollama to be running with OpenAI API compatibility
        ollama_model = model_name.replace("ollama:", "")
        log.debug(f"Converting Ollama model to OpenAI format: {model_name} -> openai:{ollama_model}")
        return f"openai:{ollama_model}"
            
    elif model_name.startswith("google"):
        # Handle Google models
        if model_name == "google-gla:gemini-2.0-flash-exp":
            return "gemini-2.0-flash-exp"
        elif model_name == "google:gemini-1.5-pro":
            return "gemini-1.5-pro"
    
    # Fallback to original name
    return model_name


def _get_prompt(name: str) -> str:
    try:
        prompt_path = Path(__file__).parent / "prompts" / f"{name}.txt"
        return prompt_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return f"Error: Prompt file '{name}.txt' not found"


async def _process_node(node):
    # from rich import print
    # print('-' * 20)
    # print(node)
    # print('-' * 20)

    if isinstance(node, CallToolsNode):
        for part in node.model_response.parts:
            if isinstance(part, ToolCallPart):
                log.debug(f"Calling tool: {part.tool_name}")

            # I cant' find a definitive way to check if a text part is a "thinking" response
            # or not, but majority of the time they are accompanied by other tool calls.
            # Using that as a basis for showing "thinking" messages.
            if isinstance(part, TextPart) and len(node.model_response.parts) > 1:
                ui.stop_spinner()
                ui.thinking(part.content)
                ui.start_spinner()

    if hasattr(node, "request"):
        session.messages.append(node.request)
        log.debug("Added request to message history")

        for part in node.request.parts:
            if part.part_kind == "retry-prompt":
                if session.spinner:
                    session.spinner.stop()
                error_msg = (
                    part.content
                    if hasattr(part, "content") and isinstance(part.content, str)
                    else "Trying a different approach"
                )
                ui.muted(f"{error_msg}")
                if session.spinner:
                    session.spinner.start()

    if hasattr(node, "model_response"):
        session.messages.append(node.model_response)
        log.debug("Added model response to message history")


def get_or_create_agent():
    # Set up Ollama configuration for OpenAI compatibility
    _setup_ollama_config()
    
    if "default" not in session.agents:
        # Get enhanced system prompt based on current model
        system_prompt = _get_enhanced_system_prompt()
        
        # Convert model name to pydantic-ai format
        pydantic_model = _convert_model_name_for_pydantic_ai(session.current_model)
        log.debug(f"Creating agent with model: {session.current_model} -> {pydantic_model}")
        log.debug(f"Number of tools available: {len(TOOLS)}")
        log.debug(f"System prompt length: {len(system_prompt)}")
        
        # Debug: Print first part of system prompt for Ollama models
        if session.current_model.startswith("ollama:"):
            log.debug(f"Using enhanced system prompt for Ollama model: {system_prompt[:200]}...")
        
        try:
            # For Ollama models through OpenAI API, create agent with specific configuration
            if session.current_model.startswith("ollama:"):
                base_agent = Agent(
                    model=pydantic_model,
                    system_prompt=system_prompt,
                    tools=TOOLS,
                    deps_type=ToolDeps,
                    # Force function calling for Ollama models
                    model_settings={'tool_choice': 'auto'}
                )
            else:
                base_agent = Agent(
                    model=pydantic_model,
                    system_prompt=system_prompt,
                    tools=TOOLS,
                    deps_type=ToolDeps,
                )
            session.agents["default"] = base_agent
            log.debug(f"Agent created successfully with {len(TOOLS)} tools")
        except Exception as e:
            log.error(f"Failed to create agent with model {pydantic_model}: {e}")
            # Fallback to default model if Ollama fails
            if session.current_model.startswith("ollama:"):
                log.warning(f"Ollama model {session.current_model} failed, falling back to default model")
                ui.warning(f"Ollama model {session.current_model} not available, using default model")
                base_agent = Agent(
                    model=DEFAULT_MODEL,
                    system_prompt=system_prompt,
                    tools=TOOLS,
                    deps_type=ToolDeps,
                )
                session.agents["default"] = base_agent
            else:
                raise e
                
    else:
        # Update model if it changed
        agent = session.agents["default"]
        pydantic_model = _convert_model_name_for_pydantic_ai(session.current_model)
        
        if agent.model != pydantic_model:
            log.debug(f"Updating agent model from {agent.model} to {pydantic_model}")
            # Create new agent with updated model
            system_prompt = _get_enhanced_system_prompt()
            try:
                # For Ollama models through OpenAI API, create agent with specific configuration
                if session.current_model.startswith("ollama:"):
                    base_agent = Agent(
                        model=pydantic_model,
                        system_prompt=system_prompt,
                        tools=TOOLS,
                        deps_type=ToolDeps,
                        # Force function calling for Ollama models
                        model_settings={'tool_choice': 'auto'}
                    )
                else:
                    base_agent = Agent(
                        model=pydantic_model,
                        system_prompt=system_prompt,
                        tools=TOOLS,
                        deps_type=ToolDeps,
                    )
                session.agents["default"] = base_agent
                log.debug(f"Agent updated successfully with {len(TOOLS)} tools")
            except Exception as e:
                log.error(f"Failed to update agent with model {pydantic_model}: {e}")
                # Keep the existing agent if update fails
                ui.warning(f"Failed to switch to {session.current_model}, keeping current model")
            
    return session.agents["default"]


def _get_enhanced_system_prompt() -> str:
    """Get system prompt enhanced for specific models."""
    
    # For local models (Qwen, Ollama), use the enhanced prompt that emphasizes tool usage
    if session.current_model and ("qwen" in session.current_model.lower() or 
                                  "ollama" in session.current_model.lower()):
        try:
            return _get_prompt("local_model_system")
        except:
            # Fallback to base prompt with enhancement if file not found
            base_prompt = _get_prompt("system")
            local_model_enhancement = """

### CRITICAL: TOOL USAGE IS MANDATORY

You MUST use the provided tools for ALL operations. DO NOT generate code or file contents directly.

**WRONG**: Generating README content in your response
**RIGHT**: Using write_file tool to create README

**WRONG**: Showing code without reading files
**RIGHT**: Using read_file to examine files first

ALWAYS use tools for file operations - tool usage is mandatory, not optional."""
            
            return base_prompt + local_model_enhancement
    
    # For API models, use the standard prompt
    return _get_prompt("system")


def _create_confirmation_callback():
    async def confirm(title: str, preview: Any, footer: Optional[str] = None) -> bool:
        tool_name = title.split(":")[0].strip() if ":" in title else title

        if not session.confirmation_enabled or tool_name in session.disabled_confirmations:
            return True

        if session.spinner:
            session.spinner.stop()

        ui.display_tool_panel(preview, title, footer)

        # Display confirmation options without using a panel, but still
        # indented by two spaces so they line up with other panel content.
        options = (
            ("y", "Yes, execute this tool"),
            ("a", "Always allow this tool"),
            ("n", "No, cancel this execution"),
        )

        # Add a single blank line before options
        ui.console.print()

        for key, description in options:
            ui.console.print(f"  {key}: {description}", style=ui.colors.warning)

        while True:
            choice = ui.console.input("  Continue? (y): ").lower().strip()

            if choice == "" or choice in ["y", "yes"]:
                ui.line()
                ui.reset_output_context()  # Reset after user input
                if session.spinner:
                    session.spinner.start()
                return True
            elif choice in ["a", "always"]:
                session.disabled_confirmations.add(tool_name)
                ui.line()
                ui.reset_output_context()  # Reset after user input
                if session.spinner:
                    session.spinner.start()
                return True
            elif choice in ["n", "no"]:
                ui.reset_output_context()  # Reset after user input
                return False

    return confirm


def _create_display_tool_status_callback():
    async def display(title: str, *args: Any, **kwargs: Any) -> None:
        """
        Display the current tool status.

        Args:
            title: str
            *args: Any
            **kwargs: Any
                Keyword arguments passed to the tool. These will be rendered in the
                form ``key=value`` in the output.
        """
        if session.spinner:
            session.spinner.stop()

        parts = []
        if args:
            parts.extend(str(arg) for arg in args)
        if kwargs:
            parts.extend(f"{k}={v}" for k, v in kwargs.items())

        arg_str = ", ".join(parts)
        ui.info(f"{title}({arg_str})")

        if session.spinner:
            session.spinner.start()

    return display


def _patch_history_on_error(error_message: str):
    """
    Patches the message history with a ToolReturnPart on error.
    """
    if not session.messages:
        return

    last_message = session.messages[-1]

    if not (
        hasattr(last_message, "kind")
        and last_message.kind == "response"
        and hasattr(last_message, "parts")
    ):
        return

    last_tool_call = None
    for part in reversed(last_message.parts):
        if hasattr(part, "part_kind") and part.part_kind == "tool-call":
            last_tool_call = part
            break

    if last_tool_call:
        tool_return = ToolReturnPart(
            tool_name=last_tool_call.tool_name,
            tool_call_id=last_tool_call.tool_call_id,
            content=error_message,
        )
        session.messages.append(ModelRequest(parts=[tool_return]))


async def _try_force_tool_usage(message: str) -> Optional[str]:
    """Force tool usage for common patterns when Ollama doesn't use function calling properly."""
    message_lower = message.lower().strip()
    
    # Import tools directly for manual execution
    from terminus.tools.directory import get_current_directory, change_directory
    from terminus.tools.list import list_directory
    from terminus.tools.read_file import read_file
    from terminus.deps import ToolDeps
    from pydantic_ai import RunContext
    
    try:
        deps = ToolDeps(
            confirm_action=_create_confirmation_callback(),
            display_tool_status=_create_display_tool_status_callback(),
        )
        ctx = RunContext(deps=deps)
        
        # Pattern matching for common requests
        if any(phrase in message_lower for phrase in ["current directory", "where am i", "pwd", "current folder"]):
            ui.tool("get_current_directory", "Getting current directory", color="directory")
            result = await get_current_directory(ctx)
            return f"Current directory: {result}"
            
        elif any(phrase in message_lower for phrase in ["navigate to", "go to", "cd "]):
            # Extract directory from message
            for phrase in ["navigate to", "go to", "cd "]:
                if phrase in message_lower:
                    parts = message_lower.split(phrase, 1)
                    if len(parts) > 1:
                        directory = parts[1].strip().strip('"\'')
                        if directory:
                            ui.tool("change_directory", f"Navigating to {directory}", color="directory")
                            result = await change_directory(ctx, directory)
                            return result
                            
        elif any(phrase in message_lower for phrase in ["list files", "show files", "ls", "dir"]):
            path = "."
            # Check if specific path mentioned
            if " in " in message_lower:
                parts = message_lower.split(" in ", 1)
                if len(parts) > 1:
                    path = parts[1].strip().strip('"\'')
            ui.tool("list_directory", f"Listing directory {path}", color="directory")
            result = await list_directory(ctx, path)
            return f"Contents of {path}:\n{result}"
            
        elif any(phrase in message_lower for phrase in ["read ", "show ", "cat "]):
            # Extract filename
            for phrase in ["read ", "show ", "cat "]:
                if phrase in message_lower:
                    parts = message_lower.split(phrase, 1)
                    if len(parts) > 1:
                        filename = parts[1].strip().strip('"\'')
                        if filename and not any(word in filename for word in ["file", "files", "directory"]):
                            ui.tool("read_file", f"Reading {filename}", color="file")
                            result = await read_file(ctx, filename)
                            return f"Contents of {filename}:\n```\n{result}\n```"
                            
    except Exception as e:
        log.debug(f"Force tool usage failed: {e}")
        return None
        
    return None


async def process_request(message: str):
    log.debug(f"Processing request: {message.replace('\n', ' ')[:100]}...")

    # First, try natural language processing for quick wins
    nl_result = nl_processor.process_input(message)
    if nl_result:
        command, description, color = nl_result
        log.debug(f"Natural language match: '{message}' → '{command}' ({description})")
        
        # Show color-coded feedback
        if color == 'safe':
            ui.success(f"🟢 {description}: {command}")
        elif color == 'destructive':
            ui.warning(f"🔴 {description}: {command}")
        else:
            ui.info(f"🟡 {description}: {command}")
        
        # Enhance the message with the natural language understanding
        enhanced_message = f"User request: {message}\n\nBased on natural language processing, this appears to be a request to: {description}\nSuggested approach: {command}\n\nPlease execute this request using the appropriate tools."
        message = enhanced_message

    # For Ollama models, try to force tool usage for common patterns
    if session.current_model and session.current_model.startswith("ollama:"):
        forced_result = await _try_force_tool_usage(message)
        if forced_result:
            return forced_result

    agent = get_or_create_agent()

    mh = session.messages.copy()
    log.debug(f"Message history size: {len(mh)}")

    project_guide = get_guide(session)
    if project_guide:
        guide_message = ModelRequest(parts=[UserPromptPart(content=project_guide)])
        mh.insert(0, guide_message)
        log.debug("Prepended project guide to message history")

    deps = ToolDeps(
        confirm_action=_create_confirmation_callback(),
        display_tool_status=_create_display_tool_status_callback(),
    )

    ctx = ErrorContext("agent", ui)
    ctx.add_cleanup(lambda e: _patch_history_on_error(str(e)))

    try:
        async with agent.iter(message, deps=deps, message_history=mh) as agent_run:
            async for node in agent_run:
                await _process_node(node)

            result = agent_run.result.output
            log.debug(f"Agent response: {result.replace('\n', ' ')[:100]}...")
            return result
    except Exception as e:
        return await ctx.handle(e)

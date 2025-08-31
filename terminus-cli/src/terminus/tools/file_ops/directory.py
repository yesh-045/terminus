"""Directory management tools with session awareness."""

import logging
from pathlib import Path

from pydantic_ai import RunContext

from ...core.deps import ToolDeps
from terminus.core.session import session

log = logging.getLogger(__name__)


async def change_directory(ctx: RunContext[ToolDeps], path: str) -> str:
    """Change the current working directory for the session."""
    log.debug(f"change_directory called with path: {path}")

    if ctx.deps and ctx.deps.display_tool_status:
        await ctx.deps.display_tool_status("Navigate", path, color="directory")

    result = session.change_directory(path)
    log.debug(f"Directory change result: {result}")
    return result


async def get_current_directory(ctx: RunContext[ToolDeps]) -> str:
    """Get the current working directory."""
    log.debug("get_current_directory called")

    if ctx.deps and ctx.deps.display_tool_status:
        await ctx.deps.display_tool_status("PWD", "Current Directory", color="directory")

    current_dir = session.get_cwd()
    log.debug(f"Current directory: {current_dir}")
    return f"Current working directory: {current_dir}"


async def run_in_directory(ctx: RunContext[ToolDeps], path: str, command: str) -> str:
    """Execute a command in a specific directory without changing session directory."""
    import subprocess
    
    log.debug(f"run_in_directory called with path: {path}, command: {command}")

    if ctx.deps and ctx.deps.display_tool_status:
        await ctx.deps.display_tool_status("Exec", f"{command} (in {path})", color="command")

    try:
        # Resolve the path relative to session working directory
        target_path = session.resolve_path(path)
        
        if not target_path.exists() or not target_path.is_dir():
            return f"Error: Directory does not exist: {path}"

        # Execute command in the specified directory
        result = subprocess.run(
            command,
            shell=True,
            cwd=target_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = []
        if result.stdout:
            output.append(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            output.append(f"STDERR:\n{result.stderr}")
        if result.returncode != 0:
            output.append(f"Exit code: {result.returncode}")
            
        return "\n".join(output) if output else "Command executed successfully (no output)"
        
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds"
    except Exception as e:
        log.error(f"Error executing command in directory: {str(e)}")
        return f"Error executing command: {str(e)}"

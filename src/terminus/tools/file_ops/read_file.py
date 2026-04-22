import logging

from pydantic_ai import RunContext
from terminus.core.session import session

log = logging.getLogger(__name__)


async def read_file(ctx: RunContext, filepath: str) -> str:
    """Read the contents of a file."""
    log.debug(f"read_file called with filepath: {filepath}")

    # Resolve path relative to session working directory
    resolved_path = session.resolve_path(filepath)
    
    if ctx.deps and ctx.deps.display_tool_status:
        await ctx.deps.display_tool_status("Read", str(resolved_path))

    try:
        with open(resolved_path, "r", encoding="utf-8") as file:
            content = file.read()
            log.debug(f"Successfully read {len(content)} characters from {resolved_path}")
            return content
    except FileNotFoundError:
        return f"Error: File not found: {resolved_path}"
    except PermissionError:
        return f"Error: Permission denied: {resolved_path}"
    except Exception as e:
        return f"Error reading file {resolved_path}: {str(e)}"

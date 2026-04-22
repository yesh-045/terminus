import asyncio
import logging
from pathlib import Path

from pydantic_ai import RunContext

from terminus import ui
from terminus.core.session import session

log = logging.getLogger(__name__)


async def write_file(ctx: RunContext, filepath: str, content: str) -> str:
    """Write content to a file."""
    log.debug(f"write_file called with filepath: {filepath}, content length: {len(content)}")

    # Resolve path relative to session working directory
    resolved_path = session.resolve_path(filepath)

    # Write content is in a panel already, showing this here feels redundant
    # Commenting out for now
    #
    # if ctx.deps and ctx.deps.display_tool_status:
    #     await ctx.deps.display_tool_status("Write", str(resolved_path))

    if ctx.deps and ctx.deps.confirm_action:
        syntax = ui.create_syntax_highlighted(content, str(resolved_path))
        footer = f"File: {resolved_path}"
        if not await ctx.deps.confirm_action("Write File", syntax, footer):
            raise asyncio.CancelledError("Tool execution cancelled by user")

    resolved_path.parent.mkdir(parents=True, exist_ok=True)

    with open(resolved_path, "w", encoding="utf-8") as file:
        file.write(content)

    return f"Successfully wrote to {resolved_path}"

import asyncio

from pydantic_ai import ModelRetry, RunContext

from terminus import ui
from terminus.core.session import session


async def update_file(
    ctx: RunContext, filepath: str, old_content: str, new_content: str
) -> str:
    # Resolve path relative to session working directory
    resolved_path = session.resolve_path(filepath)
    
    # Ignore for now, we already show panel
    #
    # if ctx.deps and ctx.deps.display_tool_status:
    #     await ctx.deps.display_tool_status("Update", str(resolved_path))

    if old_content == new_content:
        raise ModelRetry(
            "The old_content and new_content are identical. "
            "Please provide different content for the replacement."
        )

    try:
        with open(resolved_path, "r", encoding="utf-8") as file:
            content = file.read()
    except FileNotFoundError:
        raise ModelRetry(f"File not found: {resolved_path}. Please check the file path and try again.")
    except Exception as e:
        raise ModelRetry(f"Error reading file {resolved_path}: {str(e)}")

    if old_content not in content:
        preview = old_content[:100] + "..." if len(old_content) > 100 else old_content
        raise ModelRetry(
            f"Content to replace not found in {resolved_path}. "
            f"Searched for: '{preview}'. "
            "Please re-read the file and ensure the exact content matches, including whitespace."
        )

    if ctx.deps and ctx.deps.confirm_action:
        updated_content = content.replace(old_content, new_content, 1)
        diff_preview = ui.create_unified_diff(content, updated_content, str(resolved_path))
        footer = f"File: {resolved_path}"

        if not await ctx.deps.confirm_action("Update File", diff_preview, footer):
            raise asyncio.CancelledError("Tool execution cancelled by user")

    try:
        updated_content = content.replace(old_content, new_content, 1)
        with open(resolved_path, "w", encoding="utf-8") as file:
            file.write(updated_content)
    except Exception as e:
        raise ModelRetry(f"Error writing to file {resolved_path}: {str(e)}")

    return f"Successfully updated {resolved_path}"

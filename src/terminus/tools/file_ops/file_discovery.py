"""Enhanced file discovery tools with extension filtering and gitignore support."""

import logging
from pathlib import Path
from typing import List

from pydantic_ai import RunContext

from ...core.deps import ToolDeps
from terminus.core.session import session

log = logging.getLogger(__name__)


def _load_gitignore_patterns(directory: Path) -> List[str]:
    """Load .gitignore patterns from the directory and parent directories."""
    patterns = []
    current_dir = directory
    
    # Walk up the directory tree looking for .gitignore files
    while current_dir != current_dir.parent:
        gitignore_path = current_dir / ".gitignore"
        if gitignore_path.exists():
            try:
                with open(gitignore_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            patterns.append(line)
            except Exception as e:
                log.debug(f"Error reading .gitignore at {gitignore_path}: {e}")
        current_dir = current_dir.parent
    
    return patterns


def _should_ignore(file_path: Path, gitignore_patterns: List[str], base_path: Path) -> bool:
    """Check if a file should be ignored based on gitignore patterns."""
    try:
        relative_path = file_path.relative_to(base_path)
        path_str = str(relative_path).replace('\\', '/')
        
        for pattern in gitignore_patterns:
            # Simple pattern matching (can be enhanced with fnmatch for more complex patterns)
            if pattern.endswith('/'):
                # Directory pattern
                if path_str.startswith(pattern) or f"/{pattern}" in f"/{path_str}/":
                    return True
            else:
                # File pattern
                if pattern in path_str or path_str.endswith(pattern):
                    return True
                if pattern.startswith('*') and path_str.endswith(pattern[1:]):
                    return True
    except ValueError:
        # File is not relative to base_path
        pass
    
    return False


async def find_by_extension(
    ctx: RunContext[ToolDeps], 
    extension: str = ".py", 
    path: str = ".",
    respect_gitignore: bool = True
) -> str:
    """Recursively find all files with the given extension."""
    log.debug(f"find_by_extension called with extension: {extension}, path: {path}")

    if ctx.deps and ctx.deps.display_tool_status:
        await ctx.deps.display_tool_status("Search", f"*{extension} files in {path}", color="extension")

    try:
        # Resolve path relative to session directory
        search_path = session.resolve_path(path)
        
        if not search_path.exists():
            return f"Error: Path does not exist: {path}"
        
        if not search_path.is_dir():
            return f"Error: Path is not a directory: {path}"

        # Load gitignore patterns if requested
        gitignore_patterns = []
        if respect_gitignore:
            gitignore_patterns = _load_gitignore_patterns(search_path)

        # Find files with the specified extension
        found_files = []
        
        for file_path in search_path.rglob(f"*{extension}"):
            if file_path.is_file():
                # Check gitignore patterns
                if respect_gitignore and _should_ignore(file_path, gitignore_patterns, search_path):
                    continue
                
                # Get relative path for cleaner output
                try:
                    rel_path = file_path.relative_to(session.working_directory)
                    found_files.append(str(rel_path))
                except ValueError:
                    # File is outside session directory, use absolute path
                    found_files.append(str(file_path))

        if not found_files:
            return f"No files with extension '{extension}' found in {path}"

        # Sort files for consistent output
        found_files.sort()
        
        result = f"Found {len(found_files)} files with extension '{extension}':\n"
        result += "\n".join(f"  {file}" for file in found_files)
        
        return result

    except Exception as e:
        log.error(f"Error in find_by_extension: {str(e)}")
        return f"Error searching for files: {str(e)}"


async def list_extensions(ctx: RunContext[ToolDeps], path: str = ".") -> str:
    """List all unique file extensions in a directory tree."""
    log.debug(f"list_extensions called with path: {path}")

    if ctx.deps and ctx.deps.display_tool_status:
        await ctx.deps.display_tool_status("Analyze", f"Extensions in {path}", color="extension")

    try:
        search_path = session.resolve_path(path)
        
        if not search_path.exists() or not search_path.is_dir():
            return f"Error: Invalid directory path: {path}"

        extensions = set()
        file_count = 0
        
        for file_path in search_path.rglob("*"):
            if file_path.is_file():
                file_count += 1
                if file_path.suffix:
                    extensions.add(file_path.suffix.lower())

        if not extensions:
            return f"No files with extensions found in {path}"

        sorted_extensions = sorted(extensions)
        result = f"Found {len(sorted_extensions)} unique extensions in {file_count} files:\n"
        result += "\n".join(f"  {ext}" for ext in sorted_extensions)
        
        return result

    except Exception as e:
        log.error(f"Error in list_extensions: {str(e)}")
        return f"Error analyzing extensions: {str(e)}"

"""Code summarization tool using LLM capabilities."""

import logging
from pathlib import Path

from pydantic_ai import RunContext

from ...core.deps import ToolDeps
from terminus.core.session import session

log = logging.getLogger(__name__)


async def summarize_code(ctx: RunContext[ToolDeps], filepath: str) -> str:
    """Read and summarize code file using LLM."""
    log.debug(f"summarize_code called with filepath: {filepath}")

    if ctx.deps and ctx.deps.display_tool_status:
        await ctx.deps.display_tool_status("Analyze", f"Summarizing {filepath}", color="summary")

    try:
        # Resolve path relative to session directory
        file_path = session.resolve_path(filepath)
        
        if not file_path.exists():
            return f"Error: File does not exist: {filepath}"
        
        if not file_path.is_file():
            return f"Error: Path is not a file: {filepath}"

        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                # Try with different encoding for binary files
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
            except Exception:
                return f"Error: Cannot read file {filepath} - it may be a binary file"
        except Exception as e:
            return f"Error reading file {filepath}: {str(e)}"

        if not content.strip():
            return f"File {filepath} is empty"

        # Get file info
        file_size = len(content)
        line_count = content.count('\n') + 1
        extension = file_path.suffix.lower()

        # Create summary prompt
        summary_prompt = f"""Please provide a concise summary of this code file:

File: {filepath}
Extension: {extension}
Size:  {line_count} lines

Code:
```{extension[1:] if extension else 'text'}
{content}
```

Please summarize:
1. Purpose and functionality
2. Key components/classes/functions
3. Dependencies and imports
4. Main algorithms or patterns used
5. Any notable features or complexity

Keep the summary clear and concise."""

        # Here we would call the LLM agent to summarize
        # For now, we'll do a simple structural analysis
        lines = content.split('\n')
        imports = [line.strip() for line in lines if line.strip().startswith(('import ', 'from '))]
        
        # Simple function/class detection
        functions = []
        classes = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('def '):
                func_name = stripped.split('(')[0].replace('def ', '')
                functions.append(func_name)
            elif stripped.startswith('class '):
                class_name = stripped.split('(')[0].split(':')[0].replace('class ', '')
                classes.append(class_name)

        # Build summary
        summary_parts = [
            f" Code Summary: {file_path.name}",
            f" Stats: {line_count} lines",
        ]
        
        if imports:
            summary_parts.append(f" Imports ({len(imports)}): {', '.join(imports[:5])}")
            if len(imports) > 5:
                summary_parts.append(f"   ... and {len(imports) - 5} more")
        
        if classes:
            summary_parts.append(f"  Classes ({len(classes)}): {', '.join(classes)}")
        
        if functions:
            summary_parts.append(f"  Functions ({len(functions)}): {', '.join(functions[:10])}")
            if len(functions) > 10:
                summary_parts.append(f"   ... and {len(functions) - 10} more")

        # Add file type insights
        if extension in ['.py']:
            summary_parts.append(" Python file")
        elif extension in ['.js', '.ts']:
            summary_parts.append(" JavaScript/TypeScript file")
        elif extension in ['.html', '.htm']:
            summary_parts.append(" HTML file")
        elif extension in ['.css']:
            summary_parts.append(" CSS file")
        elif extension in ['.md']:
            summary_parts.append(" Markdown file")
        elif extension in ['.json']:
            summary_parts.append(" JSON configuration file")
        elif extension in ['.yml', '.yaml']:
            summary_parts.append("⚙️ YAML configuration file")

        return "\n".join(summary_parts)

    except Exception as e:
        log.error(f"Error in summarize_code: {str(e)}")
        return f"Error summarizing code: {str(e)}"


async def analyze_project_structure(ctx: RunContext[ToolDeps], path: str = ".") -> str:
    """Analyze and summarize the overall project structure."""
    log.debug(f"analyze_project_structure called with path: {path}")

    if ctx.deps and ctx.deps.display_tool_status:
        await ctx.deps.display_tool_status("Analyze", f"Project structure in {path}", color="summary")

    try:
        project_path = session.resolve_path(path)
        
        if not project_path.exists() or not project_path.is_dir():
            return f"Error: Invalid project directory: {path}"

        # Collect project statistics
        file_types = {}
        total_files = 0
        total_dirs = 0
        
        for item in project_path.rglob("*"):
            if item.is_file():
                total_files += 1
                ext = item.suffix.lower() or 'no_extension'
                file_types[ext] = file_types.get(ext, 0) + 1
            elif item.is_dir():
                total_dirs += 1

        # Build project summary
        summary = [
            f" Project Structure Analysis: {project_path.name}",
            f" Overview: {total_dirs} directories, {total_files} files",
            ""
        ]

        if file_types:
            summary.append("File Types:")
            sorted_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)
            for ext, count in sorted_types[:15]:  # Top 15 file types
                summary.append(f"   {ext}: {count} files")
            if len(sorted_types) > 15:
                summary.append(f"   ... and {len(sorted_types) - 15} more types")

        # Look for common project files
        common_files = [
            'README.md', 'README.txt', 'package.json', 'requirements.txt',
            'Cargo.toml', 'setup.py', 'pyproject.toml', 'Makefile',
            '.gitignore', 'LICENSE', 'docker-compose.yml', 'Dockerfile'
        ]
        
        found_files = []
        for file_name in common_files:
            if (project_path / file_name).exists():
                found_files.append(file_name)
        
        if found_files:
            summary.append("")
            summary.append(" Project Files Found:")
            summary.append(f"   {', '.join(found_files)}")

        return "\n".join(summary)

    except Exception as e:
        log.error(f"Error in analyze_project_structure: {str(e)}")
        return f"Error analyzing project structure: {str(e)}"

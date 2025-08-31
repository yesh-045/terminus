"""System utilities and helper commands for enhanced productivity."""

import logging
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from pydantic_ai import RunContext

from ...core.deps import ToolDeps
from terminus.core.session import session
from terminus.ui.colors import colors

log = logging.getLogger(__name__)


async def system_info(ctx: RunContext[ToolDeps]) -> str:
    """Display comprehensive system information."""
    log.debug("system_info called")

    if ctx.deps and ctx.deps.display_tool_status:
        await ctx.deps.display_tool_status("System", "Gathering system info", color="info")

    try:
        # System details
        system = platform.system()
        release = platform.release()
        version = platform.version()
        machine = platform.machine()
        processor = platform.processor()
        
        # Python details
        python_version = sys.version.split()[0]
        python_path = sys.executable
        
        # Current working directory
        current_dir = session.get_cwd()
        
        # Disk usage
        disk_usage = shutil.disk_usage(current_dir)
        total_gb = disk_usage.total / (1024**3)
        free_gb = disk_usage.free / (1024**3)
        used_gb = (disk_usage.total - disk_usage.free) / (1024**3)
        
        # Memory info (if available)
        memory_info = ""
        try:
            if system == "Windows":
                result = subprocess.run(
                    ["wmic", "computersystem", "get", "TotalPhysicalMemory", "/value"],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'TotalPhysicalMemory=' in line:
                            memory_bytes = int(line.split('=')[1])
                            memory_gb = memory_bytes / (1024**3)
                            memory_info = f"[{colors.accent}]Memory:[/{colors.accent}] {memory_gb:.1f} GB"
                            break
            elif system in ["Linux", "Darwin"]:
                # Try using free command or vm_stat
                pass
        except Exception:
            pass
        
        # Environment variables of interest
        env_vars = []
        interesting_vars = ["PATH", "HOME", "USER", "USERNAME", "SHELL", "TERM"]
        for var in interesting_vars:
            value = os.environ.get(var)
            if value:
                if var == "PATH":
                    path_count = len(value.split(os.pathsep))
                    env_vars.append(f"   {var}: {path_count} paths")
                else:
                    env_vars.append(f"   {var}: {value}")
        
        result_parts = [
            f"[{colors.primary}]🖥️ System Information[/{colors.primary}]",
            "",
            f"[{colors.accent}]Operating System:[/{colors.accent}] {system} {release}",
            f"[{colors.accent}]Architecture:[/{colors.accent}] {machine}",
            f"[{colors.accent}]Processor:[/{colors.accent}] {processor}" if processor else "",
            "",
            f"[{colors.accent}]Python Version:[/{colors.accent}] {python_version}",
            f"[{colors.accent}]Python Path:[/{colors.accent}] {python_path}",
            "",
            f"[{colors.accent}]Current Directory:[/{colors.accent}] [{colors.path}]{current_dir}[/{colors.path}]",
            "",
            f"[{colors.accent}]Disk Usage:[/{colors.accent}]",
            f"   Total: {total_gb:.1f} GB",
            f"   Used: {used_gb:.1f} GB ({(used_gb/total_gb)*100:.1f}%)",
            f"   Free: {free_gb:.1f} GB ({(free_gb/total_gb)*100:.1f}%)",
        ]
        
        if memory_info:
            result_parts.append("")
            result_parts.append(memory_info)
        
        if env_vars:
            result_parts.extend([
                "",
                f"[{colors.accent}]Environment Variables:[/{colors.accent}]",
                *env_vars
            ])
        
        # Filter out empty strings
        result_parts = [part for part in result_parts if part is not None and part != ""]
        
        return "\n".join(result_parts)

    except Exception as e:
        log.error(f"Error getting system info: {e}")
        return f"[{colors.error}]Error gathering system information: {e}[/{colors.error}]"


async def quick_stats(ctx: RunContext[ToolDeps], path: str = ".") -> str:
    """Get quick statistics about files and directories in a path."""
    log.debug(f"quick_stats called with path: {path}")

    if ctx.deps and ctx.deps.display_tool_status:
        await ctx.deps.display_tool_status("Stats", f"Analyzing {path}", color="analysis")

    try:
        target_path = session.resolve_path(path)
        
        if not target_path.exists():
            return f"[{colors.error}]Path does not exist: {path}[/{colors.error}]"
        
        if target_path.is_file():
            # Single file stats
            size = target_path.stat().st_size
            size_kb = size / 1024
            size_mb = size / (1024 * 1024)
            
            with open(target_path, 'rb') as f:
                content = f.read()
            
            try:
                text_content = content.decode('utf-8')
                lines = text_content.count('\n') + 1
                chars = len(text_content)
                words = len(text_content.split())
            except UnicodeDecodeError:
                lines = chars = words = None
            
            result_parts = [
                f"[{colors.primary}]📄 File Statistics: [{colors.file}]{target_path.name}[/{colors.file}][/{colors.primary}]",
                "",
                f"[{colors.accent}]Size:[/{colors.accent}] {size:,} bytes ({size_kb:.1f} KB)",
            ]
            
            if lines is not None:
                result_parts.extend([
                    f"[{colors.accent}]Lines:[/{colors.accent}] {lines:,}",
                    f"[{colors.accent}]Characters:[/{colors.accent}] {chars:,}",
                    f"[{colors.accent}]Words:[/{colors.accent}] {words:,}",
                ])
            else:
                result_parts.append(f"[{colors.muted}](Binary file)[/{colors.muted}]")
            
            return "\n".join(result_parts)
        
        else:
            # Directory stats
            file_count = 0
            dir_count = 0
            total_size = 0
            file_types = {}
            largest_files = []
            
            for item in target_path.rglob("*"):
                if item.is_file():
                    file_count += 1
                    size = item.stat().st_size
                    total_size += size
                    
                    # Track file types
                    ext = item.suffix.lower() or "no_extension"
                    file_types[ext] = file_types.get(ext, 0) + 1
                    
                    # Track largest files
                    largest_files.append((item, size))
                    
                elif item.is_dir():
                    dir_count += 1
            
            # Sort largest files
            largest_files.sort(key=lambda x: x[1], reverse=True)
            largest_files = largest_files[:5]  # Top 5
            
            # Sort file types by count
            sorted_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)
            
            total_mb = total_size / (1024 * 1024)
            total_gb = total_size / (1024 * 1024 * 1024)
            
            result_parts = [
                f"[{colors.primary}]📁 Directory Statistics: [{colors.directory}]{target_path.name}[/{colors.directory}][/{colors.primary}]",
                "",
                f"[{colors.accent}]Files:[/{colors.accent}] {file_count:,}",
                f"[{colors.accent}]Directories:[/{colors.accent}] {dir_count:,}",
                f"[{colors.accent}]Total Size:[/{colors.accent}] {total_mb:.1f} MB ({total_gb:.2f} GB)" if total_gb > 1 else f"[{colors.accent}]Total Size:[/{colors.accent}] {total_mb:.1f} MB",
            ]
            
            if sorted_types:
                result_parts.extend([
                    "",
                    f"[{colors.accent}]File Types (Top 10):[/{colors.accent}]"
                ])
                for ext, count in sorted_types[:10]:
                    result_parts.append(f"   [{colors.extension}]{ext}[/{colors.extension}]: {count:,} files")
            
            if largest_files:
                result_parts.extend([
                    "",
                    f"[{colors.accent}]Largest Files:[/{colors.accent}]"
                ])
                for file_path, size in largest_files:
                    size_mb = size / (1024 * 1024)
                    relative_path = file_path.relative_to(target_path)
                    result_parts.append(f"   [{colors.file}]{relative_path}[/{colors.file}]: {size_mb:.1f} MB")
            
            return "\n".join(result_parts)

    except Exception as e:
        log.error(f"Error getting stats for {path}: {e}")
        return f"[{colors.error}]Error analyzing {path}: {e}[/{colors.error}]"


async def create_project_template(ctx: RunContext[ToolDeps], name: str, template_type: str = "python") -> str:
    """Create a new project from template."""
    log.debug(f"create_project_template called with name: {name}, type: {template_type}")

    if ctx.deps and ctx.deps.display_tool_status:
        await ctx.deps.display_tool_status("Create", f"Setting up {template_type} project: {name}", color="success")

    try:
        project_path = session.resolve_path(name)
        
        if project_path.exists():
            return f"[{colors.error}]Directory already exists: {name}[/{colors.error}]"
        
        # Create project directory
        project_path.mkdir(parents=True)
        
        templates = {
            "python": {
                "files": {
                    "main.py": '"""Main module for {name}."""\n\ndef main():\n    """Entry point."""\n    print("Hello, {name}!")\n\nif __name__ == "__main__":\n    main()\n',
                    "requirements.txt": "# Add your dependencies here\n",
                    "README.md": "# {name}\n\nA Python project.\n\n## Installation\n\n```bash\npip install -r requirements.txt\n```\n\n## Usage\n\n```bash\npython main.py\n```\n",
                    ".gitignore": "__pycache__/\n*.pyc\n*.pyo\n*.pyd\n.Python\nbuild/\ndevelop-eggs/\ndist/\ndownloads/\neggs/\n.eggs/\nlib/\nlib64/\nparts/\nsdist/\nvar/\nwheels/\n*.egg-info/\n.installed.cfg\n*.egg\nMANIFEST\n\n# PyInstaller\n*.manifest\n*.spec\n\n# Unit test / coverage reports\nhtmlcov/\n.tox/\n.coverage\n.coverage.*\n.cache\nnosetests.xml\ncoverage.xml\n*.cover\n.hypothesis/\n.pytest_cache/\n\n# Virtual environments\n.env\n.venv\nenv/\nvenv/\nENV/\nenv.bak/\nvenv.bak/\n\n# IDEs\n.vscode/\n.idea/\n*.swp\n*.swo\n*~\n",
                },
                "dirs": ["src", "tests", "docs"]
            },
            "web": {
                "files": {
                    "index.html": '<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>{name}</title>\n    <link rel="stylesheet" href="style.css">\n</head>\n<body>\n    <h1>Welcome to {name}</h1>\n    <script src="script.js"></script>\n</body>\n</html>\n',
                    "style.css": "/* Styles for {name} */\n\nbody {{\n    font-family: Arial, sans-serif;\n    margin: 0;\n    padding: 20px;\n    background-color: #f0f0f0;\n}}\n\nh1 {{\n    color: #333;\n    text-align: center;\n}}\n",
                    "script.js": '// JavaScript for {name}\n\nconsole.log("Welcome to {name}!");\n',
                    "README.md": "# {name}\n\nA web project.\n\n## Getting Started\n\nOpen `index.html` in your browser.\n",
                },
                "dirs": ["assets", "css", "js", "images"]
            },
            "node": {
                "files": {
                    "package.json": '{{\n  "name": "{name}",\n  "version": "1.0.0",\n  "description": "A Node.js project",\n  "main": "index.js",\n  "scripts": {{\n    "start": "node index.js",\n    "test": "echo \\"Error: no test specified\\" && exit 1"\n  }},\n  "keywords": [],\n  "author": "",\n  "license": "ISC"\n}}\n',
                    "index.js": '// Main entry point for {name}\n\nconsole.log("Hello from {name}!");\n',
                    "README.md": "# {name}\n\nA Node.js project.\n\n## Installation\n\n```bash\nnpm install\n```\n\n## Usage\n\n```bash\nnpm start\n```\n",
                    ".gitignore": "node_modules/\nnpm-debug.log*\nyarn-debug.log*\nyarn-error.log*\n.npm\n.eslintcache\n.nyc_output\ncoverage/\n.coverage\n.env\n.env.local\n.env.development.local\n.env.test.local\n.env.production.local\n",
                },
                "dirs": ["src", "test", "docs"]
            }
        }
        
        if template_type not in templates:
            available = ", ".join(templates.keys())
            return f"[{colors.error}]Unknown template type: {template_type}[/{colors.error}]\n[{colors.muted}]Available: {available}[/{colors.muted}]"
        
        template = templates[template_type]
        created_files = []
        created_dirs = []
        
        # Create directories
        for dir_name in template.get("dirs", []):
            dir_path = project_path / dir_name
            dir_path.mkdir()
            created_dirs.append(dir_name)
        
        # Create files
        for file_name, content in template.get("files", {}).items():
            file_path = project_path / file_name
            formatted_content = content.format(name=name)
            file_path.write_text(formatted_content, encoding='utf-8')
            created_files.append(file_name)
        
        result_parts = [
            f"[{colors.success}]✓[/{colors.success}] Created {template_type} project: [{colors.directory}]{name}[/{colors.directory}]",
            "",
            f"[{colors.accent}]Created Files:[/{colors.accent}]"
        ]
        
        for file_name in created_files:
            result_parts.append(f"   [{colors.file}]{file_name}[/{colors.file}]")
        
        if created_dirs:
            result_parts.extend([
                "",
                f"[{colors.accent}]Created Directories:[/{colors.accent}]"
            ])
            for dir_name in created_dirs:
                result_parts.append(f"   [{colors.directory}]{dir_name}/[/{colors.directory}]")
        
        result_parts.extend([
            "",
            f"[{colors.info}]Next steps:[/{colors.info}]",
            f"   [{colors.command}]cd {name}[/{colors.command}]",
        ])
        
        if template_type == "python":
            result_parts.append(f"   [{colors.command}]python main.py[/{colors.command}]")
        elif template_type == "node":
            result_parts.extend([
                f"   [{colors.command}]npm install[/{colors.command}]",
                f"   [{colors.command}]npm start[/{colors.command}]"
            ])
        elif template_type == "web":
            result_parts.append(f"   Open [{colors.file}]index.html[/{colors.file}] in browser")
        
        return "\n".join(result_parts)

    except Exception as e:
        log.error(f"Error creating project template: {e}")
        return f"[{colors.error}]Error creating project: {e}[/{colors.error}]"


async def find_large_files(ctx: RunContext[ToolDeps], path: str = ".", min_size_mb: float = 10.0) -> str:
    """Find large files in a directory."""
    log.debug(f"find_large_files called with path: {path}, min_size_mb: {min_size_mb}")

    if ctx.deps and ctx.deps.display_tool_status:
        await ctx.deps.display_tool_status("Search", f"Finding files > {min_size_mb}MB in {path}", color="warning")

    try:
        target_path = session.resolve_path(path)
        
        if not target_path.exists() or not target_path.is_dir():
            return f"[{colors.error}]Invalid directory: {path}[/{colors.error}]"
        
        min_size_bytes = min_size_mb * 1024 * 1024
        large_files = []
        
        for file_path in target_path.rglob("*"):
            if file_path.is_file():
                try:
                    size = file_path.stat().st_size
                    if size >= min_size_bytes:
                        large_files.append((file_path, size))
                except (OSError, PermissionError):
                    continue
        
        if not large_files:
            return f"[{colors.muted}]No files larger than {min_size_mb}MB found in {path}[/{colors.muted}]"
        
        # Sort by size (largest first)
        large_files.sort(key=lambda x: x[1], reverse=True)
        
        result_parts = [
            f"[{colors.primary}]📏 Large Files (> {min_size_mb}MB) in [{colors.directory}]{path}[/{colors.directory}][/{colors.primary}]",
            ""
        ]
        
        total_size = 0
        for file_path, size in large_files:
            size_mb = size / (1024 * 1024)
            total_size += size
            relative_path = file_path.relative_to(target_path)
            result_parts.append(f"   [{colors.file}]{relative_path}[/{colors.file}]: {size_mb:.1f} MB")
        
        total_mb = total_size / (1024 * 1024)
        result_parts.extend([
            "",
            f"[{colors.accent}]Total:[/{colors.accent}] {len(large_files)} files, {total_mb:.1f} MB"
        ])
        
        return "\n".join(result_parts)

    except Exception as e:
        log.error(f"Error finding large files: {e}")
        return f"[{colors.error}]Error searching for large files: {e}[/{colors.error}]"


async def clean_temp_files(ctx: RunContext[ToolDeps], path: str = ".", dry_run: bool = True) -> str:
    """Clean temporary and cache files."""
    log.debug(f"clean_temp_files called with path: {path}, dry_run: {dry_run}")

    action = "Scanning" if dry_run else "Cleaning"
    if ctx.deps and ctx.deps.display_tool_status:
        await ctx.deps.display_tool_status("Clean", f"{action} temp files in {path}", color="warning")

    try:
        target_path = session.resolve_path(path)
        
        if not target_path.exists() or not target_path.is_dir():
            return f"[{colors.error}]Invalid directory: {path}[/{colors.error}]"
        
        # Patterns for temporary files
        temp_patterns = [
            "*.tmp", "*.temp", "*~", "*.bak", "*.swp", "*.swo",
            ".DS_Store", "Thumbs.db", "desktop.ini",
            "*.log", "*.cache"
        ]
        
        # Directories to clean
        temp_dirs = [
            "__pycache__", ".pytest_cache", ".mypy_cache", 
            ".ruff_cache", "node_modules", ".git/logs",
            ".vscode", "htmlcov", ".coverage"
        ]
        
        found_files = []
        found_dirs = []
        total_size = 0
        
        # Find temp files
        for pattern in temp_patterns:
            for file_path in target_path.rglob(pattern):
                if file_path.is_file():
                    try:
                        size = file_path.stat().st_size
                        found_files.append((file_path, size))
                        total_size += size
                    except (OSError, PermissionError):
                        continue
        
        # Find temp directories
        for dir_name in temp_dirs:
            for dir_path in target_path.rglob(dir_name):
                if dir_path.is_dir():
                    try:
                        # Calculate directory size
                        dir_size = sum(f.stat().st_size for f in dir_path.rglob("*") if f.is_file())
                        found_dirs.append((dir_path, dir_size))
                        total_size += dir_size
                    except (OSError, PermissionError):
                        continue
        
        if not found_files and not found_dirs:
            return f"[{colors.success}]✓[/{colors.success}] No temporary files found in {path}"
        
        result_parts = [
            f"[{colors.primary}]🧹 Temporary Files in [{colors.directory}]{path}[/{colors.directory}][/{colors.primary}]",
            ""
        ]
        
        if found_files:
            result_parts.append(f"[{colors.accent}]Files to clean:[/{colors.accent}]")
            for file_path, size in found_files[:10]:  # Show first 10
                size_kb = size / 1024
                relative_path = file_path.relative_to(target_path)
                result_parts.append(f"   [{colors.file}]{relative_path}[/{colors.file}]: {size_kb:.1f} KB")
            
            if len(found_files) > 10:
                result_parts.append(f"   [{colors.muted}]... and {len(found_files) - 10} more files[/{colors.muted}]")
        
        if found_dirs:
            result_parts.extend([
                "",
                f"[{colors.accent}]Directories to clean:[/{colors.accent}]"
            ])
            for dir_path, size in found_dirs[:5]:  # Show first 5
                size_mb = size / (1024 * 1024)
                relative_path = dir_path.relative_to(target_path)
                result_parts.append(f"   [{colors.directory}]{relative_path}/[/{colors.directory}]: {size_mb:.1f} MB")
        
        total_mb = total_size / (1024 * 1024)
        result_parts.extend([
            "",
            f"[{colors.accent}]Total space to free:[/{colors.accent}] {total_mb:.1f} MB"
        ])
        
        if dry_run:
            result_parts.extend([
                "",
                f"[{colors.info}]This is a dry run. Use dry_run=False to actually delete files.[/{colors.info}]"
            ])
        else:
            # Actually delete files
            deleted_files = 0
            deleted_dirs = 0
            
            for file_path, _ in found_files:
                try:
                    file_path.unlink()
                    deleted_files += 1
                except (OSError, PermissionError):
                    continue
            
            for dir_path, _ in found_dirs:
                try:
                    shutil.rmtree(dir_path)
                    deleted_dirs += 1
                except (OSError, PermissionError):
                    continue
            
            result_parts.extend([
                "",
                f"[{colors.success}]✓[/{colors.success}] Deleted {deleted_files} files and {deleted_dirs} directories",
                f"[{colors.success}]✓[/{colors.success}] Freed {total_mb:.1f} MB of space"
            ])
        
        return "\n".join(result_parts)

    except Exception as e:
        log.error(f"Error cleaning temp files: {e}")
        return f"[{colors.error}]Error cleaning temporary files: {e}[/{colors.error}]"

"""Development workflow and productivity tools."""

import logging
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional

from pydantic_ai import RunContext

from terminus.shared.deps import ToolDeps
from terminus.core.session import session
from terminus.ui.colors import colors

log = logging.getLogger(__name__)


async def package_info(ctx: RunContext[ToolDeps], path: str = ".") -> str:
    """Display package/project information from various manifest files."""
    log.debug(f"package_info called with path: {path}")

    if ctx.deps and ctx.deps.display_tool_status:
        await ctx.deps.display_tool_status("Package", f"Reading project info from {path}", color="config")

    try:
        target_path = session.resolve_path(path)
        
        if not target_path.exists() or not target_path.is_dir():
            return f"[{colors.error}]Invalid directory: {path}[/{colors.error}]"
        
        result_parts = [f"[{colors.primary}] Project Information[/{colors.primary}]", ""]
        
        found_any = False
        
        # Check package.json (Node.js)
        package_json = target_path / "package.json"
        if package_json.exists():
            try:
                with open(package_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                result_parts.extend([
                    f"[{colors.accent}] Node.js Project (package.json):[/{colors.accent}]",
                    f"   [{colors.keyword}]Name:[/{colors.keyword}] {data.get('name', 'Unknown')}",
                    f"   [{colors.keyword}]Version:[/{colors.keyword}] {data.get('version', 'Unknown')}",
                    f"   [{colors.keyword}]Description:[/{colors.keyword}] {data.get('description', 'No description')}",
                ])
                
                if 'scripts' in data:
                    result_parts.append(f"   [{colors.keyword}]Scripts:[/{colors.keyword}] {', '.join(data['scripts'].keys())}")
                
                if 'dependencies' in data:
                    deps = list(data['dependencies'].keys())
                    result_parts.append(f"   [{colors.keyword}]Dependencies:[/{colors.keyword}] {len(deps)} packages")
                
                result_parts.append("")
                found_any = True
                
            except (json.JSONDecodeError, Exception) as e:
                result_parts.extend([
                    f"[{colors.error}]Error reading package.json: {e}[/{colors.error}]",
                    ""
                ])
        
        # Check pyproject.toml (Python)
        pyproject_toml = target_path / "pyproject.toml"
        if pyproject_toml.exists():
            try:
                content = pyproject_toml.read_text(encoding='utf-8')
                result_parts.extend([
                    f"[{colors.accent}] Python Project (pyproject.toml):[/{colors.accent}]",
                    f"   [{colors.keyword}]Found pyproject.toml[/{colors.keyword}]",
                ])
                
                # Basic parsing (not full TOML parser)
                if '[tool.poetry]' in content:
                    result_parts.append(f"   [{colors.keyword}]Build System:[/{colors.keyword}] Poetry")
                elif '[build-system]' in content:
                    result_parts.append(f"   [{colors.keyword}]Build System:[/{colors.keyword}] Modern Python")
                
                result_parts.append("")
                found_any = True
                
            except Exception as e:
                result_parts.extend([
                    f"[{colors.error}]Error reading pyproject.toml: {e}[/{colors.error}]",
                    ""
                ])
        
        # Check setup.py (Python)
        setup_py = target_path / "setup.py"
        if setup_py.exists():
            result_parts.extend([
                f"[{colors.accent}] Python Project (setup.py):[/{colors.accent}]",
                f"   [{colors.keyword}]Legacy Python package[/{colors.keyword}]",
                ""
            ])
            found_any = True
        
        # Check requirements.txt (Python)
        requirements_txt = target_path / "requirements.txt"
        if requirements_txt.exists():
            try:
                lines = requirements_txt.read_text(encoding='utf-8').strip().split('\n')
                packages = [line.strip() for line in lines if line.strip() and not line.startswith('#')]
                result_parts.extend([
                    f"[{colors.accent}] Python Requirements:[/{colors.accent}]",
                    f"   [{colors.keyword}]Packages:[/{colors.keyword}] {len(packages)} requirements",
                    ""
                ])
                found_any = True
                
            except Exception as e:
                result_parts.extend([
                    f"[{colors.error}]Error reading requirements.txt: {e}[/{colors.error}]",
                    ""
                ])
        
        # Check Cargo.toml (Rust)
        cargo_toml = target_path / "Cargo.toml"
        if cargo_toml.exists():
            result_parts.extend([
                f"[{colors.accent}] Rust Project (Cargo.toml):[/{colors.accent}]",
                f"   [{colors.keyword}]Rust package[/{colors.keyword}]",
                ""
            ])
            found_any = True
        
        # Check go.mod (Go)
        go_mod = target_path / "go.mod"
        if go_mod.exists():
            result_parts.extend([
                f"[{colors.accent}] Go Project (go.mod):[/{colors.accent}]",
                f"   [{colors.keyword}]Go module[/{colors.keyword}]",
                ""
            ])
            found_any = True
        
        # Check composer.json (PHP)
        composer_json = target_path / "composer.json"
        if composer_json.exists():
            result_parts.extend([
                f"[{colors.accent}] PHP Project (composer.json):[/{colors.accent}]",
                f"   [{colors.keyword}]PHP package[/{colors.keyword}]",
                ""
            ])
            found_any = True
        
        # Check Gemfile (Ruby)
        gemfile = target_path / "Gemfile"
        if gemfile.exists():
            result_parts.extend([
                f"[{colors.accent}] Ruby Project (Gemfile):[/{colors.accent}]",
                f"   [{colors.keyword}]Ruby application[/{colors.keyword}]",
                ""
            ])
            found_any = True
        
        # Check for common project files
        project_files = []
        for filename in ["README.md", "README.txt", "LICENSE", "Dockerfile", ".gitignore", "Makefile"]:
            if (target_path / filename).exists():
                project_files.append(filename)
        
        if project_files:
            result_parts.extend([
                f"[{colors.accent}] Project Files:[/{colors.accent}]",
                f"   [{colors.keyword}]Found:[/{colors.keyword}] {', '.join(project_files)}",
                ""
            ])
            found_any = True
        
        if not found_any:
            result_parts.append(f"[{colors.muted}]No package manifest files found in {path}[/{colors.muted}]")
        
        # Remove trailing empty line
        if result_parts and result_parts[-1] == "":
            result_parts.pop()
        
        return "\n".join(result_parts)

    except Exception as e:
        log.error(f"Error getting package info: {e}")
        return f"[{colors.error}]Error reading package information: {e}[/{colors.error}]"


async def search_todos(ctx: RunContext[ToolDeps], path: str = ".") -> str:
    """Find TODO, FIXME, and HACK comments in code."""
    log.debug(f"search_todos called with path: {path}")

    if ctx.deps and ctx.deps.display_tool_status:
        await ctx.deps.display_tool_status("Search", f"Finding TODOs in {path}", color="warning")

    try:
        target_path = session.resolve_path(path)
        
        if not target_path.exists():
            return f"[{colors.error}]Path does not exist: {path}[/{colors.error}]"
        
        # Keywords to search for
        keywords = ["TODO", "FIXME", "HACK", "BUG", "NOTE"]
        
        # File extensions to search
        code_extensions = {
            '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.cs', '.php',
            '.rb', '.go', '.rs', '.kt', '.swift', '.dart', '.scala', '.clj',
            '.html', '.css', '.scss', '.sass', '.less', '.vue', '.jsx', '.tsx'
        }
        
        todos = []
        
        if target_path.is_file():
            files_to_search = [target_path]
        else:
            files_to_search = [
                f for f in target_path.rglob("*") 
                if f.is_file() and f.suffix.lower() in code_extensions
            ]
        
        for file_path in files_to_search:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        line_strip = line.strip()
                        for keyword in keywords:
                            if keyword in line_strip.upper():
                                # Extract the todo text
                                keyword_pos = line_strip.upper().find(keyword)
                                todo_text = line_strip[keyword_pos:].strip()
                                
                                # Clean up common comment characters
                                for char in ['#', '//', '/*', '*/', '<!--', '-->', '"""', "'''"]:
                                    todo_text = todo_text.replace(char, '').strip()
                                
                                todos.append({
                                    'file': file_path,
                                    'line': line_num,
                                    'keyword': keyword,
                                    'text': todo_text,
                                    'full_line': line.strip()
                                })
                                break  # Only match first keyword per line
                        
            except (OSError, PermissionError, UnicodeDecodeError):
                continue
        
        if not todos:
            return f"[{colors.success}]✓[/{colors.success}] No TODOs found in {path}"
        
        # Group by keyword
        by_keyword = {}
        for todo in todos:
            keyword = todo['keyword']
            if keyword not in by_keyword:
                by_keyword[keyword] = []
            by_keyword[keyword].append(todo)
        
        result_parts = [
            f"[{colors.primary}]📝 Code TODOs in [{colors.directory}]{path}[/{colors.directory}][/{colors.primary}]",
            ""
        ]
        
        # Display by keyword with different colors
        keyword_colors = {
            'TODO': colors.info,
            'FIXME': colors.warning,
            'HACK': colors.error,
            'BUG': colors.error,
            'NOTE': colors.accent
        }
        
        for keyword in ['TODO', 'FIXME', 'HACK', 'BUG', 'NOTE']:
            if keyword in by_keyword:
                items = by_keyword[keyword]
                color = keyword_colors.get(keyword, colors.muted)
                
                result_parts.append(f"[{color}]{keyword} ({len(items)}):[/{color}]")
                
                for item in items[:5]:  # Show first 5 per category
                    relative_path = item['file'].relative_to(target_path) if target_path.is_dir() else item['file'].name
                    result_parts.append(f"   [{colors.file}]{relative_path}:{item['line']}[/{colors.file}] - {item['text'][:80]}")
                
                if len(items) > 5:
                    result_parts.append(f"   [{colors.muted}]... and {len(items) - 5} more[/{colors.muted}]")
                
                result_parts.append("")
        
        total_count = len(todos)
        result_parts.append(f"[{colors.accent}]Total:[/{colors.accent}] {total_count} items found")
        
        return "\n".join(result_parts)

    except Exception as e:
        log.error(f"Error searching for TODOs: {e}")
        return f"[{colors.error}]Error searching for TODOs: {e}[/{colors.error}]"

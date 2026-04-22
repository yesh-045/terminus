"""Help and documentation tool for all available commands."""

import logging
from typing import Dict, List

from pydantic_ai import RunContext

from ...core.deps import ToolDeps
from terminus.ui.colors import colors

log = logging.getLogger(__name__)


async def list_all_commands(ctx: RunContext[ToolDeps]) -> str:
    """Display comprehensive list of all available commands organized by category."""
    log.debug("list_all_commands called")

    if ctx.deps and ctx.deps.display_tool_status:
        await ctx.deps.display_tool_status("Help", "Gathering command documentation", color="info")

    try:
        commands = {
            "File & Directory Operations": [
                ("read_file", "Read contents of a file", "read_file('path/to/file.py')"),
                ("write_file", "Write content to a file", "write_file('new_file.py', 'print(\"hello\")')"),
                ("update_file", "Update specific content in a file", "update_file('file.py', 'old_code', 'new_code')"),
                ("list_directory", "List directory contents in tree format", "list_directory('.', max_depth=3)"),
                ("change_directory", "Change working directory", "change_directory('/path/to/project')"),
                ("get_current_directory", "Get current working directory", "get_current_directory()"),
            ],
            
            "Search & Discovery": [
                ("find", "Find files by name pattern", "find('.', '*.py')"),
                ("grep", "Search for text patterns in files", "grep('.', 'TODO', case_sensitive=False)"),
                ("find_by_extension", "Find files by extension with gitignore support", "find_by_extension('.', '.py')"),
                ("list_extensions", "List all file extensions in directory", "list_extensions('.')"),
                ("search_todos", "Find TODO, FIXME, HACK comments", "search_todos('.')"),
                ("find_large_files", "Find files larger than specified size", "find_large_files('.', min_size_mb=10)"),
            ],
            
            "Code Analysis": [
                ("summarize_code", "Analyze and summarize code files", "summarize_code('main.py')"),
                ("analyze_project_structure", "Analyze overall project structure", "analyze_project_structure('.')"),
                ("quick_stats", "Get quick statistics about files/directories", "quick_stats('.')"),
            ],
            
            "System Utilities": [
                ("system_info", "Display comprehensive system information", "system_info()"),
                ("clean_temp_files", "Clean temporary and cache files", "clean_temp_files('.', dry_run=True)"),
                ("create_project_template", "Create new project from template", "create_project_template('my_project', 'python')"),
            ],
            
            "Git & Development": [
                ("git_status_enhanced", "Enhanced git status with visual formatting", "git_status_enhanced()"),
                ("git_add", "Add files to git staging area", "git_add('file.py')"),
                ("git_commit", "Commit staged changes", "git_commit('commit message')"),
                ("quick_commit", "Quick git commit with optional add all", "quick_commit('fix bug', add_all=True)"),
                ("package_info", "Display package/project information", "package_info('.')"),
            ],
            
            "Execution & Workflow": [
                ("run_command", "Execute shell commands", "run_command('ls -la')"),
                ("run_in_directory", "Execute command in specific directory", "run_in_directory('/path', 'npm install')"),
            ],
        }

        result_parts = [
            f"[{colors.accent}]Terminus CLI - Complete Command Reference[/{colors.accent}]",
            f"[{colors.text_dim}]Enhanced with session-aware paths, modern UI, and powerful utilities[/{colors.text_dim}]",
            "",
        ]

        for category, command_list in commands.items():
            result_parts.extend([
                f"[{colors.accent}]{category}[/{colors.accent}]",
                ""
            ])
            
            for cmd_name, description, example in command_list:
                result_parts.extend([
                    f"   [{colors.text}]{cmd_name}[/{colors.text}]",
                    f"   [{colors.text_dim}]{description}[/{colors.text_dim}]",
                    f"   [{colors.text_subtle}]Example: {example}[/{colors.text_subtle}]",
                    ""
                ])

        result_parts.extend([
            f"[{colors.accent}]Pro Tips:[/{colors.accent}]",
            f"   • All file paths are relative to current session directory",
            f"   • Use [{colors.text}]get_current_directory()[/{colors.text}] to see current location",
            f"   • Use [{colors.text}]change_directory()[/{colors.text}] to navigate efficiently",
            f"   • Most commands support both relative and absolute paths",
            f"   • File discovery respects .gitignore when available",
            "",
            f"[{colors.accent}]Total Commands Available: {sum(len(cmds) for cmds in commands.values())}[/{colors.accent}]"
        ])

        return "\n".join(result_parts)

    except Exception as e:
        log.error(f"Error listing commands: {e}")
        return f"[{colors.error}]Error generating command list: {e}[/{colors.error}]"


async def command_examples(ctx: RunContext[ToolDeps], category: str = "all") -> str:
    """Show practical examples for different use cases."""
    log.debug(f"command_examples called with category: {category}")

    if ctx.deps and ctx.deps.display_tool_status:
        await ctx.deps.display_tool_status("Help", f"Generating examples for {category}", color="info")

    try:
        examples = {
            "file_operations": {
                "title": "File Operations Examples",
                "scenarios": [
                    ("Reading a configuration file", "read_file('config.json')", "Reads and displays the content of config.json"),
                    ("Creating a new Python script", "write_file('hello.py', 'print(\"Hello, World!\")')", "Creates a new Python file with Hello World"),
                    ("Updating import statements", "update_file('app.py', 'from old_module', 'from new_module')", "Updates import statements in app.py"),
                    ("Exploring project structure", "list_directory('.', max_depth=2)", "Shows directory tree with depth limit"),
                ]
            },
            
            "search_and_analysis": {
                "title": "Search & Analysis Examples", 
                "scenarios": [
                    ("Find all Python files", "find_by_extension('.', '.py')", "Lists all Python files respecting .gitignore"),
                    ("Search for TODO comments", "search_todos('src')", "Finds all TODO, FIXME, HACK comments in src/"),
                    ("Find large files", "find_large_files('.', min_size_mb=5)", "Lists files larger than 5MB"),
                    ("Search for function definitions", "grep('src', 'def ', include_pattern='*.py')", "Finds all function definitions in Python files"),
                    ("Analyze code file", "summarize_code('main.py')", "Provides structural analysis of main.py"),
                ]
            },
            
            "git_workflow": {
                "title": "Git Workflow Examples",
                "scenarios": [
                    ("Check repository status", "git_status_enhanced()", "Shows enhanced git status with colors"),
                    ("Quick commit all changes", "quick_commit('Fix typos', add_all=True)", "Adds all changes and commits with message"),
                    ("Stage specific file", "git_add('src/main.py')", "Stages main.py for commit"),
                    ("View project info", "package_info('.')", "Shows package.json, pyproject.toml, etc. info"),
                ]
            },
            
            "system_management": {
                "title": "System Management Examples",
                "scenarios": [
                    ("Check system info", "system_info()", "Displays comprehensive system information"),
                    ("Clean temp files (dry run)", "clean_temp_files('.', dry_run=True)", "Shows what temp files would be deleted"),
                    ("Create Python project", "create_project_template('my_app', 'python')", "Creates new Python project structure"),
                    ("Get directory stats", "quick_stats('src')", "Shows file counts, sizes, and types in src/"),
                ]
            },
            
            "productivity": {
                "title": "Productivity Workflows",
                "scenarios": [
                    ("Project setup workflow", 
                     "change_directory('/projects') → create_project_template('new_app', 'python') → change_directory('new_app')", 
                     "Complete project creation and navigation"),
                    ("Code review workflow", 
                     "git_status_enhanced() → search_todos('.') → summarize_code('main.py')", 
                     "Review changes, find TODOs, analyze main code"),
                    ("Cleanup workflow", 
                     "find_large_files('.') → clean_temp_files('.', dry_run=True) → clean_temp_files('.', dry_run=False)", 
                     "Find large files, preview cleanup, then execute"),
                    ("Analysis workflow", 
                     "analyze_project_structure('.') → quick_stats('.') → package_info('.')", 
                     "Complete project analysis and information gathering"),
                ]
            }
        }

        if category == "all":
            result_parts = [
                f"[{colors.accent}]Terminus CLI - Practical Examples[/{colors.accent}]",
                f"[{colors.accent}]Real-world usage scenarios and workflows[/{colors.accent}]",
                ""
            ]
            
            for example_key, example_data in examples.items():
                result_parts.extend([
                    f"[{colors.success}]{example_data['title']}[/{colors.success}]",
                    ""
                ])
                
                for scenario, command, description in example_data['scenarios']:
                    result_parts.extend([
                        f"   [{colors.keyword}]{scenario}:[/{colors.keyword}]",
                        f"   [{colors.text}]{command}[/{colors.text}]",
                        f"   [{colors.muted}]{description}[/{colors.muted}]",
                        ""
                    ])
        
        elif category in examples:
            example_data = examples[category]
            result_parts = [
                f"[{colors.accent}]{example_data['title']}[/{colors.accent}]",
                ""
            ]
            
            for scenario, command, description in example_data['scenarios']:
                result_parts.extend([
                    f"[{colors.keyword}]{scenario}:[/{colors.keyword}]",
                    f"[{colors.text}]{command}[/{colors.text}]",
                    f"[{colors.muted}]{description}[/{colors.muted}]",
                    ""
                ])
        
        else:
            available_categories = ", ".join(examples.keys())
            return f"[{colors.error}]Unknown category: {category}[/{colors.error}]\n[{colors.muted}]Available: all, {available_categories}[/{colors.muted}]"

        result_parts.extend([
            f"[{colors.info}]Pro Tips:[/{colors.info}]",
            f"   • Chain commands with → for complex workflows",
            f"   • Use dry_run=True to preview destructive operations", 
            f"   • All paths are session-aware and relative to current directory",
            f"   • Use [{colors.command}]list_all_commands()[/{colors.command}] for complete reference",
        ])

        return "\n".join(result_parts)

    except Exception as e:
        log.error(f"Error generating examples: {e}")
        return f"[{colors.error}]Error generating examples: {e}[/{colors.error}]"


async def quick_help(ctx: RunContext[ToolDeps], topic: str = "overview") -> str:
    """Quick help for specific topics or overview."""
    log.debug(f"quick_help called with topic: {topic}")

    if ctx.deps and ctx.deps.display_tool_status:
        await ctx.deps.display_tool_status("Help", f"Getting help for {topic}", color="info")

    try:
        help_topics = {
            "overview": f"""[{colors.accent}]Terminus CLI - Quick Overview[/{colors.accent}]

[{colors.accent}]Essential Commands:[/{colors.accent}]
• [{colors.command}]list_all_commands()[/{colors.command}] - Complete command reference
• [{colors.command}]command_examples()[/{colors.command}] - Practical usage examples  
• [{colors.command}]get_current_directory()[/{colors.command}] - Show current location
• [{colors.command}]change_directory('path')[/{colors.command}] - Navigate to directory

[{colors.accent}]Key Features:[/{colors.accent}]
• Session-aware file operations (all paths relative to current dir)
• Enhanced Git workflow with visual status
• Code analysis and project insights
• System utilities and cleanup tools

[{colors.accent}]Quick Start:[/{colors.accent}]
1. [{colors.command}]system_info()[/{colors.command}] - Check your environment
2. [{colors.command}]analyze_project_structure('.')[/{colors.command}] - Understand current project
3. [{colors.command}]git_status_enhanced()[/{colors.command}] - Check repository status
4. [{colors.command}]search_todos('.')[/{colors.command}] - Find pending work

[{colors.info}]Use [{colors.command}]quick_help('topic')[/{colors.command}] for specific help topics[/{colors.info}]""",

            "navigation": f"""[{colors.accent}]Navigation & File Operations[/{colors.accent}]

[{colors.accent}]Directory Navigation:[/{colors.accent}]
• [{colors.command}]get_current_directory()[/{colors.command}] - Show current working directory
• [{colors.command}]change_directory('/path/to/project')[/{colors.command}] - Change directory
• [{colors.command}]list_directory('.', max_depth=3)[/{colors.command}] - List directory tree

[{colors.accent}]File Operations:[/{colors.accent}]
• [{colors.command}]read_file('file.py')[/{colors.command}] - Read file contents
• [{colors.command}]write_file('new.py', 'content')[/{colors.command}] - Create/write file
• [{colors.command}]update_file('file.py', 'old', 'new')[/{colors.command}] - Update specific content

[{colors.accent}]Search & Discovery:[/{colors.accent}]
• [{colors.command}]find_by_extension('.', '.py')[/{colors.command}] - Find files by extension
• [{colors.command}]grep('.', 'pattern')[/{colors.command}] - Search text in files
• [{colors.command}]find_large_files('.', min_size_mb=10)[/{colors.command}] - Find large files

[{colors.info}]All paths are relative to current session directory[/{colors.info}]""",

            "git": f"""[{colors.accent}]Git Workflow Commands[/{colors.accent}]

[{colors.accent}]Status & Information:[/{colors.accent}]
• [{colors.command}]git_status_enhanced()[/{colors.command}] - Enhanced visual git status
• [{colors.command}]package_info('.')[/{colors.command}] - Show project package info

[{colors.accent}]Staging & Committing:[/{colors.accent}]
• [{colors.command}]git_add('file.py')[/{colors.command}] - Stage specific file
• [{colors.command}]git_commit('message')[/{colors.command}] - Commit staged changes
• [{colors.command}]quick_commit('message', add_all=True)[/{colors.command}] - Add all and commit

[{colors.accent}]Development Workflow:[/{colors.accent}]
• [{colors.command}]search_todos('.')[/{colors.command}] - Find TODO/FIXME comments
• [{colors.command}]analyze_project_structure('.')[/{colors.command}] - Project overview
• [{colors.command}]summarize_code('file.py')[/{colors.command}] - Analyze specific file

[{colors.info}]Git commands work from current session directory[/{colors.info}]""",

            "analysis": f"""[{colors.accent}]Code Analysis & Insights[/{colors.accent}]

[{colors.accent}]Project Analysis:[/{colors.accent}]
• [{colors.command}]analyze_project_structure('.')[/{colors.command}] - Overall project structure
• [{colors.command}]quick_stats('directory')[/{colors.command}] - File statistics and sizes
• [{colors.command}]package_info('.')[/{colors.command}] - Package manifest information

[{colors.accent}]Code Analysis:[/{colors.accent}]
• [{colors.command}]summarize_code('file.py')[/{colors.command}] - Structural code summary
• [{colors.command}]search_todos('.')[/{colors.command}] - Find TODO/FIXME/HACK comments
• [{colors.command}]list_extensions('.')[/{colors.command}] - List all file types in project

[{colors.accent}]Search Capabilities:[/{colors.accent}]
• [{colors.command}]grep('.', 'pattern', case_sensitive=False)[/{colors.command}] - Text search
• [{colors.command}]find_by_extension('.', '.py')[/{colors.command}] - Extension-based search
• [{colors.command}]find_large_files('.', min_size_mb=5)[/{colors.command}] - Size-based search

[{colors.info}]Analysis respects .gitignore and excludes common build directories[/{colors.info}]""",

        }

        if topic in help_topics:
            return help_topics[topic]
        else:
            available_topics = ", ".join(help_topics.keys())
            return f"[{colors.error}]Unknown help topic: {topic}[/{colors.error}]\n[{colors.muted}]Available topics: {available_topics}[/{colors.muted}]"

    except Exception as e:
        log.error(f"Error getting help: {e}")
        return f"[{colors.error}]Error getting help: {e}[/{colors.error}]"

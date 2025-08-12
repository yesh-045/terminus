# Terminus CLI

An advanced terminal automation system powered by AI for intelligent workflow automation, multi-model support, and comprehensive project management.

## Overview

Terminus CLI is a sophisticated command-line tool that transforms terminal interactions through AI-powered automation. It serves as an intelligent assistant capable of understanding natural language commands and executing complex multi-step operations across diverse domains including development workflows, system administration, and productivity management.

Built with a modular architecture, Terminus CLI features:
- **Multi-Model AI Support**: Google Gemini and local Ollama model integration
- **Terminal-native Design**: Compatible with any shell environment and operating system
- **Language-agnostic Processing**: Handles any file type, project structure, or technology stack
- **Persistent Context Management**: Maintains conversation history and project understanding across sessions
- **Comprehensive Safety Framework**: Multi-layer confirmation system for destructive operations
- **Extensible Tool Architecture**: 40+ specialized tools organized into logical categories

## Core Capabilities

### AI-Powered Automation
- **Natural Language Processing**: Converts plain English descriptions into executable workflows
- **Intelligent Planning**: Breaks down complex requests into optimized tool sequences
- **Context-Aware Decision Making**: Leverages conversation history and project state for informed responses
- **Multi-Step Orchestration**: Coordinates complex operations across multiple tools and systems

### Development Workflow Integration
- **Git Operations**: Enhanced version control with intelligent staging, committing, and status reporting
- **Code Analysis**: Automated code review, documentation generation, and refactoring suggestions
- **Project Scaffolding**: Template-based project creation with best practice implementations
- **Testing Integration**: Automated test discovery, execution, and failure analysis

### System Administration
- **File System Management**: Intelligent file operations with pattern matching and bulk processing
- **System Monitoring**: Resource usage analysis, performance metrics, and health diagnostics
- **Cleanup Operations**: Automated temporary file removal and disk space optimization
- **Configuration Management**: Environment setup and configuration validation

### Productivity Tools
- **Email Management**: Gmail integration for reading, searching, and drafting responses
- **Calendar Operations**: Event scheduling, availability checking, and focus time blocking
- **Documentation Generation**: Automated README creation and project documentation
- **Task Automation**: Custom workflow creation for repetitive operations

## Installation

### Prerequisites
- **Python 3.10 or higher**: Modern Python with asyncio support
- **Git**: Version control system (optional but recommended)
- **API Access**: Google Gemini API key for cloud AI models
- **Local Models**: Ollama installation for offline AI capabilities (optional)

### Installation Methods

#### Option 1: Using pipx (Recommended)
Pipx provides isolated Python package installation with global command availability:

```bash
# Install pipx if not present
pip install pipx

# Install Terminus CLI globally
pipx install terminus-cli
```

#### Option 2: Using pip
Standard pip installation for direct Python environment integration:

```bash
pip install terminus-cli
```

#### Option 3: Development Installation
For contributors and advanced users requiring source access:

```bash
git clone https://github.com/yesh-045/terminus-cli.git
cd terminus-cli
python -m venv env

# Windows activation
env\Scripts\activate

# macOS/Linux activation
source env/bin/activate

# Install in development mode
pip install -e .
```

### Initial Configuration

First-time setup requires API configuration:

```bash
# Launch Terminus CLI
terminus

# Follow interactive setup wizard for:
# - Google Gemini API key configuration
# - Default model selection
# - Security preference settings
```

Configuration is stored in `~/.config/terminus.json` and can be manually edited:

```json
{
  "default_model": "google-gla:gemini-2.0-flash-exp",
  "env": {
    "GEMINI_API_KEY": "your-api-key-here"
  },
  "models": {
    "google": {
      "api_key": "your-api-key-here"
    },
    "ollama": {
      "base_url": "http://localhost:11434/v1",
      "enabled": true
    }
  }
}
```

## Quick Start Guide

### Basic Usage
Launch Terminus CLI and begin natural language interaction:

```bash
terminus
```

### Example Workflows

#### Project Analysis and Management
```
> analyze this project structure and suggest improvements
> find all TODO comments and create a comprehensive task list
> generate a detailed README file for this project
> identify the largest files consuming disk space
```

#### Development Operations
```
> run the test suite and analyze any failures
> create a new Python project with modern tooling setup
> review the codebase and suggest refactoring opportunities
> stage all modified files and commit with descriptive message
```

#### File System Management
```
> create incremental backups of all Python files to backup directory
> clean up temporary files and cache directories recursively
> organize image files by creation date into yearly folders
> find and remove duplicate files in the Downloads directory
```

#### System Administration
```
> check comprehensive system health including disk usage
> update all git repositories in current directory tree
> analyze log files for error patterns and anomalies
> optimize directory structure for better organization
```

#### Email and Calendar Integration
```
> show my 10 most recent unread emails with priority indicators
> summarize the email thread about "Project Milestone Review"
> draft a professional reply thanking the team for their contributions
> schedule a 90-minute planning meeting for next Tuesday at 2pm
> check my availability for Thursday afternoon between 1-5pm
> block 3 hours of focused development time tomorrow morning
```

### Session Management
Terminus CLI maintains persistent context across conversations:

```
> save current session for later continuation
> load previous session from yesterday's project work
> clear conversation history and start fresh
> show session statistics and message count
```


## Command Interface

### Built-in Commands
Terminus CLI provides essential session management commands:

- **`/help`** - Display comprehensive help documentation with tool overview
- **`/yolo`** - Toggle confirmation prompts (WARNING: auto-approves destructive operations)
- **`/clear`** - Clear conversation history and reset session context
- **`/dump`** - Show detailed message history for debugging and analysis
- **`/sessions --list`** - List all saved sessions with metadata
- **`/sessions --save [name]`** - Save current session with optional name
- **`/sessions --load <name>`** - Load previously saved session
- **`/sessions --clear`** - Delete all saved sessions
- **`exit`** - Gracefully exit the application

### Multi-Model Support
Switch between AI models for different use cases:

```
> switch to local ollama model for offline work
> use google gemini for complex analysis tasks
> show available models and their capabilities
```

### Natural Language Interface
Primary interaction through conversational commands:

- **"what tools are available and how do I use them?"** - Complete tool reference
- **"analyze this codebase and suggest architectural improvements"** - Project analysis
- **"find all large files and help me optimize storage usage"** - System cleanup
- **"set up a new Python project with testing and CI/CD pipeline"** - Project scaffolding
- **"backup critical files to cloud storage with encryption"** - File management
- **"find and resolve all TODO comments in the codebase"** - Code maintenance
- **"optimize this directory structure for better organization"** - File organization

## Available Tools (40 Total)

Terminus CLI provides a comprehensive suite of specialized tools organized into logical categories:

### File System Operations (10 tools)
**Core file and directory management capabilities**

| Tool | Function | Safety Level |
|------|----------|--------------|
| `read_file` | Read and analyze file contents with syntax highlighting | Safe |
| `write_file` | Create new files with intelligent content generation | Confirmation Required |
| `update_file` | Modify existing files with precision editing | Confirmation Required |
| `list_directory` | Browse directories with enhanced tree visualization | Safe |
| `find` | Search files by name patterns with advanced filtering | Safe |
| `grep` | Search text content across files with context | Safe |
| `find_by_extension` | Locate files by type with .gitignore awareness | Safe |
| `list_extensions` | Catalog all file types present in project | Safe |
| `change_directory` | Navigate with session-aware path management | Safe |
| `get_current_directory` | Display current working directory | Safe |

### Development Workflow (8 tools)
**Git operations and project management**

| Tool | Function | Safety Level |
|------|----------|--------------|
| `git_add` | Stage files with intelligent selection preview | Confirmation Required |
| `git_commit` | Commit changes with automated message generation | Confirmation Required |
| `git_status_enhanced` | Enhanced visual git status with change summary | Safe |
| `quick_commit` | Streamlined commit workflow for rapid iteration | Confirmation Required |
| `summarize_code` | Analyze and explain code structure and patterns | Safe |
| `analyze_project_structure` | Comprehensive project architecture overview | Safe |
| `search_todos` | Locate TODO, FIXME, and HACK comments | Safe |
| `package_info` | Display project metadata and dependencies | Safe |

### System Utilities (5 tools)
**System administration and resource management**

| Tool | Function | Safety Level |
|------|----------|--------------|
| `run_command` | Execute shell commands with safety validation | Confirmation Required |
| `run_in_directory` | Execute commands in specific directory contexts | Confirmation Required |
| `system_info` | Comprehensive system information and diagnostics | Safe |
| `find_large_files` | Locate large files for storage optimization | Safe |
| `clean_temp_files` | Remove temporary and cache files safely | Confirmation Required |

### Analysis and Discovery (4 tools)
**Project analysis and code intelligence**

| Tool | Function | Safety Level |
|------|----------|--------------|
| `quick_stats` | File and directory statistics with metrics | Safe |
| `create_project_template` | Generate project scaffolding with best practices | Confirmation Required |
| `generate_project_readme` | AI-powered README generation from codebase | Safe |
| `analyze_code_for_refactoring` | Code quality analysis with improvement suggestions | Safe |

### Help and Documentation (3 tools)
**User assistance and guidance**

| Tool | Function | Safety Level |
|------|----------|--------------|
| `list_all_commands` | Complete tool reference with usage examples | Safe |
| `command_examples` | Practical usage patterns and workflows | Safe |
| `quick_help` | Context-specific help and guidance | Safe |

### Gmail Integration (4 tools)
**Email management and automation**

| Tool | Function | Safety Level |
|------|----------|--------------|
| `list_unread` | Fetch and display unread emails with metadata | Safe |
| `summary` | Generate AI-powered email content summaries | Safe |
| `generate_draft` | Create email drafts from natural language input | Confirmation Required |
| `search_email` | Search emails by sender, subject, or content | Safe |

### Calendar Operations (3 tools)
**Schedule management and time blocking**

| Tool | Function | Safety Level |
|------|----------|--------------|
| `add_event` | Schedule new calendar events with smart parsing | Confirmation Required |
| `check_availability` | Check for scheduling conflicts and free time | Safe |
| `block_focus` | Create focus time blocks for productive work | Confirmation Required |

### Google API Management (3 tools)
**Authentication and service configuration**

| Tool | Function | Safety Level |
|------|----------|--------------|
| `google_auth_status` | Check Google API authentication status | Safe |
| `google_auth_setup` | Configure Google API credentials and OAuth flow | Confirmation Required |
| `google_auth_revoke` | Revoke Google API access and clear credentials | Confirmation Required |  


## Multi-Model AI Support

Terminus CLI supports multiple AI providers for different use cases and requirements:

### Google Gemini Integration
- **Model**: Gemini 2.0 Flash Experimental
- **Strengths**: Advanced reasoning, code analysis, complex planning
- **Use Cases**: Complex development tasks, comprehensive analysis, multi-step workflows
- **Requirements**: Google AI API key

### Ollama Local Models
- **Offline Operation**: Complete functionality without internet connectivity
- **Privacy**: All processing occurs locally on your machine
- **Supported Models**: Qwen, Llama, CodeLlama, and other Ollama-compatible models
- **Requirements**: Ollama installation and model downloads

### Model Selection
```
> switch to google gemini for complex analysis
> use local ollama qwen model for offline work
> show available models and capabilities
> set default model for this session
```

## Advanced Features

### Session Persistence
- **Auto-save**: Automatic session preservation across application restarts
- **Named Sessions**: Save and load specific project contexts
- **History Management**: Comprehensive conversation history with search
- **State Recovery**: Restore working directory and preferences

### Safety Framework
- **Multi-layer Confirmation**: Preview and approve destructive operations
- **Command Whitelisting**: Predefined safe shell commands
- **User Override**: Flexible safety configuration per tool
- **Error Recovery**: Graceful handling of failures with cleanup

### Project Intelligence
- **Context Awareness**: Understands project structure and conventions
- **Technology Detection**: Automatically identifies languages and frameworks
- **Best Practice Enforcement**: Suggests improvements following industry standards
- **Documentation Generation**: Creates comprehensive project documentation

### Integration Ecosystem
- **Git Workflow**: Enhanced version control with intelligent operations
- **Google Services**: Gmail and Calendar integration for productivity
- **Shell Environment**: Native terminal integration across platforms
- **File System**: Advanced file operations with pattern matching

## System Requirements

### Core Dependencies
- **Python 3.10+**: Modern Python runtime with full asyncio support
- **Terminal Environment**: Compatible with PowerShell, Command Prompt, Bash, Zsh
- **Network Access**: Required for cloud AI models and Google API integration
- **Disk Space**: Minimal footprint with optional local model storage

### Optional Components
- **Git**: Version control operations and repository management
- **Ollama**: Local AI model runtime for offline functionality
- **Google APIs**: Enhanced email and calendar integration
- **Text Editors**: Integration with VS Code, Vim, and other editors

## Configuration Management

### Configuration Location
Configuration files are stored in the user's home directory:
- **Windows**: `%USERPROFILE%\.config\terminus.json`
- **macOS/Linux**: `~/.config/terminus.json`

### Configuration Structure
```json
{
  "default_model": "google-gla:gemini-2.0-flash-exp",
  "env": {
    "GEMINI_API_KEY": "your-api-key-here"
  },
  "models": {
    "google": {
      "api_key": "your-google-api-key",
      "project_id": "your-project-id"
    },
    "ollama": {
      "base_url": "http://localhost:11434/v1",
      "enabled": true,
      "default_model": "qwen"
    }
  },
  "settings": {
    "confirmation_enabled": true,
    "auto_save_sessions": true,
    "max_session_history": 1000,
    "allowed_commands": [
      "ls", "cat", "grep", "find", "pwd", "echo", "which",
      "head", "tail", "wc", "sort", "uniq", "diff", "tree"
    ]
  }
}
```

### Manual Configuration
Edit configuration directly using your preferred text editor:

```bash
# Windows
notepad "%USERPROFILE%\.config\terminus.json"

# macOS/Linux
nano ~/.config/terminus.json
```

## Architecture Overview

Terminus CLI is built with a clean, modular architecture designed for extensibility and maintainability:

### Core Components
- **Agent System**: Single intelligent agent with multi-model support
- **Tool Framework**: 40+ specialized tools organized into logical categories
- **Session Management**: Persistent context and state management
- **Safety Framework**: Multi-layer confirmation and validation system
- **UI System**: Rich terminal interface with consistent styling

### Project Structure
```
terminus-cli/
├── src/terminus/
│   ├── core/                    # Core business logic
│   │   ├── agent.py            # AI agent orchestration
│   │   ├── session.py          # Session management
│   │   └── persistence.py      # Data persistence
│   ├── infrastructure/         # External integrations
│   │   ├── config/            # Configuration management
│   │   └── models/            # AI model providers
│   ├── tools/                 # Tool implementations
│   │   ├── filesystem/        # File operations
│   │   ├── development/       # Development workflow
│   │   ├── system/           # System utilities
│   │   ├── integrations/     # External service integration
│   │   └── help/             # Help and documentation
│   ├── interface/cli/         # Command-line interface
│   │   ├── __main__.py       # Application entry point
│   │   ├── commands.py       # Built-in commands
│   │   └── repl.py          # Interactive shell
│   └── shared/               # Shared utilities
│       ├── constants.py      # Application constants
│       └── deps.py          # Dependency injection
```

### Design Principles
- **Single Responsibility**: Each tool serves a specific, well-defined purpose
- **Composability**: Tools can be combined for complex workflows
- **Safety First**: Destructive operations require explicit confirmation
- **Context Awareness**: Maintains project and session understanding
- **Extensibility**: New tools and models can be easily integrated

## Contributing

### Development Setup
```bash
git clone https://github.com/yesh-045/terminus-cli.git
cd terminus-cli
python -m venv env
source env/bin/activate  # or env\Scripts\activate on Windows
pip install -e .
```

### Adding New Tools
1. Create tool function in appropriate category directory
2. Register tool in `tools/wrapper.py`
3. Add comprehensive docstring for AI agent understanding
4. Include appropriate safety level and confirmation requirements
5. Add unit tests and documentation

### Code Standards
- Type hints for all function parameters and return values
- Comprehensive docstrings following Google style
- Error handling with graceful degradation
- Safety considerations for destructive operations

## Support and Documentation

### Getting Help
- Use `/help` command within the application for comprehensive documentation
- Visit the GitHub repository for issue reporting and feature requests
- Review the ARCHITECTURE.md file for detailed technical documentation

### Troubleshooting
- Configuration issues: Verify API keys and model availability
- Performance problems: Check system resources and network connectivity
- Tool failures: Review error logs and safety confirmations
- Model switching: Ensure proper model installation and configuration

## License

MIT License - see LICENSE file for details.

## Acknowledgments

Built with modern Python technologies including:
- **pydantic-ai**: Advanced AI agent framework
- **Rich**: Beautiful terminal interfaces and formatting
- **Typer**: Modern CLI application framework
- **Google AI**: Gemini model integration
- **Ollama**: Local AI model runtime

# Terminus CLI

An advanced terminal automation system powered by AI for intelligent workflow automation, multi-model support, and comprehensive project management.

## Overview

Terminus CLI is a command-line AI assistant that helps automate common tasks through natural language commands. It provides file operations, system utilities, and productivity tools while maintaining safety through confirmation prompts for destructive operations.

Key features:
- **Multi-Model AI Support**: Google Gemini and local Ollama model integration
- **Terminal-native Design**: Works in any shell environment
- **File Operations**: Read, write, search, and organize files safely
- **Session Management**: Maintains conversation history across sessions
- **Safety Framework**: Confirmation prompts for destructive operations
- **Extensible Tools**: 35+ specialized tools for common tasks

## Core Capabilities

### File Operations
- **File Management**: Read, write, and modify files with safety confirmations
- **Search and Discovery**: Find files by name, content, or type across directories
- **Directory Navigation**: Browse and organize directory structures
- **Content Analysis**: Analyze code structure and generate documentation

### System Utilities
- **Command Execution**: Run shell commands with safety validation
- **System Information**: Display system metrics and resource usage
- **File Cleanup**: Remove temporary files and optimize storage usage
- **Process Management**: Monitor and manage running processes

### Productivity Tools
- **Email Integration**: Gmail operations for reading and managing messages
- **Calendar Management**: Schedule events and check availability
- **Project Documentation**: Generate README files and project documentation
- **Code Analysis**: Review code structure and suggest improvements

## Installation

### Prerequisites
- **Python 3.10 or higher**: Modern Python with asyncio support
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
# Download the source code
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
Start Terminus CLI and begin with simple commands:

```bash
terminus
```

### Example Commands

#### File Operations
```
> read the config file and show me its contents
> find all Python files in this directory
> create a backup copy of important.txt
> show me all files larger than 10MB
```

#### System Tasks
```
> check system disk usage and memory
> clean up temporary files safely
> show me what processes are using the most CPU
> list all installed software packages
```

#### Productivity
```
> check my recent unread emails
> schedule a meeting for tomorrow at 2pm
> generate documentation for this project
> analyze this code file for potential improvements
```

### Session Management
```
> save this session for later
> load my previous work session
> clear conversation history
> show session information
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

## Available Tools

Terminus CLI includes these built-in capabilities:

### File Management
- Read and write text files
- Create directory structures  
- Search and filter files
- File compression and archiving

### System Operations
- Monitor system resources
- Manage processes
- Check disk usage
- Clean temporary files

### Communication
- Send and receive emails
- Calendar operations
- Meeting scheduling

### Text Processing
- Generate documentation
- Analyze and summarize content
- Format and convert text
- Search within files

### Network Operations
- Web content retrieval
- Download files
- Check connectivity

### Development Tools
- Code analysis
- Project structure review
- Test execution
- Documentation generation

## Tool Categories

### Essential Operations
Core functionality for daily tasks:
- File operations (create, read, write, delete)
- Directory management
- System monitoring
- Process management

### Safety Features
Built-in safety mechanisms:
- Confirmation prompts for destructive operations
- Backup creation before modifications
- Operation logging and audit trails
- Safe mode for automated operations
## Safety and Security

### Operation Safety
- Confirmation prompts for file modifications
- Backup creation before destructive operations
- Operation logging for audit trails
- Safe mode for automated tasks

### Privacy Protection
- Local processing when possible
- Secure credential storage
- No data sharing without consent
- Session data encryption

## Technical Features

### Multi-Model Support
- Google Gemini integration
- Local Ollama support
- Model switching capabilities
- Fallback model handling

### Session Management
- Persistent conversation context
- Save and restore sessions
- Message history management
- Cross-session continuity

### Smart Execution
- Intelligent tool selection
- Context-aware responses
- Error handling and recovery
- Performance optimization

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
## Configuration

Terminus CLI stores configuration in `~/.config/terminus.json`:

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

### Setup Requirements
- **Python 3.10+** 
- **API Key**: Google Gemini API key for cloud models
- **Optional**: Ollama for local models

## Support

### Getting Help
- Use `/help` command within the application
- Visit the project documentation
- Check the issues section for common problems

### Contributing
Contributions welcome! Please check the contribution guidelines before submitting pull requests.

### License
This project is licensed under the MIT License.

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
# Clone or download the project
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
- Check the issues section for common problems
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

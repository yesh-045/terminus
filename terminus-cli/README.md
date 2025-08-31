# Terminus CLI v0.1.0

A lightweight terminal automation system with local AI agents.

**Latest Update (v0.1.0):** Modular architecture refactoring for improved maintainability and extensibility.

## What it does

terminus is a powerful CLI tool that brings AI-powered automation to your terminal. It's designed to handle **any** repetitive task - from file operations and system administration to development workflows and data processing. Think of it as your intelligent terminal assistant that can understand natural language and execute complex multi-step operations.

Unlike complex IDE extensions or heavyweight automation tools, terminus is:
- **Terminal-native**: Works in any shell, on any system
- **Language-agnostic**: Handles any file type or project structure  
- **Context-aware**: Remembers your workflow and adapts to your project
- **Transparent**: Shows you exactly what it's doing with confirmation prompts

## Core Features

- ** Natural Language Interface**: Describe what you want in plain English
- ** Intelligent File Operations**: Read, write, organize, and transform files with AI assistance
- ** Shell Integration**: Execute commands with smart confirmation and error handling
- ** Session Memory**: Maintains context across conversations for complex workflows
- ** Project Understanding**: Analyzes codebases, detects patterns, and suggests improvements
- ** Safety First**: Confirmation prompts protect against destructive operations
- ** Git Integration**: Smart version control with enhanced status and commit workflows
- ** Task Automation**: Handles repetitive tasks from backups to deployments
- ** Development Tools**: Project scaffolding, testing, and code analysis

## Installation

### Option 1: Using pipx (Recommended)
Install pipx if you don't have it:
```bash
pip install pipx
```

Then install terminus globally:
```bash
pipx install terminus-cli
```

This installs terminus in an isolated environment while making it available globally from any terminal.

### Option 1: Using pip
```bash
pip install terminus-cli
```

### Option 3: Development Installation
For development or local installation:
```bash
git clone <repository-url>
cd terminus-cli
python -m venv env
# On Windows:
env\Scripts\activate
# On macOS/Linux:
source env/bin/activate
pip install .
```

## Quick Start

1. **First-time setup**: Run terminus and configure your API key:
```bash
terminus
```

2. **Start automating anything**:
```
# 🔍 Project Analysis & Discovery
> analyze this project structure and suggest improvements
> find all TODO comments and create a task list
> what are the largest files taking up space?

# 📁 File & Directory Management  
> create a backup of all .py files to /backup folder
> clean up temporary files and cache directories
> organize these photos by date into folders

# 🚀 Development Workflows
> run the tests and fix any failures you find
> create a comprehensive README for this project
> set up a new Python project with proper structure

# 🔧 System Administration
> check system health and disk usage
> find and remove duplicate files in Downloads
> update all git repositories in this directory

# 📊 Data Processing
> convert all .csv files to .json format
> generate a report of file types and sizes
> merge all markdown files into a single document

# 📧 Email & Calendar Management
> show me my 10 most recent unread emails
> summarize the email with subject "Project Update"
> draft a reply to John thanking him for the update
> schedule a 1-hour meeting with the team for tomorrow at 2pm
> check if I'm free next Tuesday between 10am-12pm
> block 2 hours of focus time for deep work tomorrow morning
```


## Available Commands

### Built-in Commands
- `/help` - Show comprehensive help guide with AI tools overview
- `/yolo` - Toggle tool confirmation prompts (DANGEROUS: auto-approves actions)
- `/clear` - Clear conversation history and start fresh
- `/dump` - Show detailed message history for debugging
- `exit` - Exit the application gracefully

### AI-Powered Natural Language Interface
Instead of memorizing commands, just describe what you want:
- **"what tools are available?"** → Complete command reference
- **"analyze this project and suggest improvements"** → Project structure analysis
- **"find all large files and help me clean up"** → System cleanup utilities
- **"set up a new Python project with tests"** → Project scaffolding
- **"backup all important files to cloud storage"** → File management automation
- **"find and fix all TODO comments"** → Code maintenance workflows
- **"optimize this directory structure"** → File organization assistance


## Project Structure (v0.1.0)

Terminus now features a modular architecture:

```
src/terminus/
├── core/               # Core components
│   ├── agent.py       # AI agent orchestration
│   ├── repl.py        # Main interaction loop
│   ├── session.py     # State management
│   └── deps.py        # Tool dependencies
├── tools/             # Tool implementations
│   ├── file_ops/      # File operations
│   ├── dev_tools/     # Development tools
│   ├── analysis/      # Code analysis
│   └── integrations/  # External integrations
├── infrastructure/    # Infrastructure components
├── ui/                # Rich UI components
└── utils/             # Utility modules
```

## Requirements

- **Python 3.10+** - Modern Python with async support
- **Google Gemini API key** - For AI-powered automation
- **Git** (optional) - For version control operations
- **Terminal/Shell** - Works with PowerShell, CMD, Bash, Zsh

## Configuration

After installation, terminus will prompt you to configure your API key on first run. The configuration is stored in `~/.config/terminus.json`.

### Manual Configuration
Edit your config file directly,

To edit : notepad "$env:USERPROFILE\.config\terminus.json" and manually update the api key
```json
{
  "default_model": "google-gla:gemini-2.0-flash-exp",
  "env": {
    "GEMINI_API_KEY": "your-api-key-here"
  }
}
```




## License

MIT

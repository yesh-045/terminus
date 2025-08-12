# Terminus

A lightweight terminal automation system with local AI agents.

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

### Option 2: Using pip
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

## Enhanced Tools Available (38 total)

### 📁 File & Directory Operations
1. **read_file** - Read and analyze file contents  
2. **write_file** - Create new files with content  
3. **update_file** - Modify existing files intelligently  
4. **list_directory** - Browse directory structures  
5. **change_directory** - Navigate with session awareness  
6. **get_current_directory** - Show current working directory  
7. **find** - Search files by name patterns  
8. **grep** - Search text content across files  
9. **find_by_extension** - Find files by type (.gitignore aware)  
10. **list_extensions** - Catalog all file types in project  

### 🔍 Analysis & Discovery
11. **summarize_code** - Analyze and explain code files  
12. **analyze_project_structure** - Complete project overview  
13. **search_todos** - Find TODO/FIXME/HACK comments  
14. **package_info** - Display project metadata  
15. **quick_stats** - File/directory statistics  

### 🚀 Development Workflow
16. **git_add** - Stage files for commit  
17. **git_commit** - Commit staged changes  
18. **git_status_enhanced** - Enhanced visual git status  
19. **quick_commit** - Fast git commit workflow  
20. **create_project_template** - Generate project scaffolding  

### 🔧 System & Automation
21. **run_command** - Execute shell commands safely  
22. **run_in_directory** - Execute commands in specific directories  
23. **system_info** - Comprehensive system information  
24. **find_large_files** - Locate large files for cleanup  
25. **clean_temp_files** - Clean temporary and cache files  

### 📚 Help & Documentation
26. **list_all_commands** - Complete command reference  
27. **command_examples** - Practical usage examples  
28. **quick_help** - Context-specific help and guidance  

### 📧 Gmail Operations
29. **list_unread** - Fetch and display unread emails
30. **summary** - Generate AI summaries of email content
31. **generate_draft** - Create email drafts from natural language
32. **search_email** - Search emails by sender, subject, or content

### 📅 Calendar Operations  
33. **add_event** - Schedule new calendar events
34. **check_availability** - Check for scheduling conflicts
35. **block_focus** - Create focus time blocks in calendar

### 🔧 Google API Setup
36. **google_auth_status** - Check Google API authentication status
37. **google_auth_setup** - Set up Google API credentials and OAuth
38. **google_auth_revoke** - Revoke Google API access  


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

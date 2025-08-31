# Terminus CLI - Complete Architecture Documentation

## Table of Contents
- [Overview](#overview)
- [Core Architecture](#core-architecture)
- [Agent System](#agent-system)
- [Tool System](#tool-system)
- [UI System](#ui-system)
- [Request Processing Flow](#request-processing-flow)
- [Configuration System](#configuration-system)
- [Safety & Security](#safety--security)
- [Project Structure](#project-structure)
- [Key Design Principles](#key-design-principles)
- [Development Guide](#development-guide)

## Overview

**Terminus** is a lightweight terminal automation system powered by AI (specifically Google Gemini 2.0 Flash). It's designed as an intelligent CLI assistant that understands natural language commands and executes complex multi-step operations through a collection of 28 specialized tools.

## Design Philosophy & Tool Selection Flow

### Design Philosophy

- **Action-Oriented**: The system is designed to bias toward action—when in doubt, it takes steps to fulfill the user's intent, not just explain what it could do.
- **Minimalism**: Output is concise and focused on results, not narration.
- **Safety**: Destructive or potentially risky actions always require explicit user confirmation, with clear previews.
- **Extensibility**: New tools can be added easily, and the agent will automatically consider them for relevant tasks.
- **Composability**: Tools are designed to be chained together for complex workflows, with the agent orchestrating multi-step plans.

### Agent Tool Selection & Execution Flow

#### How Natural Language Input is Interpreted and Tool Selection Happens

1. **LLM as the Brain**
   - Terminus uses a large language model (LLM, e.g., Google Gemini) as the core reasoning engine.
   - The LLM receives the user's raw natural language input, the current session context, and a detailed system prompt.

2. **System Prompt Engineering**
   - The system prompt (`prompts/system.txt`) describes all available tools, their purposes, and usage patterns.
   - It instructs the LLM to always prefer specialized tools, to read before writing, and to chain tools for complex tasks.

3. **Tool Metadata Exposure**
   - Each tool is registered with a docstring that describes its function, parameters, and safety level.
   - The LLM sees these docstrings and uses them to match user intent to the right tool(s).

4. **Intent Parsing**
   - The LLM parses the user's request to extract actionable intent (e.g., "find all TODOs" → search for comments, "summarize code" → analyze files).
   - It identifies required parameters (file patterns, search terms, etc.) from the input.

5. **Tool Selection Logic**
   - The LLM matches the parsed intent to the most relevant tool(s) by comparing the request to tool docstrings and parameter types.
   - If a request requires multiple steps, the LLM plans a sequence (e.g., find files → read files → update report).
   - If no specialized tool matches, it falls back to `run_command` for generic shell execution.

6. **Dynamic Planning**
   - The LLM can adapt its plan based on intermediate results (e.g., if no TODOs are found, it may skip report generation).
   - It can ask for clarification if the request is ambiguous.

7. **Execution and Feedback Loop**
   - The agent executes the selected tool(s), passing results back to the LLM for further reasoning if needed.
   - The LLM can generate follow-up tool calls or finalize the response based on tool outputs.

**Example:**

> User: "List all Python files with TODO comments and summarize them."

- LLM interprets: Find all `.py` files → search for TODOs → summarize results.
- Tool chain: `find` (pattern: `*.py`) → `grep` or `search_todos` → synthesize summary.
- The LLM generates the tool calls, interprets results, and produces a concise summary for the user.

1. **Intent Recognition**
   - The agent parses the user's natural language input to determine intent (action, information, or hybrid).
   - It uses the system prompt and conversation context to disambiguate requests.

2. **Tool Matching**
   - The agent reviews all registered tools, considering their docstrings, parameter types, and safety level.
   - It prefers specialized tools (e.g., `read_file`, `find`, `grep`) over generic shell execution (`run_command`).
   - If multiple tools could apply, it may chain them (e.g., `find` → `read_file` → `update_file`).

3. **Planning & Routing**
   - For complex requests, the agent plans a sequence of tool invocations, routing outputs from one tool as inputs to the next.
   - The plan is dynamically adjusted based on intermediate results and user confirmations.

4. **Confirmation & Preview**
   - Before executing any destructive or irreversible action, the agent presents a preview panel and asks for confirmation.
   - The user can approve, deny, or "always allow" specific tools for the session.

5. **Execution & Feedback**
   - The agent executes the selected tool(s), displaying real-time status and results in the terminal UI.
   - Errors are handled gracefully, with actionable messages and logs if needed.

6. **Session Update**
   - The session state (messages, working directory, allowed commands, etc.) is updated after each operation.
   - The agent uses this context for future requests, enabling context-aware automation.

### Example: How a Request is Handled

> User: "Find all TODOs in Python files and create a summary report."

1. Agent uses `find` to locate all `.py` files.
2. Agent uses `grep` or `search_todos` to extract TODO comments from those files.
3. Agent uses `write_file` or `update_file` to create or update a summary report.
4. If file creation is involved, a confirmation panel is shown before writing.
5. Results are displayed in a concise, actionable format.

### What Makes Terminus Special

- **Terminal-native**: Works in any shell, on any system
- **Language-agnostic**: Handles any file type or project structure  
- **Context-aware**: Remembers workflow and adapts to your project
- **Transparent**: Shows exactly what it's doing with confirmation prompts
- **Single Agent Design**: One intelligent agent with many tools vs multiple specialized agents

## Core Architecture

### Modular Architecture (v0.2.0 Update)

Terminus has been restructured with a modular architecture for better maintainability and extensibility:

```
src/terminus/
├── core/               # Core components (NEW)
│   ├── agent.py       # AI agent orchestration
│   ├── repl.py        # Main interaction loop  
│   ├── session.py     # Global state management
│   ├── deps.py        # Tool dependency system
│   ├── commands.py    # Built-in slash commands
│   ├── config.py      # Configuration handling
│   └── setup.py       # First-time setup wizard
├── tools/             # Tool implementations
│   ├── file_ops/      # File operations (NEW)
│   ├── dev_tools/     # Development tools (NEW)
│   ├── analysis/      # Code analysis (NEW)
│   ├── integrations/  # External integrations (NEW)
│   └── wrapper.py     # Tool registration
├── infrastructure/    # Infrastructure components (NEW)
│   ├── models.py      # Model management
│   └── natural_language.py # NLP utilities
├── ui/                # UI components
├── utils/             # Utility modules
└── prompts/           # System prompts
```

### Application Entry Point (`__main__.py`)

```python
# Entry Point: terminus.__main__:app (defined in pyproject.toml)
# Framework: Built with typer for CLI interface

def main():
    """Main application flow"""
    1. Initialize configuration (API keys, settings)
    2. Setup logging and session
    3. Load project guide (if terminus.md exists)
    4. Start the REPL (Read-Eval-Print Loop)
```

**Key Components:**
- **CLI Framework**: `typer` for command-line interface
- **Async Event Loop**: Manual setup for proper signal handling
- **Configuration Loading**: Handles first-time setup and validation
- **Session Initialization**: Prepares global state

### Session Management (`core/session.py`)

The global session object maintains state across the entire application lifecycle:

```python
@dataclass
class Session:
    current_model: str = DEFAULT_MODEL           # AI model identifier
    agents: Dict = field(default_factory=dict)   # Agent instances cache
    messages: list = field(default_factory=list) # Conversation history
    working_directory: Path                      # Current working directory
    allowed_commands: Set[str]                   # Whitelisted shell commands
    confirmation_enabled: bool = True            # Tool confirmation prompts
    disabled_confirmations: Set[str]             # Tools user always allows
    spinner: Any = None                          # UI spinner state
    current_task: Optional[asyncio.Task] = None  # Active async task
    sigint_received: bool = False                # Signal handling state
```

**Session Responsibilities:**
- Maintains conversation context between requests
- Tracks working directory changes
- Manages user preferences (confirmations, allowed commands)
- Handles UI state (spinners, current operations)
- Provides signal handling for graceful cancellation

## Agent System

### Single Agent Architecture

Unlike complex multi-agent systems, Terminus uses a **focused single-agent approach**:

```python
def get_or_create_agent():
    """Create or retrieve the main agent instance"""
    if "default" not in session.agents:
        base_agent = Agent(
            model=DEFAULT_MODEL,              # Google Gemini 2.0 Flash
            system_prompt=_get_prompt("system"), # From prompts/system.txt
            tools=TOOLS,                      # 28 specialized tools
            deps_type=ToolDeps,              # Dependencies for tool execution
        )
        session.agents["default"] = base_agent
    return session.agents["default"]
```

### Agent System Prompt

The agent's behavior is defined by a comprehensive system prompt (`prompts/system.txt`) that includes:

- **Intent Recognition**: Action vs Information vs Hybrid requests
- **Tool Selection Guidelines**: Preference order and usage patterns
- **Response Style**: Minimal, actionable output
- **Workflow Patterns**: Common task sequences
- **Safety Guidelines**: When to use confirmations

### Agent Processing Flow

```python
async def process_request(message: str):
    """Main agent processing pipeline"""
    1. Load conversation history
    2. Prepend project guide if available
    3. Create tool dependencies (confirmation, status display)
    4. Iterate through agent responses
    5. Process each node (tool calls, text responses)
    6. Update session state
    7. Return final response
```

## Tool System

### Tool Architecture

Terminus provides **35 specialized tools** organized into logical categories:

#### 📁 File & Directory Operations (10 tools)

| Tool | Purpose | Safety Level |
|------|---------|--------------|
| `read_file` | Read and analyze files | Safe |
| `write_file` | Create new files | Requires confirmation |
| `update_file` | Modify existing files intelligently | Requires confirmation |
| `list_directory` | Browse with tree structure | Safe |
| `find` | Find files by pattern | Safe |
| `grep` | Text search across files | Safe |
| `find_by_extension` | Find by file type | Safe |
| `list_extensions` | Catalog project file types | Safe |
| `change_directory` | Session-aware navigation | Safe |
| `get_current_directory` | Show current location | Safe |

#### 🔍 Analysis & Discovery (5 tools)

| Tool | Purpose | Safety Level |
|------|---------|--------------|
| `summarize_code` | Analyze and explain code | Safe |
| `analyze_project_structure` | Complete project overview | Safe |
| `search_todos` | Find TODO/FIXME comments | Safe |
| `package_info` | Project metadata | Safe |
| `quick_stats` | File/directory statistics | Safe |

#### 🚀 Development Workflow (5 tools)

| Tool | Purpose | Safety Level |
|------|---------|--------------|
| `git_add` | Stage files with preview | Requires confirmation |
| `git_commit` | Commit with message | Requires confirmation |
| `git_status_enhanced` | Visual git status | Safe |
| `quick_commit` | Fast commit workflow | Requires confirmation |
| `create_project_template` | Project scaffolding | Requires confirmation |

#### 🔧 System & Automation (5 tools)

| Tool | Purpose | Safety Level |
|------|---------|--------------|
| `run_command` | Execute shell commands safely | Requires confirmation |
| `run_in_directory` | Execute in specific directories | Requires confirmation |
| `system_info` | System information | Safe |
| `find_large_files` | Locate large files | Safe |
| `clean_temp_files` | Clean temporary files | Requires confirmation |

#### 📚 Help & Documentation (3 tools)

| Tool | Purpose | Safety Level |
|------|---------|--------------|
| `list_all_commands` | Complete command reference | Safe |
| `command_examples` | Usage examples | Safe |
| `quick_help` | Context-specific help | Safe |

#### 📧 Gmail Operations (4 tools)

| Tool | Purpose | Safety Level |
|------|---------|--------------|
| `list_unread` | Fetch top N unread emails | Safe |
| `summary` | Generate AI summaries of email content | Requires confirmation |
| `generate_draft` | Create email drafts from natural language | Requires confirmation |
| `search_email` | Search emails by sender, subject, or content | Safe |

#### 📅 Calendar Operations (3 tools)

| Tool | Purpose | Safety Level |
|------|---------|--------------|
| `add_event` | Schedule new calendar events | Requires confirmation |
| `check_availability` | Check for scheduling conflicts | Safe |
| `block_focus` | Create focus time blocks | Requires confirmation |

### Tool Dependencies System (`core/deps.py`)

```python
@dataclass
class ToolDeps:
    """Dependencies passed to tools via RunContext"""
    confirm_action: Optional[Callable]      # User confirmation callback
    display_tool_status: Optional[Callable] # Progress display callback
```

**Import Updates (v0.2.0):**
- All tool files now use relative imports: `from ...core.deps import ToolDeps`
- Core modules reference each other with relative imports
- Session is imported as: `from terminus.core.session import session`

### Tool Registration

Tools are registered in `tools/wrapper.py`:

```python
def create_tools():
    """Create Tool instances for all tools"""
    return [
        Tool(read_file),
        Tool(write_file),
        Tool(update_file),
        # ... all 28 tools
    ]
```

## UI System

### Modular UI Architecture

```
ui/
├── __init__.py     # Main exports and backwards compatibility
├── core.py         # Banner, spinners, core functionality
├── colors.py       # Color scheme and styling
├── formatting.py   # Syntax highlighting, diffs
├── messages.py     # Standard message types
└── panels.py       # Rich panel creation and display
```

### Panel System

The UI uses a sophisticated panel system for consistent display:

```python
# Panel types with specific purposes
display_agent_panel(content, has_footer)    # AI responses
display_tool_panel(content, title, footer)  # Tool output/preview
display_confirmation_panel(content)         # User confirmations
display_error_panel(message, detail, title) # Error messages
display_info_panel(content)                 # Information display
```

### Color Scheme

```python
class Colors:
    primary = "cyan"           # Agent responses, main branding
    success = "green"          # Success messages
    warning = "yellow"         # Warnings, confirmations
    error = "red"             # Error messages
    muted = "bright_black"    # Secondary information
    tool_data = "blue"        # Tool output data
    accent = "magenta"        # Highlights, special elements
```

### Context-Aware Spacing

The UI system maintains context about previous output types to provide appropriate spacing:

```python
_last_output = None  # "status", "panel", "user_input", or None

def _prepare_to_print(new_type: str):
    """Adds blank lines based on context for optimal visual flow"""
```

## Request Processing Flow

### Complete User Request Lifecycle

```mermaid
graph TD
    A[User Input] --> B[REPL.run()]
    B --> C{Built-in Command?}
    C -->|Yes| D[Handle Command (/help, /clear, etc.)]
    C -->|No| E[Process Request]
    E --> F[Agent Processing]
    F --> G[Tool Selection & Planning]
    G --> H{Confirmation Required?}
    H -->|Yes| I[Show Tool Preview]
    I --> J[User Confirmation]
    J --> K{Approved?}
    K -->|Yes| L[Execute Tool]
    K -->|No| M[Cancel Operation]
    H -->|No| L
    L --> N[Tool Execution]
    N --> O[Update Session State]
    O --> P[Agent Synthesis]
    P --> Q[Display Result]
    Q --> R[Ready for Next Input]
```

### Detailed Processing Steps

#### 1. Input Processing (`repl.py`)

```python
async def _handle_user_request(self, user_input: str):
    """Process user request with full error handling"""
    1. Start thinking spinner
    2. Create async task for request processing
    3. Handle cancellation (Ctrl+C)
    4. Display results or errors
    5. Clean up task state
```

#### 2. Agent Processing (`agent.py`)

```python
async def process_request(message: str):
    """Main agent processing pipeline"""
    1. Get or create agent instance
    2. Prepare message history with context
    3. Add project guide if available
    4. Set up tool dependencies
    5. Iterate through agent stream
    6. Process each response node
    7. Return synthesized result
```

#### 3. Node Processing

The agent processes different types of response nodes:

- **CallToolsNode**: Tool execution requests
- **TextPart**: Thinking responses or final answers
- **ToolCallPart**: Specific tool invocations
- **ToolReturnPart**: Tool execution results

#### 4. Tool Execution

Each tool receives a `RunContext[ToolDeps]` with:
- Access to confirmation callbacks
- Status display capabilities
- Session state and working directory
- Error handling context

## Configuration System

### Configuration Structure

```json
{
  "default_model": "google-gla:gemini-2.0-flash-exp",
  "env": {
    "GEMINI_API_KEY": "your-api-key-here"
  },
  "settings": {
    "allowed_commands": [
      "ls", "cat", "grep", "find", "pwd", "echo", "which",
      "head", "tail", "wc", "sort", "uniq", "diff", "tree"
    ]
  }
}
```

### Configuration Management (`config.py`)

- **Location**: `~/.config/terminus.json`
- **Validation**: Schema validation and error recovery
- **Merging**: Deep merge with defaults
- **Environment**: API key injection into environment variables

### First-Time Setup (`setup.py`)

The setup wizard handles:

1. **Welcome Screen**: Introduction and purpose
2. **API Key Collection**: Secure password input
3. **Configuration Creation**: Merge with defaults
4. **Validation**: Ensure required fields
5. **Error Recovery**: Backup and reset options

```python
def run_setup() -> Dict:
    """Complete setup flow"""
    1. Check for existing config
    2. Validate existing config if present
    3. Handle invalid/corrupted configs
    4. Create new config if needed
    5. Return validated configuration
```

## Safety & Security

### Multi-Layer Safety System

#### 1. Tool Confirmation System

```python
# Tool classification by safety level
ALLOWED_TOOLS = [
    "read_file",      # Always safe
    "find", 
    "grep",
    "list_directory"
]

# Confirmation flow for destructive operations
async def confirm(title: str, preview: Any, footer: str = None) -> bool:
    """Show tool preview and get user confirmation"""
    1. Display tool data panel
    2. Show confirmation options
    3. Handle user choice (y/n/always)
    4. Update disabled confirmations if "always"
    5. Return approval status
```

#### 2. Command Whitelisting

```python
# Predefined safe shell commands
DEFAULT_ALLOWED_COMMANDS = [
    "ls", "cat", "grep", "rg", "find", "pwd", "echo", "which",
    "head", "tail", "wc", "sort", "uniq", "diff", "tree", "file",
    "stat", "du", "df", "ps", "top", "env", "date", "whoami"
]
```

#### 3. Error Handling (`utils/error.py`)

```python
class ErrorContext:
    """Comprehensive error handling with cleanup"""
    1. Extract clean error messages
    2. Determine if errors should be logged
    3. Save detailed logs to temp files
    4. Provide user-friendly error display
    5. Execute cleanup callbacks
```

#### 4. Signal Handling

- **Graceful Cancellation**: Proper SIGINT handling
- **Task Cleanup**: Cancel running operations safely
- **State Preservation**: Maintain session integrity
- **User Feedback**: Clear cancellation messages

## Project Structure (v0.2.0 - Modular Architecture)

```
terminus-cli/
├── pyproject.toml           # Package configuration
├── README.md               # User documentation  
├── ARCHITECTURE.md         # This file
├── src/terminus/
│   ├── __init__.py         # Package exports
│   ├── __main__.py         # Application entry point
│   ├── constants.py        # App constants and defaults
│   ├── core/               # Core components (NEW)
│   │   ├── __init__.py     # Core module exports
│   │   ├── agent.py        # AI agent orchestration
│   │   ├── repl.py         # Main interaction loop
│   │   ├── session.py      # Global state management
│   │   ├── deps.py         # Tool dependency system
│   │   ├── commands.py     # Built-in slash commands
│   │   ├── config.py       # Configuration handling
│   │   └── setup.py        # First-time setup wizard
│   ├── infrastructure/     # Infrastructure components (NEW)
│   │   ├── __init__.py     # Infrastructure exports
│   │   ├── models.py       # Model management and config
│   │   └── natural_language.py # NLP utilities
│   ├── tools/              # Tool implementations
│   │   ├── __init__.py     # Tool exports
│   │   ├── wrapper.py      # Tool registration and creation
│   │   ├── file_ops/       # File operations (NEW)
│   │   │   ├── __init__.py # File ops exports
│   │   │   ├── read_file.py # File reading operations
│   │   │   ├── write_file.py # File creation operations
│   │   │   ├── update_file.py # File modification operations
│   │   │   ├── find.py     # File discovery
│   │   │   ├── grep.py     # Text search
│   │   │   ├── list.py     # Directory listing
│   │   │   ├── directory.py # Directory operations
│   │   │   └── file_discovery.py # Advanced file discovery
│   │   ├── dev_tools/      # Development tools (NEW)
│   │   │   ├── __init__.py # Dev tools exports
│   │   │   ├── git.py      # Git operations
│   │   │   ├── run_command.py # Shell command execution
│   │   │   ├── dev_workflow.py # Development workflow
│   │   │   ├── system_utilities.py # System utilities
│   │   │   └── help_system.py # Help and documentation
│   │   ├── analysis/       # Code analysis tools (NEW)
│   │   │   ├── __init__.py # Analysis exports
│   │   │   ├── code_analysis.py # Code summarization
│   │   │   ├── code_review.py # Code review capabilities
│   │   │   └── code_reviewer.py # Code analyzer engine
│   │   └── integrations/   # External integrations (NEW)
│   │       ├── __init__.py # Integration exports
│   │       ├── gmail.py    # Gmail API operations
│   │       ├── calendar.py # Google Calendar operations
│   │       ├── google_auth.py # Google OAuth handling
│   │       └── google_setup.py # Google API setup
│   ├── ui/                 # Rich-based UI system
│   │   ├── __init__.py     # UI exports
│   │   ├── core.py         # Banner, spinners, core functions
│   │   ├── panels.py       # Panel creation and display
│   │   ├── messages.py     # Message display functions
│   │   ├── colors.py       # Color schemes and styling
│   │   └── formatting.py   # Syntax highlighting and formatting
│   ├── utils/              # Utility modules
│   │   ├── __init__.py     # Utility exports
│   │   ├── error.py        # Error handling and logging
│   │   ├── command.py      # Command parsing utilities
│   │   ├── input.py        # Multiline input handling
│   │   ├── logger.py       # Logging configuration
│   │   └── guide.py        # Project guide loading
│   └── prompts/            # System prompts
│       ├── system.txt      # Main agent system prompt
│       └── local_model_system.txt # Local model prompt
├── build/                  # Build artifacts
└── env/                    # Virtual environment
```

## Key Design Principles

### 1. Single Agent Architecture
- **Simplicity**: One intelligent agent instead of multiple specialized agents
- **Context Retention**: Maintains conversation flow and project understanding
- **Tool Orchestration**: Agent selects and combines tools as needed

### 2. Tool-First Design
- **Modularity**: Each capability is a discrete, testable tool
- **Composability**: Tools can be combined for complex workflows
- **Extensibility**: New tools can be added without core changes

### 3. Safety by Default
- **Confirmation System**: Prevents accidental destructive operations
- **Command Whitelisting**: Only safe shell commands allowed by default
- **User Control**: Multiple safety override mechanisms

### 4. Session Awareness
- **Context Preservation**: Maintains working directory and conversation history
- **State Management**: Tracks user preferences and ongoing operations
- **Graceful Recovery**: Handles interruptions and errors cleanly

### 5. Natural Language Interface
- **Intent Recognition**: Understands action vs information requests
- **Flexible Input**: Users describe goals rather than memorizing commands
- **Intelligent Planning**: Agent breaks down complex requests automatically

### 6. Terminal Native
- **Shell Integration**: Works with any terminal and shell
- **Async Design**: Non-blocking operations with proper cancellation
- **Rich UI**: Beautiful terminal interfaces without external dependencies

### 7. Transparent Operation
- **Tool Previews**: Shows what will happen before execution
- **Status Updates**: Real-time feedback on long operations
- **Error Clarity**: Clear, actionable error messages

## Development Guide

### Adding New Tools

1. **Create Tool Function**:
   ```python
   async def my_new_tool(ctx: RunContext[ToolDeps], param: str) -> str:
       """Tool description for the agent."""
       # Implementation
       return "Result"
   ```

2. **Register Tool**:
   ```python
   # In tools/wrapper.py
   Tool(my_new_tool)
   ```

3. **Import in Tools Module**:
   ```python
   # In tools/__init__.py or wrapper.py
   from .my_module import my_new_tool
   ```

### Tool Development Guidelines

- **Use Type Hints**: Helps agent understand parameters
- **Clear Docstrings**: Agent uses these for tool selection
- **Error Handling**: Return error messages, don't raise exceptions
- **Confirmation**: Use `ctx.deps.confirm_action` for destructive operations
- **Status Updates**: Use `ctx.deps.display_tool_status` for progress

### UI Development

- **Consistent Styling**: Use predefined colors and panel types
- **Context Awareness**: Consider previous output type for spacing
- **Rich Components**: Leverage Rich library features appropriately
- **Accessibility**: Ensure good contrast and readable output

### Testing

- **Tool Testing**: Each tool should have unit tests
- **Integration Testing**: Test tool combinations and workflows
- **Error Scenarios**: Test error handling and recovery
- **UI Testing**: Verify panel display and formatting

### Configuration

- **Backward Compatibility**: Maintain config schema compatibility
- **Validation**: Always validate configuration changes
- **Defaults**: Provide sensible defaults for new options
- **Documentation**: Update setup wizard for new configuration options

---

This architecture enables Terminus to be a powerful, safe, and extensible terminal automation tool that grows with user needs while maintaining simplicity and reliability.

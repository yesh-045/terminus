# Terminus CLI - Architecture Documentation

## Table of Contents
- [System Overview](#system-overview)
- [Architecture Principles](#architecture-principles)
- [Core Components](#core-components)
- [Multi-Model Support](#multi-model-support)
- [Tool System Architecture](#tool-system-architecture)
- [Session Management](#session-management)
- [Safety Framework](#safety-framework)
- [User Interface System](#user-interface-system)
- [Request Processing Pipeline](#request-processing-pipeline)
- [Configuration Management](#configuration-management)
- [Project Structure](#project-structure)
- [Development Guidelines](#development-guidelines)

## System Overview

Terminus CLI is an advanced terminal automation system built around a sophisticated AI agent that orchestrates specialized tools to accomplish complex workflows. The system is designed with a clean separation of concerns, modular architecture, and comprehensive safety mechanisms.

### Key Architectural Features

**Single Agent Design**: Unlike multi-agent systems, Terminus uses one intelligent agent that coordinates multiple specialized tools, reducing complexity while maintaining powerful capabilities.

**Multi-Model Support**: Flexible AI backend supporting both cloud-based models (Google Gemini) and local models (Ollama) for different use cases and privacy requirements.

**Tool-First Architecture**: Core functionality implemented as discrete, composable tools that can be combined for complex workflows.

**Session Persistence**: Maintains conversation context, working directory state, and user preferences across application restarts.

**Safety by Design**: Multi-layer confirmation system prevents accidental destructive operations while maintaining workflow efficiency.

## Architecture Principles

### Design Philosophy

**Action-Oriented Approach**: The system prioritizes taking action over explanation. When user intent is clear, Terminus executes appropriate tools rather than merely describing what could be done.

**Minimalist Output**: Responses are concise and focused on results. Verbose explanations are avoided in favor of clear, actionable information.

**Safety Without Friction**: Destructive operations require confirmation with clear previews, but safe operations proceed immediately to maintain workflow efficiency.

**Extensible Foundation**: New tools can be added easily, and the agent automatically incorporates them into its reasoning without configuration changes.

**Composable Operations**: Tools are designed to work together, enabling the agent to orchestrate complex multi-step workflows from simple components.

### Agent Decision-Making Process

**Intent Recognition**: The language model analyzes natural language input to determine whether the request is informational, action-oriented, or hybrid.

**Tool Selection**: Based on intent analysis, the agent matches requests to the most appropriate tools by comparing against tool docstrings and parameter requirements.

**Workflow Planning**: For complex requests, the agent plans sequences of tool invocations, using outputs from earlier tools as inputs to later ones.

**Dynamic Adaptation**: Plans can be modified based on intermediate results, errors, or user feedback during execution.

**Context Integration**: All decisions consider conversation history, current working directory, project structure, and previous tool outputs.
## Core Components

### Application Entry Point

The application follows a clean initialization sequence managed by the main entry point:

```python
# Entry Point: terminus.interface.cli.__main__:app
# Framework: Built with typer for robust CLI interface management

async def main():
    """Application startup sequence"""
    1. Load and validate configuration
    2. Initialize logging and error handling  
    3. Setup session management
    4. Load project context if available
    5. Start interactive REPL
```

**Key Responsibilities:**
- **Configuration Management**: Handles first-time setup, validation, and API key management
- **Session Initialization**: Prepares global application state and context
- **Error Handling**: Establishes comprehensive error catching and recovery
- **Signal Management**: Provides graceful shutdown and interruption handling

### Agent Orchestration System

The core agent system provides intelligent coordination of tools and workflows:

```python
# Located in: core/agent.py

@dataclass
class AgentManager:
    """Central agent management with multi-model support"""
    agents: Dict[str, Agent] = field(default_factory=dict)
    current_model: str = DEFAULT_MODEL
    
def get_or_create_agent(model_name: str = None) -> Agent:
    """Retrieve or create agent for specified model"""
    model = model_name or session.current_model
    if model not in session.agents:
        agent = Agent(
            model=model,
            system_prompt=load_system_prompt(),
            tools=create_tools(),
            deps_type=ToolDeps
        )
        session.agents[model] = agent
    return session.agents[model]
```

**Agent Capabilities:**
- **Multi-Model Support**: Seamless switching between Google Gemini and Ollama models
- **Context Management**: Maintains conversation history and project understanding
- **Tool Orchestration**: Intelligent selection and chaining of specialized tools
- **Error Recovery**: Graceful handling of failures with alternative approaches

### Session Management Infrastructure

Global session state maintains context and preferences across the application lifecycle:

```python
# Located in: core/session.py

@dataclass
class Session:
    """Application-wide state management"""
    current_model: str = DEFAULT_MODEL
    agents: Dict[str, Agent] = field(default_factory=dict)
    messages: List[Message] = field(default_factory=list)
    working_directory: Path = field(default_factory=Path.cwd)
    allowed_commands: Set[str] = field(default_factory=set)
    confirmation_enabled: bool = True
    disabled_confirmations: Set[str] = field(default_factory=set)
    current_task: Optional[asyncio.Task] = None
    session_metadata: Dict = field(default_factory=dict)
```

**Session Features:**
- **Persistent Context**: Conversation history and working directory tracking
- **User Preferences**: Confirmation settings and allowed command management
- **Task Coordination**: Async task management with cancellation support
- **State Persistence**: Save and load session data across application restarts
## Multi-Model Support

### Model Provider Architecture

Terminus CLI implements a flexible model provider system supporting both cloud and local AI models:

```python
# Located in: infrastructure/models/

class ModelManager:
    """Manages multiple AI model providers"""
    
    def __init__(self):
        self.providers = {
            'google': GoogleModelProvider(),
            'ollama': OllamaModelProvider()
        }
    
    async def switch_model(self, model_identifier: str):
        """Switch active model with validation"""
        provider, model = self.parse_model_identifier(model_identifier)
        await self.providers[provider].validate_model(model)
        session.current_model = model_identifier
```

### Google Gemini Integration

**Cloud-Based Processing**: Utilizes Google's Gemini 2.0 Flash Experimental model for advanced reasoning and complex analysis tasks.

**Key Features:**
- Advanced natural language understanding
- Superior code analysis and generation capabilities
- Complex multi-step workflow planning
- Extensive context window for large projects

**Configuration:**
```python
google_config = {
    "api_key": "your-gemini-api-key",
    "model": "gemini-2.0-flash-exp",
    "safety_settings": {...},
    "generation_config": {...}
}
```

### Ollama Local Model Support

**Offline Operation**: Complete functionality without internet connectivity using locally hosted models.

**Supported Models:**
- **Qwen**: Excellent for code understanding and generation
- **Llama**: General-purpose reasoning and analysis
- **CodeLlama**: Specialized for programming tasks
- **Custom Models**: Any Ollama-compatible model

**OpenAI API Compatibility**: Implements OpenAI-compatible endpoint (`http://localhost:11434/v1`) for seamless pydantic-ai integration.

**Configuration:**
```python
ollama_config = {
    "base_url": "http://localhost:11434/v1",
    "model": "qwen:latest",
    "enabled": True,
    "timeout": 60
}
```

### Model Selection Strategy

**Automatic Failover**: If primary model is unavailable, automatically fallback to alternative models based on task requirements.

**Task-Specific Selection**: Different models optimized for different task types:
- **Complex Analysis**: Google Gemini
- **Code Generation**: CodeLlama or Qwen
- **Offline Work**: Any available Ollama model
- **Privacy-Sensitive**: Local models only

## Tool System Architecture

### Tool Organization and Categories

Terminus CLI provides **40 specialized tools** organized into logical categories for clear separation of concerns:

```
tools/
├── filesystem/          # File and directory operations (10 tools)
│   ├── read_file.py    # File content reading and analysis
│   ├── write_file.py   # File creation with content generation
│   ├── update_file.py  # Intelligent file modification
│   ├── find.py         # Pattern-based file discovery
│   ├── grep.py         # Text search across files
│   ├── list.py         # Directory browsing and visualization
│   ├── directory.py    # Directory navigation and management
│   └── file_discovery.py # Advanced file type analysis
├── development/         # Development workflow tools (8 tools)
│   ├── git.py          # Git operations and version control
│   ├── code_analysis.py # Code structure analysis
│   ├── dev_workflow.py # Development utilities
│   └── project_automation.py # Automated project tasks
├── system/             # System utilities (5 tools)
│   ├── run_command.py  # Safe shell command execution
│   └── system_utilities.py # System information and cleanup
├── integrations/       # External service integration (10 tools)
│   ├── gmail.py        # Email management and automation
│   ├── calendar.py     # Calendar operations and scheduling
│   └── google_setup.py # Google API authentication
├── help/               # Help and documentation (3 tools)
│   └── help_system.py  # User assistance and guidance
└── wrapper.py          # Tool registration and management
```

### Tool Implementation Pattern

Each tool follows a consistent implementation pattern for reliability and maintainability:

```python
async def tool_function(ctx: RunContext[ToolDeps], param: str) -> str:
    """
    Brief description of tool function for AI agent understanding.
    
    Args:
        ctx: Runtime context with access to confirmation and status callbacks
        param: Tool-specific parameters with type hints
        
    Returns:
        Result string or structured data for agent processing
    """
    try:
        # Parameter validation
        if not param:
            return "Error: Required parameter missing"
            
        # Tool-specific logic
        result = perform_operation(param)
        
        # Status updates for long operations
        if ctx.deps.display_tool_status:
            ctx.deps.display_tool_status(f"Processing {param}...")
            
        # Confirmation for destructive operations
        if requires_confirmation and ctx.deps.confirm_action:
            confirmed = await ctx.deps.confirm_action(
                title="Confirm Operation",
                preview=preview_data,
                footer="This action cannot be undone"
            )
            if not confirmed:
                return "Operation cancelled by user"
                
        return f"Successfully completed: {result}"
        
    except Exception as e:
        return f"Error: {str(e)}"
```

### Tool Safety Classification

Tools are classified by safety level to determine confirmation requirements:

**Safe Tools** (No confirmation required):
- File reading and analysis operations
- Directory browsing and navigation
- Information gathering and reporting
- Help and documentation access

**Confirmation Required Tools**:
- File creation and modification
- System command execution
- Git operations with repository changes
- External service integrations
- Configuration modifications

### Tool Dependencies System

The dependency injection system provides tools with access to user interface and confirmation mechanisms:

```python
@dataclass
class ToolDeps:
    """Dependencies passed to tools via RunContext"""
    confirm_action: Optional[Callable[[str, Any, str], Awaitable[bool]]]
    display_tool_status: Optional[Callable[[str], None]]
    
    # Additional context
    working_directory: Path
    session_state: Dict[str, Any]
    user_preferences: Dict[str, Any]
```

### Tool Registration and Discovery

Tools are automatically registered and made available to the AI agent:

```python
# Located in: tools/wrapper.py

def create_tools() -> List[Tool]:
    """Create Tool instances for all available tools"""
    return [
        # Filesystem tools
        Tool(read_file),
        Tool(write_file),
        Tool(update_file),
        # ... all 40 tools
    ]

# Agent automatically discovers tool capabilities
agent = Agent(
    model=model_name,
    tools=create_tools(),
    system_prompt=system_prompt
)
```

## Session Management

### Session State Architecture

The session management system provides comprehensive state persistence and context management:

```python
# Located in: core/session.py

@dataclass
class Session:
    """Global application state management"""
    # Model and agent management
    current_model: str = DEFAULT_MODEL
    agents: Dict[str, Agent] = field(default_factory=dict)
    
    # Conversation context
    messages: List[Message] = field(default_factory=list)
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Working environment
    working_directory: Path = field(default_factory=Path.cwd)
    environment_variables: Dict[str, str] = field(default_factory=dict)
    
    # User preferences
    confirmation_enabled: bool = True
    disabled_confirmations: Set[str] = field(default_factory=set)
    allowed_commands: Set[str] = field(default_factory=set)
    
    # Runtime state
    current_task: Optional[asyncio.Task] = None
    task_history: List[Dict] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
```

### Session Persistence

Sessions can be saved and restored to maintain context across application restarts:

```python
# Located in: core/persistence.py

class SessionPersistence:
    """Handles session save/load operations"""
    
    @staticmethod
    def save_session(session: Session, name: str = None) -> str:
        """Save session to disk with optional name"""
        session_data = {
            'session_id': session.session_id,
            'messages': serialize_messages(session.messages),
            'working_directory': str(session.working_directory),
            'user_preferences': {
                'confirmation_enabled': session.confirmation_enabled,
                'disabled_confirmations': list(session.disabled_confirmations),
                'allowed_commands': list(session.allowed_commands)
            },
            'metadata': {
                'created_at': session.created_at.isoformat(),
                'last_activity': session.last_activity.isoformat(),
                'message_count': len(session.messages)
            }
        }
        
        filename = name or f"session_{session.session_id[:8]}"
        save_path = get_sessions_directory() / f"{filename}.json"
        
        with open(save_path, 'w') as f:
            json.dump(session_data, f, indent=2)
            
        return str(save_path)
    
    @staticmethod
    def load_session(identifier: str) -> Session:
        """Load session by name or ID"""
        session_file = find_session_file(identifier)
        
        with open(session_file, 'r') as f:
            session_data = json.load(f)
            
        session = Session()
        session.session_id = session_data['session_id']
        session.messages = deserialize_messages(session_data['messages'])
        session.working_directory = Path(session_data['working_directory'])
        
        # Restore user preferences
        prefs = session_data['user_preferences']
        session.confirmation_enabled = prefs['confirmation_enabled']
        session.disabled_confirmations = set(prefs['disabled_confirmations'])
        session.allowed_commands = set(prefs['allowed_commands'])
        
        return session
```

### Session Commands

Built-in commands provide session management capabilities:

```python
# Session management commands
/sessions --list                    # List all saved sessions
/sessions --save [name]            # Save current session
/sessions --load <name_or_id>      # Load specific session
/sessions --clear                  # Delete all saved sessions
/sessions --info                   # Show current session information
```

### Context Management

The session system maintains context across interactions:

**Conversation History**: Complete message history with tool calls and responses
**Working Directory**: Tracks directory changes and maintains path context
**User Preferences**: Remembers confirmation settings and command permissions
**Project Context**: Understands project structure and file relationships

## Safety Framework

### Multi-Layer Safety System

Terminus CLI implements comprehensive safety mechanisms to prevent accidental destructive operations while maintaining workflow efficiency:

### Confirmation System

```python
# Located in: interface/cli/repl.py

async def confirm_action(title: str, preview: Any, footer: str = None) -> bool:
    """Multi-level confirmation system"""
    
    # Display tool preview panel
    display_tool_panel(
        content=preview,
        title=title,
        footer=footer or "Confirm this action?"
    )
    
    # Present confirmation options
    while True:
        choice = input("Proceed? [y/n/always]: ").lower().strip()
        
        if choice in ['y', 'yes']:
            return True
        elif choice in ['n', 'no']:
            return False
        elif choice == 'always':
            # Add to disabled confirmations for this session
            tool_name = extract_tool_name_from_title(title)
            session.disabled_confirmations.add(tool_name)
            return True
        else:
            print("Please enter 'y' (yes), 'n' (no), or 'always'")
```

### Command Whitelisting

Safe shell commands are pre-approved for execution without confirmation:

```python
# Located in: shared/constants.py

DEFAULT_ALLOWED_COMMANDS = {
    # File operations
    "ls", "cat", "head", "tail", "file", "stat",
    
    # Text processing
    "grep", "rg", "find", "wc", "sort", "uniq", "diff",
    
    # System information
    "pwd", "echo", "which", "env", "date", "whoami",
    "ps", "top", "df", "du",
    
    # Development tools
    "git status", "git log", "git diff", "git branch"
}
```

### Error Handling and Recovery

Comprehensive error handling with user-friendly messages and recovery options:

```python
# Located in: shared/utils/error.py

class ErrorHandler:
    """Centralized error handling with context preservation"""
    
    @staticmethod
    def handle_tool_error(error: Exception, tool_name: str, context: Dict) -> str:
        """Handle tool execution errors gracefully"""
        
        # Extract clean error message
        clean_message = extract_user_friendly_message(error)
        
        # Log detailed error for debugging
        if should_log_error(error):
            error_id = log_detailed_error(error, tool_name, context)
            clean_message += f" (Error ID: {error_id})"
        
        # Provide recovery suggestions
        recovery_suggestions = generate_recovery_suggestions(error, tool_name)
        if recovery_suggestions:
            clean_message += f"\n\nSuggestions:\n{recovery_suggestions}"
            
        return clean_message
    
    @staticmethod
    def execute_cleanup_on_error(cleanup_functions: List[Callable]):
        """Execute cleanup functions when errors occur"""
        for cleanup_func in cleanup_functions:
            try:
                cleanup_func()
            except Exception:
                pass  # Cleanup errors should not prevent error reporting
```

### Signal Handling

Graceful handling of interruption signals (Ctrl+C) with proper cleanup:

```python
# Located in: interface/cli/repl.py

async def handle_sigint():
    """Handle Ctrl+C interruption gracefully"""
    
    if session.current_task:
        # Cancel running task
        session.current_task.cancel()
        
        try:
            await session.current_task
        except asyncio.CancelledError:
            pass
            
        # Clean up task state
        session.current_task = None
        
    # Provide user feedback
    display_info_panel("Operation cancelled by user")
    
    # Preserve session state
    auto_save_session_if_enabled()
```

### Data Validation

Input validation and sanitization for all tool parameters:

```python
def validate_file_path(path: str) -> Tuple[bool, str]:
    """Validate file path for safety"""
    
    # Check for directory traversal attempts
    if '..' in path or path.startswith('/'):
        return False, "Path traversal detected"
    
    # Validate path format
    try:
        validated_path = Path(path).resolve()
    except Exception:
        return False, "Invalid path format"
    
    # Check permissions
    if not has_read_permission(validated_path):
        return False, "Insufficient permissions"
        
    return True, str(validated_path)
```
## User Interface System

### Modular UI Architecture

The user interface system provides rich terminal interactions with consistent styling and responsive design:

```
interface/cli/
├── __main__.py          # Application entry point and CLI setup
├── commands.py          # Built-in command implementations
├── repl.py             # Interactive shell and request processing
└── ui/                 # User interface components
    ├── core.py         # Core UI functionality and spinners
    ├── panels.py       # Rich panel creation and management
    ├── messages.py     # Message formatting and display
    ├── colors.py       # Color scheme and styling constants
    └── formatting.py   # Syntax highlighting and content formatting
```

### Panel System

Rich panels provide consistent visual organization for different content types:

```python
# Located in: interface/cli/ui/panels.py

def display_agent_panel(content: str, has_footer: bool = True):
    """Display AI agent responses with consistent styling"""
    panel = Panel(
        content,
        title="[cyan]Terminus[/cyan]",
        border_style="cyan",
        padding=(1, 2)
    )
    console.print(panel)

def display_tool_panel(content: Any, title: str, footer: str = None):
    """Display tool output with syntax highlighting"""
    formatted_content = format_tool_output(content)
    panel = Panel(
        formatted_content,
        title=f"[blue]{title}[/blue]",
        border_style="blue",
        subtitle=footer if footer else None
    )
    console.print(panel)

def display_confirmation_panel(content: Any) -> bool:
    """Display confirmation panel with user interaction"""
    panel = Panel(
        content,
        title="[yellow]Confirmation Required[/yellow]",
        border_style="yellow",
        padding=(1, 2)
    )
    console.print(panel)
```

### Color Scheme and Styling

Consistent color scheme across all interface components:

```python
# Located in: interface/cli/ui/colors.py

class Colors:
    """Application color constants"""
    primary = "cyan"           # Agent responses and branding
    success = "green"          # Success messages and confirmations
    warning = "yellow"         # Warnings and user confirmations  
    error = "red"             # Error messages and failures
    info = "blue"             # Tool output and information
    muted = "bright_black"    # Secondary information
    accent = "magenta"        # Special highlights and emphasis
    
class Styles:
    """Rich markup style definitions"""
    code = "bold bright_white on grey23"
    file_path = "underline cyan"
    command = "bold green"
    parameter = "italic blue"
```

### Content Formatting

Advanced content formatting with syntax highlighting and intelligent display:

```python
# Located in: interface/cli/ui/formatting.py

def format_code_content(content: str, language: str = None) -> str:
    """Apply syntax highlighting to code content"""
    if language:
        lexer = get_lexer_by_name(language)
        formatter = TerminalFormatter()
        return highlight(content, lexer, formatter)
    return content

def format_file_diff(original: str, modified: str) -> str:
    """Create formatted diff display"""
    diff_lines = unified_diff(
        original.splitlines(keepends=True),
        modified.splitlines(keepends=True),
        fromfile="original",
        tofile="modified"
    )
    return "".join(diff_lines)

def format_directory_tree(path: Path, max_depth: int = 3) -> str:
    """Generate formatted directory tree visualization"""
    tree = Tree(f"[bold cyan]{path.name}[/bold cyan]")
    build_tree_recursive(tree, path, max_depth)
    return tree
```

### Context-Aware Spacing

The UI system maintains awareness of previous output types to provide optimal visual flow:

```python
# Located in: interface/cli/ui/core.py

class UIContext:
    """Manages UI state and context"""
    
    def __init__(self):
        self.last_output_type = None
        self.needs_spacing = False
        
    def prepare_output(self, output_type: str):
        """Add appropriate spacing based on context"""
        spacing_rules = {
            ("panel", "panel"): 1,
            ("status", "panel"): 0,
            ("user_input", "panel"): 1,
            ("error", "panel"): 1
        }
        
        rule_key = (self.last_output_type, output_type)
        lines_needed = spacing_rules.get(rule_key, 0)
        
        if lines_needed > 0:
            console.print("\n" * lines_needed, end="")
            
        self.last_output_type = output_type
```

### Interactive Components

Rich interactive components for user input and selection:

```python
def multi_line_input_prompt() -> str:
    """Multi-line input with syntax highlighting"""
    lines = []
    print("Enter your request (Ctrl+D or empty line to finish):")
    
    while True:
        try:
            line = input("│ " if lines else "┌ ")
            if not line and lines:
                break
            lines.append(line)
        except EOFError:
            break
            
    return "\n".join(lines)

def selection_prompt(options: List[str], title: str) -> int:
    """Interactive selection from list of options"""
    panel = Panel(
        "\n".join(f"{i+1}. {option}" for i, option in enumerate(options)),
        title=title,
        border_style="blue"
    )
    console.print(panel)
    
    while True:
        try:
            choice = int(input("Select option (number): ")) - 1
            if 0 <= choice < len(options):
                return choice
        except ValueError:
            pass
        print("Invalid selection. Please enter a valid number.")
```

## Request Processing Pipeline

### Complete Request Lifecycle

The request processing pipeline handles user input through a sophisticated multi-stage process:

```
User Input → REPL Processing → Agent Analysis → Tool Selection → 
Confirmation → Tool Execution → Result Synthesis → UI Display
```

### Stage 1: Input Processing

```python
# Located in: interface/cli/repl.py

async def process_user_input(user_input: str):
    """Main input processing pipeline"""
    
    # Handle built-in commands first
    if user_input.startswith('/'):
        return await handle_builtin_command(user_input)
    
    # Create async task for AI processing
    task = asyncio.create_task(process_ai_request(user_input))
    session.current_task = task
    
    try:
        # Start thinking indicator
        with thinking_spinner():
            result = await task
            
        # Display results
        display_agent_panel(result)
        
    except asyncio.CancelledError:
        display_info_panel("Request cancelled by user")
    except Exception as e:
        display_error_panel(f"Processing error: {e}")
    finally:
        session.current_task = None
```

### Stage 2: Agent Analysis

```python
# Located in: core/agent.py

async def process_ai_request(message: str) -> str:
    """AI agent request processing"""
    
    # Get appropriate agent for current model
    agent = get_or_create_agent(session.current_model)
    
    # Prepare conversation context
    conversation_history = prepare_message_history()
    
    # Add project context if available
    if project_guide := load_project_guide():
        conversation_history.insert(0, project_guide)
    
    # Set up tool dependencies
    tool_deps = ToolDeps(
        confirm_action=confirm_action,
        display_tool_status=display_status
    )
    
    # Process through agent
    result_parts = []
    async for response in agent.run_stream(
        message, 
        message_history=conversation_history,
        deps=tool_deps
    ):
        result_parts.extend(await process_response_node(response))
    
    # Update session state
    session.messages.extend(conversation_history)
    session.last_activity = datetime.now()
    
    return synthesize_response(result_parts)
```

### Stage 3: Tool Selection and Execution

```python
async def process_response_node(node) -> List[str]:
    """Process individual response nodes from agent"""
    
    if isinstance(node, CallToolsNode):
        return await execute_tool_calls(node.tool_calls)
    elif isinstance(node, TextPart):
        return [node.content]
    else:
        return [str(node)]

async def execute_tool_calls(tool_calls: List[ToolCall]) -> List[str]:
    """Execute multiple tool calls with confirmation"""
    results = []
    
    for tool_call in tool_calls:
        # Check if confirmation is needed
        if tool_requires_confirmation(tool_call.tool_name):
            if not await request_confirmation(tool_call):
                results.append(f"Tool {tool_call.tool_name} cancelled by user")
                continue
        
        # Execute tool with error handling
        try:
            result = await execute_single_tool(tool_call)
            results.append(result)
        except Exception as e:
            error_msg = handle_tool_error(e, tool_call.tool_name)
            results.append(error_msg)
    
    return results
```

### Stage 4: Confirmation Flow

```python
async def request_confirmation(tool_call: ToolCall) -> bool:
    """Handle tool confirmation with preview"""
    
    # Generate preview of tool operation
    preview_data = generate_tool_preview(tool_call)
    
    # Display confirmation panel
    display_confirmation_panel(
        title=f"Execute {tool_call.tool_name}",
        content=preview_data,
        footer="This action may modify files or system state"
    )
    
    # Get user decision
    while True:
        choice = input("Proceed? [y/n/always/never]: ").lower()
        
        if choice in ['y', 'yes']:
            return True
        elif choice in ['n', 'no']:
            return False
        elif choice == 'always':
            # Disable confirmations for this tool this session
            session.disabled_confirmations.add(tool_call.tool_name)
            return True
        elif choice == 'never':
            # Add to permanently disabled confirmations
            add_to_user_preferences('disabled_confirmations', tool_call.tool_name)
            return False
```

### Stage 5: Result Synthesis

```python
def synthesize_response(result_parts: List[str]) -> str:
    """Combine tool results into coherent response"""
    
    if not result_parts:
        return "No results to display"
    
    if len(result_parts) == 1:
        return result_parts[0]
    
    # Multiple results - create structured summary
    synthesis = []
    for i, result in enumerate(result_parts, 1):
        if result.startswith("Error:"):
            synthesis.append(f"❌ Step {i}: {result}")
        else:
            synthesis.append(f"✅ Step {i}: {result}")
    
    return "\n".join(synthesis)
```

### Error Handling and Recovery

```python
def handle_processing_error(error: Exception, context: Dict) -> str:
    """Comprehensive error handling with recovery"""
    
    # Categorize error type
    if isinstance(error, APIError):
        return handle_api_error(error)
    elif isinstance(error, ToolError):
        return handle_tool_error(error, context.get('tool_name'))
    elif isinstance(error, ValidationError):
        return handle_validation_error(error)
    else:
        return handle_generic_error(error, context)

def handle_api_error(error: APIError) -> str:
    """Handle AI model API errors"""
    if error.status_code == 401:
        return "Authentication failed. Please check your API key configuration."
    elif error.status_code == 429:
        return "Rate limit exceeded. Please wait before trying again."
    elif error.status_code >= 500:
        return "AI service temporarily unavailable. Please try again later."
    else:
        return f"AI service error: {error.message}"
```

## Configuration Management

### Configuration Architecture

The configuration system provides flexible, hierarchical configuration management with secure credential handling:

```python
# Located in: infrastructure/config/

@dataclass
class TerminusConfig:
    """Main configuration data structure"""
    default_model: str
    models: Dict[str, ModelConfig]
    settings: UserSettings
    environment: Dict[str, str]
    
@dataclass  
class ModelConfig:
    """Model-specific configuration"""
    enabled: bool
    api_key: Optional[str]
    base_url: Optional[str]
    parameters: Dict[str, Any]

@dataclass
class UserSettings:
    """User preference settings"""
    confirmation_enabled: bool
    auto_save_sessions: bool
    max_session_history: int
    allowed_commands: Set[str]
    disabled_confirmations: Set[str]
```

### Configuration Files

**Primary Configuration**: `~/.config/terminus.json`
```json
{
  "default_model": "google-gla:gemini-2.0-flash-exp",
  "models": {
    "google": {
      "enabled": true,
      "api_key": "your-gemini-api-key",
      "parameters": {
        "temperature": 0.1,
        "max_tokens": 4096
      }
    },
    "ollama": {
      "enabled": true,
      "base_url": "http://localhost:11434/v1",
      "default_model": "qwen:latest",
      "parameters": {
        "temperature": 0.7
      }
    }
  },
  "settings": {
    "confirmation_enabled": true,
    "auto_save_sessions": true,
    "max_session_history": 1000,
    "allowed_commands": [
      "ls", "cat", "grep", "find", "pwd", "echo", "which",
      "head", "tail", "wc", "sort", "uniq", "diff", "tree"
    ],
    "disabled_confirmations": []
  }
}
```

### Configuration Loading and Validation

```python
# Located in: infrastructure/config/loader.py

class ConfigLoader:
    """Handles configuration loading with validation and merging"""
    
    @staticmethod
    def load_config() -> TerminusConfig:
        """Load configuration with fallback to defaults"""
        config_path = get_config_path()
        
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                return merge_with_defaults(user_config)
            except (json.JSONDecodeError, ValidationError) as e:
                handle_config_error(e)
                return create_default_config()
        else:
            return run_first_time_setup()
    
    @staticmethod
    def validate_config(config_data: Dict) -> Tuple[bool, List[str]]:
        """Validate configuration against schema"""
        errors = []
        
        # Validate required fields
        required_fields = ['default_model', 'models', 'settings']
        for field in required_fields:
            if field not in config_data:
                errors.append(f"Missing required field: {field}")
        
        # Validate model configurations
        for model_name, model_config in config_data.get('models', {}).items():
            model_errors = validate_model_config(model_name, model_config)
            errors.extend(model_errors)
        
        return len(errors) == 0, errors
```

### First-Time Setup

```python
# Located in: infrastructure/config/setup.py

class FirstTimeSetup:
    """Handles initial configuration setup"""
    
    def run_setup(self) -> TerminusConfig:
        """Interactive setup wizard"""
        
        display_welcome_screen()
        
        # Collect API credentials
        google_api_key = self.collect_google_api_key()
        ollama_enabled = self.check_ollama_availability()
        
        # Configure preferences
        settings = self.configure_user_settings()
        
        # Create configuration
        config = TerminusConfig(
            default_model="google-gla:gemini-2.0-flash-exp",
            models={
                "google": ModelConfig(
                    enabled=bool(google_api_key),
                    api_key=google_api_key,
                    parameters={"temperature": 0.1}
                ),
                "ollama": ModelConfig(
                    enabled=ollama_enabled,
                    base_url="http://localhost:11434/v1",
                    parameters={"temperature": 0.7}
                )
            },
            settings=settings,
            environment={}
        )
        
        # Save configuration
        save_config(config)
        
        return config
    
    def collect_google_api_key(self) -> Optional[str]:
        """Securely collect Google API key"""
        display_info_panel(
            "Google Gemini API Key Setup",
            "To use cloud AI models, you need a Google AI API key.\n"
            "Get one at: https://makersuite.google.com/app/apikey"
        )
        
        while True:
            api_key = getpass.getpass("Enter your Google API key (or press Enter to skip): ")
            if not api_key:
                return None
            
            if validate_google_api_key(api_key):
                return api_key
            else:
                print("Invalid API key format. Please try again.")
```

### Environment Variable Integration

```python
def setup_environment_variables(config: TerminusConfig):
    """Set up environment variables for model access"""
    
    # Google API key
    if config.models.get('google', {}).get('api_key'):
        os.environ['GEMINI_API_KEY'] = config.models['google']['api_key']
    
    # Ollama configuration
    if config.models.get('ollama', {}).get('enabled'):
        ollama_config = config.models['ollama']
        os.environ['OLLAMA_BASE_URL'] = ollama_config.get('base_url', 'http://localhost:11434')
    
    # Additional environment variables
    for key, value in config.environment.items():
        os.environ[key] = value
```

### Configuration Updates

```python
def update_configuration(updates: Dict[str, Any]) -> bool:
    """Update configuration with new values"""
    try:
        current_config = load_config()
        updated_config = deep_merge(current_config, updates)
        
        # Validate updated configuration
        is_valid, errors = validate_config(updated_config)
        if not is_valid:
            raise ValidationError(f"Invalid configuration: {', '.join(errors)}")
        
        # Save updated configuration
        save_config(updated_config)
        
        # Update runtime environment
        setup_environment_variables(updated_config)
        
        return True
        
    except Exception as e:
        handle_config_update_error(e)
        return False
```

## Project Structure

### Clean Architecture Implementation

The project follows clean architecture principles with clear separation of concerns:

```
terminus-cli/
├── pyproject.toml
├── README.md
├── ARCHITECTURE.md
│
├── src/terminus/
│   ├── __init__.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   ├── session.py
│   │   └── persistence.py
│   │
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── config/
│   │   │   ├── __init__.py
│   │   │   ├── loader.py
│   │   │   └── setup.py
│   │   └── models/
│   │       ├── __init__.py
│   │       ├── google.py
│   │       └── ollama.py
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── wrapper.py
│   │   │
│   │   ├── filesystem/
│   │   │   ├── __init__.py
│   │   │   ├── read_file.py
│   │   │   ├── write_file.py
│   │   │   ├── update_file.py
│   │   │   ├── find.py
│   │   │   ├── grep.py
│   │   │   ├── list.py
│   │   │   ├── directory.py
│   │   │   └── file_discovery.py
│   │   │
│   │   ├── development/
│   │   │   ├── __init__.py
│   │   │   ├── git.py
│   │   │   ├── code_analysis.py
│   │   │   ├── dev_workflow.py
│   │   │   └── project_automation.py
│   │   │
│   │   ├── system/
│   │   │   ├── __init__.py
│   │   │   ├── run_command.py
│   │   │   └── system_utilities.py
│   │   │
│   │   ├── integrations/
│   │   │   ├── __init__.py
│   │   │   ├── gmail.py
│   │   │   ├── calendar.py
│   │   │   └── google_setup.py
│   │   │
│   │   └── help/
│   │       ├── __init__.py
│   │       └── help_system.py
│   │
│   ├── interface/
│   │   ├── __init__.py
│   │   └── cli/
│   │       ├── __init__.py
│   │       ├── __main__.py
│   │       ├── commands.py
│   │       ├── repl.py
│   │       └── ui/
│   │           ├── __init__.py
│   │           ├── core.py
│   │           ├── panels.py
│   │           ├── messages.py
│   │           ├── colors.py
│   │           └── formatting.py
│   │
│   ├── shared/
│   │   ├── __init__.py
│   │   ├── constants.py
│   │   ├── deps.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── error.py
│   │       ├── validation.py
│   │       └── file_operations.py
│   │
│   └── prompts/
│       ├── __init__.py
│       ├── system.txt
│       └── model_specific/
│           ├── google_gemini.txt
│           └── ollama_qwen.txt
│
├── build/
├── env/
└── sessions/
```
```

### Module Dependencies

**Core Layer**: Contains pure business logic with no external dependencies
- `core/agent.py`: Agent orchestration and workflow management
- `core/session.py`: Application state and context management
- `core/persistence.py`: Data serialization and storage

**Infrastructure Layer**: Handles external system integrations
- `infrastructure/config/`: Configuration management and validation
- `infrastructure/models/`: AI model provider implementations

**Tools Layer**: Implements all application functionality as discrete tools
- Organized by functional domain (filesystem, development, system, etc.)
- Each tool is independently testable and composable
- Clear separation between safe and confirmation-required operations

**Interface Layer**: Manages user interactions and presentation
- `interface/cli/`: Command-line interface implementation
- Rich terminal UI with consistent styling and responsive design

**Shared Layer**: Common utilities and dependency injection
- Application constants and configuration
- Error handling and validation utilities
- Dependency injection framework for tool execution

## Development Guidelines

### Adding New Tools

Follow these steps to add new tools to the system:

#### 1. Create Tool Implementation

```python
# Example: tools/filesystem/new_tool.py

async def new_filesystem_tool(ctx: RunContext[ToolDeps], parameter: str) -> str:
    """
    Brief description of the tool's purpose for AI agent understanding.
    
    This docstring is crucial as the AI agent uses it to determine when
    and how to use this tool. Be specific about:
    - What the tool does
    - What parameters it expects
    - What it returns
    - Any side effects or requirements
    
    Args:
        ctx: Runtime context with dependencies (confirmation, status display)
        parameter: Description of the expected parameter
        
    Returns:
        Result description or error message
    """
    try:
        # Input validation
        if not parameter:
            return "Error: Parameter is required"
        
        # Tool-specific implementation
        result = perform_tool_operation(parameter)
        
        # Progress updates for long operations
        if ctx.deps.display_tool_status:
            ctx.deps.display_tool_status("Processing...")
        
        # Confirmation for destructive operations
        if is_destructive_operation and ctx.deps.confirm_action:
            confirmed = await ctx.deps.confirm_action(
                title="Confirm Tool Operation",
                preview=generate_preview(parameter),
                footer="This action will modify the file system"
            )
            if not confirmed:
                return "Operation cancelled by user"
        
        return f"Successfully completed: {result}"
        
    except Exception as e:
        return f"Error executing tool: {str(e)}"
```

#### 2. Register Tool

```python
# Update tools/wrapper.py

from terminus.tools.filesystem.new_tool import new_filesystem_tool

def create_tools():
    """Create Tool instances for all tools."""
    return [
        # Existing tools...
        Tool(new_filesystem_tool),
        # Additional tools...
    ]
```

#### 3. Export Tool

```python
# Update tools/filesystem/__init__.py

from .new_tool import new_filesystem_tool

__all__ = [
    # Existing exports...
    'new_filesystem_tool',
]
```

### Tool Development Best Practices

**Type Hints**: Always use comprehensive type hints for parameters and return values
```python
async def tool_function(
    ctx: RunContext[ToolDeps], 
    file_path: str, 
    content: Optional[str] = None
) -> str:
```

**Clear Docstrings**: Write detailed docstrings that help the AI agent understand tool usage
```python
"""
Read file contents and return formatted output.

This tool safely reads file contents with automatic encoding detection
and provides syntax highlighting for code files. It handles large files
by truncating content and provides error messages for access issues.

Args:
    ctx: Runtime context for dependency injection
    file_path: Path to the file to read (relative or absolute)
    
Returns:
    Formatted file contents or error message if file cannot be read
"""
```

**Error Handling**: Return user-friendly error messages instead of raising exceptions
```python
try:
    result = perform_operation()
    return f"Success: {result}"
except FileNotFoundError:
    return f"Error: File '{file_path}' not found"
except PermissionError:
    return f"Error: Permission denied accessing '{file_path}'"
except Exception as e:
    return f"Error: {str(e)}"
```

**Safety Classification**: Consider whether your tool requires confirmation
```python
# For destructive operations, always use confirmation
if ctx.deps.confirm_action:
    confirmed = await ctx.deps.confirm_action(
        title="Destructive Operation",
        preview=show_what_will_be_affected,
        footer="This cannot be undone"
    )
    if not confirmed:
        return "Operation cancelled"
```


### Testing Guidelines

**Unit Tests**: Create comprehensive tests for each tool
```python
# tests/tools/filesystem/test_new_tool.py

import pytest
from unittest.mock import AsyncMock, MagicMock

from terminus.tools.filesystem.new_tool import new_filesystem_tool
from terminus.shared.deps import ToolDeps

@pytest.mark.asyncio
async def test_new_tool_success():
    """Test successful tool execution."""
    # Setup
    mock_deps = ToolDeps(
        confirm_action=AsyncMock(return_value=True),
        display_tool_status=MagicMock()
    )
    mock_ctx = MagicMock()
    mock_ctx.deps = mock_deps
    
    # Execute
    result = await new_filesystem_tool(mock_ctx, "test_parameter")
    
    # Assert
    assert "Successfully completed" in result
    mock_deps.display_tool_status.assert_called()

@pytest.mark.asyncio
async def test_new_tool_user_cancellation():
    """Test tool cancellation by user."""
    # Setup
    mock_deps = ToolDeps(
        confirm_action=AsyncMock(return_value=False),
        display_tool_status=MagicMock()
    )
    mock_ctx = MagicMock()
    mock_ctx.deps = mock_deps
    
    # Execute
    result = await new_filesystem_tool(mock_ctx, "test_parameter")
    
    # Assert
    assert "cancelled by user" in result
```

**Integration Tests**: Test tool combinations and workflows
```python
@pytest.mark.asyncio
async def test_tool_workflow():
    """Test multiple tools working together."""
    # Test that tools can be chained together effectively
    pass
```

### UI Development Guidelines

**Consistent Styling**: Use established color schemes and panel types
```python
from terminus.interface.cli.ui.colors import Colors
from terminus.interface.cli.ui.panels import display_tool_panel

# Use consistent colors
display_tool_panel(
    content=formatted_output,
    title=f"[{Colors.info}]Tool Output[/{Colors.info}]",
    footer=f"[{Colors.muted}]Operation completed[/{Colors.muted}]"
)
```

**Responsive Design**: Consider different terminal sizes and contexts
```python
def format_output_for_terminal(content: str, max_width: int = 80) -> str:
    """Format content to fit terminal width."""
    lines = content.split('\n')
    formatted_lines = []
    
    for line in lines:
        if len(line) <= max_width:
            formatted_lines.append(line)
        else:
            # Wrap long lines appropriately
            wrapped = wrap_line(line, max_width)
            formatted_lines.extend(wrapped)
    
    return '\n'.join(formatted_lines)
```

### Documentation Standards

**API Documentation**: Document all public interfaces
**Architecture Decisions**: Record significant design choices
**User Guides**: Provide clear examples and usage patterns
**Troubleshooting**: Include common issues and solutions

### Version Control Practices

**Commit Messages**: Use clear, descriptive commit messages
```
feat: add new file analysis tool for project insights
fix: resolve confirmation dialog timeout issue  
docs: update tool development guidelines
refactor: reorganize UI components for better maintainability
```

**Branch Strategy**: Use feature branches for new development
```
feature/new-tool-implementation
bugfix/confirmation-dialog-issue
docs/architecture-update
```

**Code Reviews**: All changes should be reviewed for:
- Code quality and consistency
- Test coverage and correctness
- Documentation completeness
- Security considerations
- Performance implications

This architecture enables Terminus CLI to maintain high code quality, extensibility, and user experience while supporting rapid development of new features and tools.

"""
Tool interfaces and abstract base classes for Terminus CLI.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Union

from pydantic_ai import RunContext


class ToolCategory(Enum):
    """Categories for organizing tools."""
    FILE_OPERATIONS = "file_ops"
    DEVELOPMENT = "dev_tools"
    ANALYSIS = "analysis"
    INTEGRATIONS = "integrations"
    SYSTEM = "system"


class ToolSafety(Enum):
    """Safety levels for tools."""
    SAFE = "safe"                    # Read-only operations
    CONFIRMABLE = "confirmable"      # Requires user confirmation
    RESTRICTED = "restricted"        # Admin/special permissions needed


@dataclass
class ToolMetadata:
    """Metadata describing a tool."""
    name: str
    description: str
    category: ToolCategory
    safety_level: ToolSafety
    version: str = "1.0.0"
    tags: List[str] = None
    examples: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.examples is None:
            self.examples = []


@dataclass
class ToolResult:
    """Result of a tool execution."""
    success: bool
    data: Any = None
    message: str = ""
    error: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    @classmethod
    def success_result(cls, data: Any = None, message: str = "") -> "ToolResult":
        """Create a successful result."""
        return cls(success=True, data=data, message=message)

    @classmethod
    def error_result(cls, error: str, data: Any = None) -> "ToolResult":
        """Create an error result."""
        return cls(success=False, error=error, data=data)


class ToolContext(Protocol):
    """Context passed to tools during execution."""
    
    @property
    def working_directory(self) -> str:
        """Current working directory."""
        ...
    
    @property
    def session_data(self) -> Dict[str, Any]:
        """Session-specific data."""
        ...
    
    async def confirm_action(self, title: str, preview: str, details: str = "") -> bool:
        """Request user confirmation for an action."""
        ...
    
    async def display_status(self, message: str, **kwargs) -> None:
        """Display status information to the user."""
        ...


class BaseTool(ABC):
    """Abstract base class for all tools."""
    
    def __init__(self):
        self._metadata = self.get_metadata()
    
    @property
    def metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return self._metadata
    
    @abstractmethod
    def get_metadata(self) -> ToolMetadata:
        """Return tool metadata."""
        pass
    
    @abstractmethod
    async def execute(self, context: ToolContext, **kwargs) -> ToolResult:
        """Execute the tool with given parameters."""
        pass
    
    async def validate_parameters(self, **kwargs) -> Dict[str, Any]:
        """Validate and process parameters before execution."""
        return kwargs
    
    async def pre_execute(self, context: ToolContext, **kwargs) -> bool:
        """Pre-execution hook. Return False to abort execution."""
        return True
    
    async def post_execute(self, context: ToolContext, result: ToolResult) -> ToolResult:
        """Post-execution hook. Can modify the result."""
        return result


class FileOperationTool(BaseTool):
    """Base class for file operation tools."""
    
    def get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name=self.__class__.__name__,
            description="File operation tool",
            category=ToolCategory.FILE_OPERATIONS,
            safety_level=ToolSafety.SAFE
        )


class DevelopmentTool(BaseTool):
    """Base class for development tools."""
    
    def get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name=self.__class__.__name__,
            description="Development tool",
            category=ToolCategory.DEVELOPMENT,
            safety_level=ToolSafety.CONFIRMABLE
        )


class AnalysisTool(BaseTool):
    """Base class for analysis tools."""
    
    def get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name=self.__class__.__name__,
            description="Analysis tool",
            category=ToolCategory.ANALYSIS,
            safety_level=ToolSafety.SAFE
        )


class IntegrationTool(BaseTool):
    """Base class for integration tools."""
    
    def get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name=self.__class__.__name__,
            description="Integration tool",
            category=ToolCategory.INTEGRATIONS,
            safety_level=ToolSafety.CONFIRMABLE
        )


class ToolRegistry:
    """Registry for managing tool registration and discovery."""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._categories: Dict[ToolCategory, List[str]] = {
            category: [] for category in ToolCategory
        }
    
    def register(self, tool: BaseTool) -> None:
        """Register a tool."""
        tool_name = tool.metadata.name
        self._tools[tool_name] = tool
        self._categories[tool.metadata.category].append(tool_name)
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def list_tools(self, category: Optional[ToolCategory] = None) -> List[str]:
        """List tools, optionally filtered by category."""
        if category:
            return self._categories.get(category, []).copy()
        return list(self._tools.keys())
    
    def get_tools_by_category(self) -> Dict[ToolCategory, List[str]]:
        """Get tools organized by category."""
        return {
            category: tools.copy() 
            for category, tools in self._categories.items()
        }
    
    def get_tool_metadata(self, name: str) -> Optional[ToolMetadata]:
        """Get metadata for a tool."""
        tool = self._tools.get(name)
        return tool.metadata if tool else None


# Global tool registry instance
tool_registry = ToolRegistry()

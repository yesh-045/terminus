"""
Interfaces and protocols for Terminus CLI.
"""

from .tool_interfaces import (
    BaseTool,
    ToolCategory,
    ToolContext,
    ToolMetadata,
    ToolRegistry,
    ToolResult,
    ToolSafety,
    FileOperationTool,
    DevelopmentTool,
    AnalysisTool,
    IntegrationTool,
    tool_registry,
)

__all__ = [
    "BaseTool",
    "ToolCategory",
    "ToolContext",
    "ToolMetadata",
    "ToolRegistry",
    "ToolResult",
    "ToolSafety",
    "FileOperationTool",
    "DevelopmentTool",
    "AnalysisTool",
    "IntegrationTool",
    "tool_registry",
]

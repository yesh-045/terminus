from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ToolDeps:
    """Dependencies passed to tools via RunContext."""
    # Use Any to avoid Pydantic JSON schema generation for Callable types
    confirm_action: Optional[Any] = None
    display_tool_status: Optional[Any] = None

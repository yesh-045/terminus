import asyncio
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Set

from ..constants import DEFAULT_MODEL


@dataclass
class Session:
    current_model: str = DEFAULT_MODEL
    agents: Dict = field(default_factory=dict)
    messages: list = field(default_factory=list)
    spinner: Any = None
    spinner_rotation_task: Optional[asyncio.Task] = None
    current_task: Optional[asyncio.Task] = None
    sigint_received: bool = False
    allowed_commands: Set[str] = field(default_factory=set)
    disabled_confirmations: Set[str] = field(default_factory=set)
    confirmation_enabled: bool = True
    debug_enabled: bool = False
    log_file: Optional[str] = None
    project_guide: Optional[str] = None
    # Enhanced: Directory awareness
    working_directory: Optional[Path] = None

    def init(self, config: Dict[str, Any], model: str):
        """Initialize the session state."""
        self.current_model = model
        self.working_directory = Path.cwd()  # Initialize with current directory

        if "settings" in config:
            if "allowed_commands" in config["settings"]:
                self.allowed_commands.update(config["settings"]["allowed_commands"])

    def change_directory(self, path: str) -> str:
        """Change the session's working directory."""
        try:
            new_path = Path(path).resolve()
            if new_path.exists() and new_path.is_dir():
                self.working_directory = new_path
                # Also change the actual process directory for subprocess compatibility
                os.chdir(new_path)
                return f"Changed directory to: {new_path}"
            else:
                return f"Error: Directory does not exist: {path}"
        except Exception as e:
            return f"Error changing directory: {str(e)}"

    def get_cwd(self) -> str:
        """Get the current working directory."""
        if self.working_directory is None:
            self.working_directory = Path.cwd()
        return str(self.working_directory)

    def resolve_path(self, path: str) -> Path:
        """Resolve a path relative to the session's working directory."""
        if self.working_directory is None:
            self.working_directory = Path.cwd()
        path_obj = Path(path)
        if path_obj.is_absolute():
            return path_obj
        else:
            return self.working_directory / path_obj


# Create global session instance
session = Session()

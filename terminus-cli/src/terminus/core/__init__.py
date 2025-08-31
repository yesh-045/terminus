"""
Core functionality for Terminus CLI.
"""

from .session import session, Session
from .config import (
    ConfigError,
    ConfigValidationError,
    config_exists,
    ensure_config_structure,
    get_config_path,
    load_config,
    save_config,
    set_env_vars,
    validate_config_structure,
)
from .deps import ToolDeps

__all__ = [
    "session",
    "Session",
    "ConfigError",
    "ConfigValidationError", 
    "config_exists",
    "ensure_config_structure",
    "get_config_path",
    "load_config",
    "save_config",
    "set_env_vars",
    "validate_config_structure",
    "ToolDeps",
]

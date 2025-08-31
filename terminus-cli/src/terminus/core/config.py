"""Configuration management for terminus CLI."""

import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict, Optional

from ..constants import DEFAULT_USER_CONFIG


class ConfigError(Exception):
    """Base exception for configuration errors."""

    pass


class ConfigValidationError(ConfigError):
    """Raised when config structure is invalid."""

    pass


def get_config_path() -> Path:
    """Get the path to the config file."""
    return Path.home() / ".config" / "terminus.json"


def config_exists() -> bool:
    """Check if the config file exists."""
    return get_config_path().exists()


def read_config_file() -> Dict[str, Any]:
    """Read and parse the config file.

    Returns:
        dict: Parsed configuration

    Raises:
        ConfigError: If config file doesn't exist or can't be accessed
        ConfigValidationError: If config file contains invalid JSON
    """
    config_path = get_config_path()

    if not config_path.exists():
        raise ConfigError(f"Config file not found at {config_path}")

    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except PermissionError as e:
        raise ConfigError(f"Cannot access config file at {config_path}") from e
    except json.JSONDecodeError as e:
        raise ConfigValidationError(f"Invalid JSON in config file at {config_path}") from e


def validate_config_structure(config: Dict[str, Any]) -> None:
    """Validate the configuration structure.

    Args:
        config: Configuration dictionary to validate

    Raises:
        ConfigValidationError: If required fields are missing or invalid
    """
    if not isinstance(config, dict):
        raise ConfigValidationError("Config must be a JSON object")

    if "default_model" not in config:
        raise ConfigValidationError("Config missing required field 'default_model'")

    if not isinstance(config["default_model"], str):
        raise ConfigValidationError("'default_model' must be a string")

    if "env" not in config:
        raise ConfigValidationError("Config missing required field 'env'")

    if not isinstance(config["env"], dict):
        raise ConfigValidationError("'env' field must be an object")


def set_env_vars(env_dict: Dict[str, str]) -> None:
    """Set environment variables from config.

    Args:
        env_dict: Dictionary of environment variables to set
    """
    for key, value in env_dict.items():
        if value and isinstance(value, str):
            os.environ[key] = value


def update_config_file(updates: Dict[str, Any]) -> None:
    """Update the config file with new values.

    Args:
        updates: Dictionary of updates to apply to the config

    Raises:
        ConfigError: If config file cannot be read or written
    """
    try:
        config = read_config_file()
    except FileNotFoundError:
        raise ConfigError("Config file not found. Please run initial setup first.")

    # Merge updates into existing config
    for key, value in updates.items():
        if isinstance(value, dict) and key in config and isinstance(config[key], dict):
            # For nested dicts, merge instead of replace
            config[key].update(value)
        else:
            config[key] = value

    # Write updated config back to file
    config_path = get_config_path()

    # Ensure the config directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
    except (PermissionError, IOError) as e:
        raise ConfigError(f"Failed to write config file: {e}")


def deep_merge_dicts(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries, preserving existing values in update.

    Args:
        base: Base dictionary with default values
        update: Dictionary with user values to preserve

    Returns:
        Merged dictionary with all keys from base and values from update where they exist
    """
    result = base.copy()

    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value

    return result


def ensure_config_structure() -> Dict[str, Any]:
    """Ensure the config file has all expected keys with defaults for missing ones.

    This function reads the existing config, merges it with the default structure,
    and writes back the updated config if any keys were missing.

    Returns:
        The updated configuration dictionary

    Raises:
        ConfigError: If config file cannot be read or written
    """
    try:
        config = read_config_file()
    except ConfigError:
        raise

    original_config = json.dumps(config, sort_keys=True)
    merged_config = deep_merge_dicts(DEFAULT_USER_CONFIG, config)
    updated_config = json.dumps(merged_config, sort_keys=True)

    if original_config != updated_config:
        try:
            config_path = get_config_path()
            with open(config_path, "w") as f:
                json.dump(merged_config, f, indent=2)
        except (PermissionError, IOError) as e:
            raise ConfigError(f"Failed to update config file with missing keys: {e}")

    return merged_config


def backup_config() -> Optional[Path]:
    """Create a backup of the current config file.

    Returns:
        Path to the backup file if successful, None if no config exists
    """
    config_path = get_config_path()

    if not config_path.exists():
        return None

    # Create backup with timestamp
    import datetime

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = config_path.with_suffix(f".backup_{timestamp}.json")

    try:
        shutil.copy2(config_path, backup_path)
        return backup_path
    except (PermissionError, IOError):
        return None


def reset_config(create_backup: bool = True) -> Dict[str, Any]:
    """Reset configuration to defaults.

    Args:
        create_backup: Whether to create a backup of the current config

    Returns:
        The new default configuration

    Raises:
        ConfigError: If config cannot be reset
    """
    config_path = get_config_path()
    backup_path = None

    # Create backup if requested and config exists
    if create_backup and config_path.exists():
        backup_path = backup_config()

    try:
        # Ensure the directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Write default config
        with open(config_path, "w") as f:
            json.dump(DEFAULT_USER_CONFIG, f, indent=2)

        result = {
            "message": "Configuration reset to defaults",
            "config_path": str(config_path),
            "backup_path": str(backup_path) if backup_path else None,
        }

        return DEFAULT_USER_CONFIG.copy()

    except (PermissionError, IOError) as e:
        # If we created a backup, try to restore it
        if backup_path and backup_path.exists():
            try:
                shutil.copy2(backup_path, config_path)
            except Exception:
                pass  # Best effort restoration

        raise ConfigError(f"Failed to reset configuration: {e}")


def restore_config_from_backup(backup_path: Path) -> Dict[str, Any]:
    """Restore configuration from a backup file.

    Args:
        backup_path: Path to the backup file

    Returns:
        The restored configuration

    Raises:
        ConfigError: If backup cannot be restored
    """
    if not backup_path.exists():
        raise ConfigError(f"Backup file not found: {backup_path}")

    config_path = get_config_path()

    try:
        # Validate backup file first
        with open(backup_path, "r") as f:
            backup_config = json.load(f)

        # Restore the backup
        shutil.copy2(backup_path, config_path)

        return backup_config

    except (json.JSONDecodeError, PermissionError, IOError) as e:
        raise ConfigError(f"Failed to restore config from backup: {e}")


def list_config_backups() -> list[Path]:
    """List available config backup files.

    Returns:
        List of backup file paths, sorted by creation time (newest first)
    """
    config_path = get_config_path()
    config_dir = config_path.parent

    if not config_dir.exists():
        return []

    backups = []
    for file_path in config_dir.glob("terminus.backup_*.json"):
        backups.append(file_path)

    # Sort by modification time (newest first)
    backups.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return backups


def clean_old_backups(keep_count: int = 5) -> int:
    """Clean up old backup files, keeping only the most recent ones.

    Args:
        keep_count: Number of backup files to keep

    Returns:
        Number of backup files deleted
    """
    backups = list_config_backups()

    if len(backups) <= keep_count:
        return 0

    deleted_count = 0
    for backup_path in backups[keep_count:]:
        try:
            backup_path.unlink()
            deleted_count += 1
        except (PermissionError, IOError):
            continue  # Skip files we can't delete

    return deleted_count


def load_config() -> Optional[Dict[str, Any]]:
    """Load configuration from file.
    
    Returns:
        Configuration dictionary or None if file doesn't exist
    """
    try:
        return read_config_file()
    except ConfigError:
        return None


def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to file.
    
    Args:
        config: Configuration dictionary to save
        
    Raises:
        ConfigError: If config cannot be saved
    """
    config_path = get_config_path()
    
    # Ensure the config directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
    except (PermissionError, IOError) as e:
        raise ConfigError(f"Failed to save config file: {e}")

import json
from pathlib import Path
from typing import Dict, Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from .config import deep_merge_dicts, ensure_config_structure, read_config_file
from ..constants import DEFAULT_USER_CONFIG

console = Console()


def validate_json_file(config_path: Path) -> Optional[Dict]:
    """Validate if a JSON file is valid and return its content."""
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return None


def collect_api_keys() -> Dict[str, str]:
    """Collect API keys from user input."""
    console.print("\n[bold]API Keys Configuration[/bold]\n")
    
    api_keys = {}
    
    # Gemini API Key
    console.print("Enter your Gemini API key:")
    value = Prompt.ask("Google Gemini API Key", password=True, default="")
    if value:
        api_keys["GEMINI_API_KEY"] = value

    # Google API Credentials (optional)
    console.print("\n[bold]Google Services (Gmail & Calendar) - Optional[/bold]")
    console.print("To enable Gmail and Calendar features, you need Google API credentials.")
    console.print("Get them from: https://console.developers.google.com")
    
    setup_google = Confirm.ask("Set up Google API credentials now?", default=False)
    if setup_google:
        client_id = Prompt.ask("Google OAuth2 Client ID", default="")
        if client_id:
            api_keys["GOOGLE_CLIENT_ID"] = client_id
            
        client_secret = Prompt.ask("Google OAuth2 Client Secret", password=True, default="")
        if client_secret:
            api_keys["GOOGLE_CLIENT_SECRET"] = client_secret
            
        if client_id and client_secret:
            console.print("[green]✓ Google API credentials configured[/green]")
            console.print("Note: You'll complete OAuth setup when first using Gmail/Calendar features.")

    return api_keys


def create_config(config_path: Path) -> Dict:
    """Create a new configuration file."""
    console.print(
        Panel.fit(
            "[bold cyan]terminus Setup[/bold cyan]\n\n"
            "Welcome! Let's configure your terminal automation assistant.",
            border_style="cyan",
        )
    )

    api_keys = collect_api_keys()

    if not api_keys:
        console.print("\n[red]No API keys provided. At least one API key is required.[/red]")
        if not Confirm.ask("Continue anyway?", default=False):
            raise KeyboardInterrupt("Setup cancelled")

    # Start with user's choices
    user_config = {"default_model": DEFAULT_USER_CONFIG["default_model"], "env": api_keys if api_keys else {}}

    # Merge with defaults to get all fields
    config = deep_merge_dicts(DEFAULT_USER_CONFIG, user_config)

    # Remove placeholder API keys if user didn't provide any
    if not api_keys:
        config["env"] = {}

    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    console.print(f"\n[green]✓ Configuration saved to {config_path}[/green]")

    return config


def handle_invalid_config(config_path: Path) -> Dict:
    """Handle invalid configuration file."""
    console.print(
        Panel.fit(
            "[bold red]Invalid Configuration File[/bold red]\n\n"
            f"The configuration file at {config_path} is invalid or corrupted.",
            border_style="red",
        )
    )

    console.print("\nOptions:")
    console.print("1. Reset configuration (create backup and reset to defaults)")
    console.print("2. Delete configuration (remove file completely)")
    console.print("3. Exit and fix manually")

    choice = Prompt.ask("\nWhat would you like to do?", choices=["1", "2", "3"])

    if choice == "1":
        from terminus.config import reset_config
        try:
            reset_config(create_backup=True)
            console.print("[green]✓[/green] Configuration reset successfully (backup created)")
            return read_config_file()
        except Exception as e:
            console.print(f"[red]Error resetting config: {e}[/red]")
            raise SystemExit("Failed to reset configuration")
    elif choice == "2":
        config_path.unlink()
        return create_config(config_path)
    else:
        raise SystemExit("Please fix the configuration file manually and try again.")


def run_setup() -> Dict:
    """Run the setup flow and return the configuration."""
    config_path = Path.home() / ".config" / "terminus.json"

    if config_path.exists():
        config = validate_json_file(config_path)
        if config is None:
            return handle_invalid_config(config_path)

        required_fields = ["default_model", "env"]
        if all(field in config for field in required_fields):
            # Ensure all default fields are present
            return ensure_config_structure()
        else:
            console.print("[yellow]Configuration file is missing required fields.[/yellow]")
            return handle_invalid_config(config_path)

    return create_config(config_path)

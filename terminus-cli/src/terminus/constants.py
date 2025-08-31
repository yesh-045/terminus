APP_NAME = "terminus"
APP_VERSION = "0.1.0"

# Simplified single model support
DEFAULT_MODEL = "google-gla:gemini-2.0-flash-exp"

# Non-destructive tools that should always be allowed without confirmation
ALLOWED_TOOLS = [
    "read_file",
    "find",
    "grep",
    "list_directory",
    # Gmail safe tools
    "list_unread",
    "search_email",
    # Calendar safe tools
    "check_availability",
    # Google setup tools
    "google_auth_status",
]

DEFAULT_USER_CONFIG = {
    "default_model": DEFAULT_MODEL,
    "env": {
        "GEMINI_API_KEY": "your-gemini-api-key",
        "GOOGLE_CLIENT_ID": "your-google-client-id",
        "GOOGLE_CLIENT_SECRET": "your-google-client-secret",
    },
    "gmail": {
        "max_emails_per_request": 50,
        "default_summary_length": "brief"
    },
    "calendar": {
        "default_event_duration": 60,
        "business_hours_start": "09:00",
        "business_hours_end": "17:00",
        "timezone": "UTC"
    },
    "settings": {
        "allowed_commands": [
            "ls",
            "cat",
            "grep",
            "rg",
            "find",
            "pwd",
            "echo",
            "which",
            "head",
            "tail",
            "wc",
            "sort",
            "uniq",
            "diff",
            "tree",
            "file",
            "stat",
            "du",
            "df",
            "ps",
            "top",
            "env",
            "date",
            "whoami",
            "hostname",
            "uname",
            "id",
            "groups",
            "history",
        ],
    },
}

"""Debug logging configuration for terminus CLI."""

import logging

from terminus.core.session import session
from terminus.ui.messages import muted as ui_muted


class UILogHandler(logging.Handler):
    """A logging handler that outputs messages to the UI's muted function."""

    def emit(self, record):
        spinner_was_active = False
        if session.spinner:
            spinner_was_active = True
            session.spinner.stop()

        ui_muted(self.format(record))

        if spinner_was_active:
            session.spinner.start()


def _is_allowed_module(name: str) -> bool:
    """Check if a logger name is from an allowed module."""
    # allowed = ["terminus", "openai", "google_genai", "anthropic", "pydantic_ai"]
    allowed = ["terminus"]
    return any(name == module or name.startswith(module + ".") for module in allowed)


def setup_logging(debug_enabled: bool):
    """Configure logging for debug mode or disable completely."""
    if debug_enabled:
        logging.root.setLevel(logging.DEBUG)

        handler = UILogHandler()
        handler.setFormatter(logging.Formatter("⚙︎ %(levelname)s (%(name)s): %(message)s"))
        handler.addFilter(lambda record: _is_allowed_module(record.name))

        logging.root.addHandler(handler)
    else:
        logging.disable(logging.CRITICAL)

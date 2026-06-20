"""
Application identity and version metadata.
"""

from pathlib import Path

PRODUCER_NAME = "Corbit"
PRODUCT_NAME = "Rivar"

_VERSION_FILE = Path(__file__).resolve().parents[2] / "VERSION"


def load_app_version() -> str:
    """
    Load app version from repository VERSION file.
    Falls back to a safe placeholder if the file is unavailable.
    """
    try:
        version = _VERSION_FILE.read_text(encoding="utf-8").strip()
        return version or "0.0.0"
    except Exception:
        return "0.0.0"


APP_VERSION = load_app_version()

from __future__ import annotations

from importlib import metadata
from pathlib import Path


PACKAGE_NAME = "research-draw"
VERSION_FILE = Path(__file__).resolve().parents[1] / "VERSION"
DEFAULT_VERSION = "0.0.0"


def _normalize(raw: str) -> str:
    value = str(raw).strip()
    if not value:
        return DEFAULT_VERSION
    return value.lstrip("vV")


def _read_version_file() -> str:
    try:
        text = VERSION_FILE.read_text(encoding="utf-8")
    except OSError:
        return DEFAULT_VERSION
    return _normalize(text)


def get_version() -> str:
    local = _read_version_file()
    if local != DEFAULT_VERSION:
        return local
    try:
        installed = metadata.version(PACKAGE_NAME)
    except metadata.PackageNotFoundError:
        return DEFAULT_VERSION
    except Exception:
        return DEFAULT_VERSION
    return _normalize(installed)


__version__ = get_version()
APP_VERSION = f"v{__version__}"
CLI_VERSION = f"ResearchDrawApp {APP_VERSION} (CLI Optimized)"

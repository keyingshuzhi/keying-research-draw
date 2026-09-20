from __future__ import annotations

from typing import Dict


EXTRA_HINTS: Dict[str, str] = {
    "data": "uv sync --extra data",
    "stats": "uv sync --extra stats",
    "ml": "uv sync --extra ml",
    "maps": "uv sync --extra maps",
    "raster": "uv sync --extra raster",
    "all": "uv sync --extra all",
}


def format_missing_dependency(
    package: str,
    feature: str,
    recommended_extra: str,
    fallback_pip: str | None = None,
) -> str:
    install_cmd = EXTRA_HINTS.get(recommended_extra, fallback_pip or f"uv add {package}")
    fallback_cmd = fallback_pip or f"uv add {package}"
    return (
        f"{feature} 需要依赖 `{package}`。建议安装：{install_cmd}。"
        f"如需单独安装：{fallback_cmd}"
    )

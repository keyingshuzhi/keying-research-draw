from __future__ import annotations

from typing import Dict


EXTRA_HINTS: Dict[str, str] = {
    "data": 'pip install -e ".[data]"',
    "stats": 'pip install -e ".[stats]"',
    "ml": 'pip install -e ".[ml]"',
    "maps": 'pip install -e ".[maps]"',
    "raster": 'pip install -e ".[raster]"',
    "all": 'pip install -e ".[all]"',
}


def format_missing_dependency(
    package: str,
    feature: str,
    recommended_extra: str,
    fallback_pip: str | None = None,
) -> str:
    install_cmd = EXTRA_HINTS.get(recommended_extra, fallback_pip or f"pip install {package}")
    fallback_cmd = fallback_pip or f"pip install {package}"
    return (
        f"{feature} 需要依赖 `{package}`。建议安装：{install_cmd}。"
        f"如需单独安装：{fallback_cmd}"
    )


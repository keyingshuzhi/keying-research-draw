from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional


def fig_ax_from(ret):
    if isinstance(ret, tuple) and len(ret) >= 2:
        return ret[0], ret[1]
    if hasattr(ret, "savefig"):
        import matplotlib.pyplot as plt

        return ret, plt.gca()
    raise TypeError("绘图函数返回值异常，期望 (fig, ax) 或 (fig, ax, *).")


def _slugify(text: str) -> str:
    text = text.strip()
    text = re.sub(r"[\/\\\:\*\?\"\<\>\|\s]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "figure"


def autosave_name(fig, fallback: Optional[str], plot_key: str, title: Optional[str]) -> str:
    if fallback:
        return fallback
    title_text: Optional[str] = None
    try:
        if getattr(fig, "_suptitle", None) is not None:
            title_text = fig._suptitle.get_text() or None
    except Exception:
        pass
    if not title_text:
        for ax in getattr(fig, "axes", []):
            t = (ax.get_title() or "").strip()
            if t:
                title_text = t
                break
    if title_text:
        return _slugify(title_text)
    if title:
        return _slugify(title)
    return f"{plot_key}_output"


def resolve_match_screen(args) -> bool:
    if getattr(args, "no_match_screen", False):
        return False
    if getattr(args, "match_screen", False):
        return True
    return True


def apply_outdir_override(args) -> None:
    if getattr(args, "outdir", None):
        os.environ["PLOT_OUTDIR_OVERRIDE"] = str(Path(args.outdir).expanduser().resolve())


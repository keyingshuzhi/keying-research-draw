from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

from src.registry import demo_data_path_for_plot, demo_defaults_for_map_plot
from src.save.export import autosave_name, fig_ax_from, resolve_match_screen


def demo_file_for_plot(plot: str, project_root: Path) -> Optional[Path]:
    return demo_data_path_for_plot(plot, project_root)


def apply_demo_map_defaults(args: Any, plot: str, project_root: Path) -> None:
    defaults = demo_defaults_for_map_plot(plot, project_root)
    if not defaults:
        return

    for key, value in defaults.items():
        if not hasattr(args, key):
            continue
        current = getattr(args, key)
        if current in (None, ""):
            setattr(args, key, value)


def finalize_plot_output(args: Any, plot_key: str, title: str | None, plotter: Any, rendered: Any) -> str:
    import matplotlib.pyplot as plt

    fig, _ax = fig_ax_from(rendered)
    save_name = autosave_name(fig, getattr(args, "save_name", None), plot_key, title)
    out = plotter.save(
        name=save_name,
        fig=fig,
        fmt=getattr(args, "fmt", None),
        dpi=getattr(args, "dpi", None),
        match_screen=resolve_match_screen(args),
        tight=getattr(args, "tight", False),
    )
    print(f"✅ Saved: {out}")

    no_show = bool(getattr(args, "no_show", False))
    if not no_show and os.environ.get("MPLBACKEND", "").lower() != "agg":
        try:
            plt.show()
        except Exception:
            pass
    else:
        try:
            plt.close(fig)
        except Exception:
            pass
    return out

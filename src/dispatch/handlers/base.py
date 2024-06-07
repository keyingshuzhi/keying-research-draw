from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class HandlerContext:
    args: Any
    project_root: Path
    static_plotter_cls: Any
    map_plotter_cls: Any
    plot3d_plotter_cls: Any


@dataclass(frozen=True)
class HandlerResult:
    plotter: Any
    rendered: Any
    plot_key: str
    title: str | None


class PlotHandler(Protocol):
    key: str

    def render(self, plot_key: str, mode: str) -> HandlerResult:
        ...

# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from src.cli import parse_cli_args
from src.config import ensure_matplotlib_backend
from src.dispatch import PlotDispatchExecutor
from src.plotters import get_3d_plotter_cls, get_map_plotter_cls, get_static_plotter_cls

ensure_matplotlib_backend()


class ResearchDrawApp:
    """
    Thin application entrypoint.
    - CLI parsing and config merge are handled in `src.cli.parser`
    - Plotter class discovery is handled in `src.plotters.factory`
    - Plot dispatching/execution is handled in `src.dispatch.executor`
    - Entry via package/module mode only (no runtime path injection).
    """

    def __init__(self, argv: Optional[List[str]] = None) -> None:
        self.this_dir = Path(__file__).resolve().parent
        self.project_root = self.this_dir.parent

        self.parser, self.args = parse_cli_args(argv)
        self.static_plotter_cls = get_static_plotter_cls(self.this_dir)
        self.map_plotter_cls = get_map_plotter_cls(self.this_dir)
        self.plot3d_plotter_cls = get_3d_plotter_cls(self.this_dir)
        self.executor = PlotDispatchExecutor(
            args=self.args,
            static_plotter_cls=self.static_plotter_cls,
            map_plotter_cls=self.map_plotter_cls,
            plot3d_plotter_cls=self.plot3d_plotter_cls,
            project_root=self.project_root,
        )

    def run(self) -> None:
        self.executor.run()


def main() -> None:
    ResearchDrawApp().run()


if __name__ == "__main__":
    main()

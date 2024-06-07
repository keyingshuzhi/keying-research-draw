from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Optional

from src.dispatch.handlers import Domain2DHandler, HandlerContext, MapHandler, Plot3DHandler, Static2DHandler
from src.dispatch.handlers.helpers import apply_demo_map_defaults, demo_file_for_plot, finalize_plot_output
from src.dispatch.routes import (
    apply_plot_side_effects,
    is_3d_plot,
    is_extended_plot,
    is_map_plot,
    normalize_mode,
    normalize_plot_name,
)
from src.save.export import apply_outdir_override


class PlotDispatchExecutor:
    def __init__(self, args, static_plotter_cls, map_plotter_cls, plot3d_plotter_cls, project_root: Path) -> None:
        self.args = args
        self.project_root = Path(project_root).resolve()
        self._context = HandlerContext(
            args=args,
            project_root=self.project_root,
            static_plotter_cls=static_plotter_cls,
            map_plotter_cls=map_plotter_cls,
            plot3d_plotter_cls=plot3d_plotter_cls,
        )
        self.handlers = self._build_handlers()

    def _build_handlers(self) -> Dict[str, object]:
        return {
            "static2d": Static2DHandler(self._context),
            "domain2d": Domain2DHandler(self._context),
            "plot3d": Plot3DHandler(self._context),
            "map": MapHandler(self._context),
        }

    def _demo_file_for_plot(self, plot: str) -> Optional[Path]:
        return demo_file_for_plot(plot, self.project_root)

    def _apply_demo_map_defaults(self, plot: str) -> None:
        apply_demo_map_defaults(self.args, plot, self.project_root)

    def _prepare_runtime(self, apply_side_effects: bool = True) -> None:
        if apply_side_effects:
            apply_plot_side_effects(self.args)
        apply_outdir_override(self.args)

        if os.environ.get("CI") or os.environ.get("HEADLESS"):
            import matplotlib

            self.args.no_show = True
            backend = matplotlib.get_backend().lower()
            if "agg" not in backend:
                try:
                    matplotlib.use("Agg")
                except Exception:
                    pass

    @staticmethod
    def _handler_key_for_plot(plot_key: str) -> str:
        if is_map_plot(plot_key):
            return "map"
        if is_3d_plot(plot_key):
            return "plot3d"
        if is_extended_plot(plot_key):
            return "domain2d"
        return "static2d"

    def _execute(self, handler_key: str, plot_key: str, mode: str) -> None:
        handler = self.handlers.get(handler_key)
        if handler is None:
            raise RuntimeError(f"未注册 handler：{handler_key}")
        result = handler.render(plot_key, mode)
        finalize_plot_output(
            args=self.args,
            plot_key=result.plot_key,
            title=result.title,
            plotter=result.plotter,
            rendered=result.rendered,
        )

    def run_demo_static(self) -> None:
        self._prepare_runtime(apply_side_effects=True)
        plot_key = normalize_plot_name(self.args.plot)
        handler_key = "domain2d" if is_extended_plot(plot_key) else "static2d"
        self._execute(handler_key, plot_key, "demo")

    def run_custom_static(self) -> None:
        self._prepare_runtime(apply_side_effects=True)
        plot_key = normalize_plot_name(self.args.plot)
        handler_key = "domain2d" if is_extended_plot(plot_key) else "static2d"
        self._execute(handler_key, plot_key, "custom")

    def run_file_static(self) -> None:
        self._prepare_runtime(apply_side_effects=True)
        plot_key = normalize_plot_name(self.args.plot)
        handler_key = "domain2d" if is_extended_plot(plot_key) else "static2d"
        self._execute(handler_key, plot_key, "file")

    def run_3d(self) -> None:
        self._prepare_runtime(apply_side_effects=True)
        plot_key = normalize_plot_name(self.args.plot)
        mode = normalize_mode(self.args.mode)
        self._execute("plot3d", plot_key, mode)

    def run_map(self) -> None:
        self._prepare_runtime(apply_side_effects=True)
        plot_key = normalize_plot_name(self.args.plot)
        mode = normalize_mode(self.args.mode)
        self._execute("map", plot_key, mode)

    def run(self) -> None:
        self._prepare_runtime(apply_side_effects=True)
        plot_key = normalize_plot_name(self.args.plot)
        mode = normalize_mode(self.args.mode)
        handler_key = self._handler_key_for_plot(plot_key)
        self._execute(handler_key, plot_key, mode)

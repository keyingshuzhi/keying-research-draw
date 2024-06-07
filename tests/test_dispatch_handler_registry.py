from __future__ import annotations

from src.cli.parser import build_parser
from src.dispatch.executor import PlotDispatchExecutor
from src.dispatch.routes import normalize_plot_name


def _new_executor(project_root, plot: str) -> PlotDispatchExecutor:
    parser = build_parser()
    args = parser.parse_args(["--mode", "demo", "--plot", plot])
    return PlotDispatchExecutor(
        args=args,
        static_plotter_cls=None,
        map_plotter_cls=None,
        plot3d_plotter_cls=None,
        project_root=project_root,
    )


def test_handler_registry_keys(project_root):
    ex = _new_executor(project_root, "box")
    assert set(ex.handlers.keys()) == {"static2d", "domain2d", "plot3d", "map"}


def test_handler_key_routing():
    assert PlotDispatchExecutor._handler_key_for_plot(normalize_plot_name("box")) == "static2d"
    assert PlotDispatchExecutor._handler_key_for_plot(normalize_plot_name("ma")) == "domain2d"
    assert PlotDispatchExecutor._handler_key_for_plot(normalize_plot_name("scatter3d")) == "plot3d"
    assert PlotDispatchExecutor._handler_key_for_plot(normalize_plot_name("world")) == "map"

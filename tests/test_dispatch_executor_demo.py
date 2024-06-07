from __future__ import annotations

import pytest

from src.cli.parser import build_parser
from src.dispatch.executor import PlotDispatchExecutor
from src.dispatch.routes import normalize_plot_name
from src.main import ResearchDrawApp


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


def test_apply_demo_map_defaults_choropleth_world(project_root):
    ex = _new_executor(project_root, "choropleth_world")
    ex._apply_demo_map_defaults(normalize_plot_name("choropleth_world"))
    assert str(ex.args.file).endswith("data/world_choropleth.csv")
    assert ex.args.key_col == "ISO_A3"
    assert ex.args.value_col == "value"
    assert ex.args.on == "iso_a3"
    assert ex.args.scheme in {"quantiles", "natural", "equal"}
    assert int(ex.args.k) >= 2


def test_apply_demo_map_defaults_choropleth_china(project_root):
    ex = _new_executor(project_root, "choropleth_china")
    ex._apply_demo_map_defaults(normalize_plot_name("choropleth_china"))
    assert str(ex.args.file).endswith("data/china_values.csv")
    assert ex.args.level == 1
    assert ex.args.key_col == "NAME_1"
    assert ex.args.value_col == "value"
    assert ex.args.on == "NAME"
    assert ex.args.scheme == "quantiles"
    assert ex.args.k == 5
    assert ex.args.cmap == "Reds"


def test_apply_demo_map_defaults_raster(project_root):
    ex = _new_executor(project_root, "raster")
    ex._apply_demo_map_defaults(normalize_plot_name("raster"))
    assert str(ex.args.raster_file).endswith(".tif")
    assert ex.args.basemap in {"world_admin0", "china_l1"}
    assert 0.0 <= float(ex.args.alpha) <= 1.0


def test_apply_demo_map_defaults_points(project_root):
    ex = _new_executor(project_root, "points")
    ex._apply_demo_map_defaults(normalize_plot_name("points"))
    assert str(ex.args.file).endswith("data/points_cn.csv")
    assert ex.args.lon_col == "lon"
    assert ex.args.lat_col == "lat"
    assert ex.args.label_col == "name"
    assert ex.args.hue_col == "category"
    assert ex.args.size_col == "value"
    assert ex.args.size_range == "24,180"
    assert ex.args.basemap in {"world_admin0", "china_l1"}


def test_demo_confusion_smoke(tmp_path):
    pytest.importorskip("pandas")
    outdir = tmp_path / "figures"
    app = ResearchDrawApp(
        [
            "--mode",
            "demo",
            "--plot",
            "confusion",
            "--no-show",
            "--outdir",
            str(outdir),
            "--save-name",
            "smoke_demo_confusion",
        ]
    )
    app.run()
    assert (outdir / "smoke_demo_confusion.png").exists()


def test_demo_upset_smoke(tmp_path):
    pytest.importorskip("pandas")
    outdir = tmp_path / "figures"
    app = ResearchDrawApp(
        [
            "--mode",
            "demo",
            "--plot",
            "upset",
            "--no-show",
            "--outdir",
            str(outdir),
            "--save-name",
            "smoke_demo_upset",
        ]
    )
    app.run()
    assert (outdir / "smoke_demo_upset.png").exists()

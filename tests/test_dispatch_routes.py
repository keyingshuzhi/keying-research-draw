from __future__ import annotations

import pytest

from src.dispatch.routes import (
    apply_plot_side_effects,
    is_3d_plot,
    is_extended_plot,
    is_map_plot,
    normalize_mode,
    normalize_plot_name,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("boxplot", "box"),
        ("小提琴图", "violin"),
        ("PR", "roc"),
        ("scatter3d", "plot3d_scatter"),
        ("surface3d", "plot3d_surface"),
        ("wireframe3d", "plot3d_wireframe"),
        ("contour3d", "plot3d_contour"),
        ("line3d", "plot3d_line"),
        ("isosurface3d", "plot3d_isosurface"),
        ("slice3d", "plot3d_slice"),
        ("quiver3d", "plot3d_quiver"),
        ("waterfall3d", "plot3d_waterfall"),
        ("embedding3d", "plot3d_embedding"),
        ("mesh3d", "plot3d_mesh"),
        ("choropleth_china", "map_choropleth_china"),
    ],
)
def test_normalize_plot_name(raw: str, expected: str):
    assert normalize_plot_name(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("demo", "demo"), ("演示", "demo"), ("文件", "file"), ("custom", "custom")],
)
def test_normalize_mode(raw: str, expected: str):
    assert normalize_mode(raw) == expected


def test_map_and_extended_detection():
    assert is_map_plot("map_world")
    assert not is_map_plot("box")
    assert is_3d_plot("plot3d_scatter")
    assert not is_3d_plot("scatter")
    assert is_extended_plot("ma")
    assert not is_extended_plot("volcano")


def test_apply_plot_side_effects():
    class _Args:
        plot = "pr"
        curve = None
        embed_method = None
        invert_x = False

    args = _Args()
    apply_plot_side_effects(args)
    assert args.curve == "pr"

    args.plot = "umap"
    apply_plot_side_effects(args)
    assert args.embed_method == "umap"

    args.plot = "ftir"
    apply_plot_side_effects(args)
    assert args.invert_x is True

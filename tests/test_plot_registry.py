from __future__ import annotations

from src.registry import (
    canonical_plots_by_group,
    demo_defaults_for_map_plot,
    normalize_plot_name,
    public_plot_name,
    required_fields_for_plot,
)


def test_registry_group_catalog_basic():
    grouped = canonical_plots_by_group()
    assert "stats_2d" in grouped
    assert "domain_2d" in grouped
    assert "plots_3d" in grouped
    assert "maps" in grouped
    assert "scatter3d" in grouped["plots_3d"]
    assert "choropleth_world" in grouped["maps"]


def test_registry_alias_normalization():
    assert normalize_plot_name("scatter3d") == "plot3d_scatter"
    assert normalize_plot_name("world") == "map_world"
    assert normalize_plot_name("PR") == "roc"
    assert public_plot_name("plot3d_scatter") == "scatter3d"
    assert public_plot_name("map_choropleth_world") == "choropleth_world"


def test_registry_required_fields():
    assert required_fields_for_plot("scatter3d") == ["x_col", "y_col", "z_col"]
    assert required_fields_for_plot("map_choropleth_world") == ["key_col", "value_col"]


def test_registry_map_demo_defaults(project_root):
    world = demo_defaults_for_map_plot("map_choropleth_world", project_root)
    assert world["key_col"] == "ISO_A3"
    assert world["value_col"] == "value"
    assert str(world["file"]).endswith("data/world_choropleth.csv")

    points = demo_defaults_for_map_plot("points", project_root)
    assert points["lon_col"] == "lon"
    assert points["lat_col"] == "lat"
    assert str(points["file"]).endswith("data/points_cn.csv")

from __future__ import annotations

from pathlib import Path

import pytest

from src.main import ResearchDrawApp


def test_demo_box_smoke(tmp_path):
    outdir = tmp_path / "figures"
    app = ResearchDrawApp(
        [
            "--mode",
            "demo",
            "--plot",
            "box",
            "--no-show",
            "--outdir",
            str(outdir),
            "--save-name",
            "smoke_demo_box",
        ]
    )
    app.run()
    assert (outdir / "smoke_demo_box.png").exists()


def test_demo_scatter3d_smoke(tmp_path):
    outdir = tmp_path / "figures"
    app = ResearchDrawApp(
        [
            "--mode",
            "demo",
            "--plot",
            "scatter3d",
            "--no-show",
            "--outdir",
            str(outdir),
            "--save-name",
            "smoke_demo_scatter3d",
        ]
    )
    app.run()
    assert (outdir / "smoke_demo_scatter3d.png").exists()


def test_demo_surface3d_smoke(tmp_path):
    outdir = tmp_path / "figures"
    app = ResearchDrawApp(
        [
            "--mode",
            "demo",
            "--plot",
            "surface3d",
            "--no-show",
            "--outdir",
            str(outdir),
            "--save-name",
            "smoke_demo_surface3d",
        ]
    )
    app.run()
    assert (outdir / "smoke_demo_surface3d.png").exists()


def test_demo_line3d_smoke(tmp_path):
    outdir = tmp_path / "figures"
    app = ResearchDrawApp(
        [
            "--mode",
            "demo",
            "--plot",
            "line3d",
            "--no-show",
            "--outdir",
            str(outdir),
            "--save-name",
            "smoke_demo_line3d",
        ]
    )
    app.run()
    assert (outdir / "smoke_demo_line3d.png").exists()


def test_demo_wireframe3d_smoke(tmp_path):
    outdir = tmp_path / "figures"
    app = ResearchDrawApp(
        [
            "--mode",
            "demo",
            "--plot",
            "wireframe3d",
            "--no-show",
            "--outdir",
            str(outdir),
            "--save-name",
            "smoke_demo_wireframe3d",
        ]
    )
    app.run()
    assert (outdir / "smoke_demo_wireframe3d.png").exists()


def test_demo_contour3d_smoke(tmp_path):
    outdir = tmp_path / "figures"
    app = ResearchDrawApp(
        [
            "--mode",
            "demo",
            "--plot",
            "contour3d",
            "--no-show",
            "--outdir",
            str(outdir),
            "--save-name",
            "smoke_demo_contour3d",
        ]
    )
    app.run()
    assert (outdir / "smoke_demo_contour3d.png").exists()


def test_demo_quiver3d_smoke(tmp_path):
    outdir = tmp_path / "figures"
    app = ResearchDrawApp(
        [
            "--mode",
            "demo",
            "--plot",
            "quiver3d",
            "--no-show",
            "--outdir",
            str(outdir),
            "--save-name",
            "smoke_demo_quiver3d",
        ]
    )
    app.run()
    assert (outdir / "smoke_demo_quiver3d.png").exists()


def test_demo_waterfall3d_smoke(tmp_path):
    outdir = tmp_path / "figures"
    app = ResearchDrawApp(
        [
            "--mode",
            "demo",
            "--plot",
            "waterfall3d",
            "--no-show",
            "--outdir",
            str(outdir),
            "--save-name",
            "smoke_demo_waterfall3d",
        ]
    )
    app.run()
    assert (outdir / "smoke_demo_waterfall3d.png").exists()


def test_demo_embedding3d_smoke(tmp_path):
    outdir = tmp_path / "figures"
    app = ResearchDrawApp(
        [
            "--mode",
            "demo",
            "--plot",
            "embedding3d",
            "--no-show",
            "--outdir",
            str(outdir),
            "--save-name",
            "smoke_demo_embedding3d",
        ]
    )
    app.run()
    assert (outdir / "smoke_demo_embedding3d.png").exists()


def test_demo_mesh3d_smoke(tmp_path):
    outdir = tmp_path / "figures"
    app = ResearchDrawApp(
        [
            "--mode",
            "demo",
            "--plot",
            "mesh3d",
            "--no-show",
            "--outdir",
            str(outdir),
            "--save-name",
            "smoke_demo_mesh3d",
        ]
    )
    app.run()
    assert (outdir / "smoke_demo_mesh3d.png").exists()


def test_demo_slice3d_smoke(tmp_path):
    outdir = tmp_path / "figures"
    app = ResearchDrawApp(
        [
            "--mode",
            "demo",
            "--plot",
            "slice3d",
            "--no-show",
            "--outdir",
            str(outdir),
            "--save-name",
            "smoke_demo_slice3d",
        ]
    )
    app.run()
    assert (outdir / "smoke_demo_slice3d.png").exists()


def test_demo_isosurface3d_smoke(tmp_path):
    pytest.importorskip("skimage")
    outdir = tmp_path / "figures"
    app = ResearchDrawApp(
        [
            "--mode",
            "demo",
            "--plot",
            "isosurface3d",
            "--no-show",
            "--outdir",
            str(outdir),
            "--save-name",
            "smoke_demo_isosurface3d",
        ]
    )
    app.run()
    assert (outdir / "smoke_demo_isosurface3d.png").exists()


def test_map_smoke_when_dependencies_and_data_exist(project_root, tmp_path):
    pytest.importorskip("geopandas")
    basemap_root = project_root / "data" / "geo"
    if not basemap_root.exists():
        pytest.skip("offline basemap not found")

    outdir = tmp_path / "figures"
    app = ResearchDrawApp(
        [
            "--plot",
            "world",
            "--no-show",
            "--outdir",
            str(outdir),
            "--save-name",
            "smoke_map_world",
            "--basemap-root",
            str(basemap_root),
        ]
    )
    app.run()
    assert (outdir / "smoke_map_world.png").exists()

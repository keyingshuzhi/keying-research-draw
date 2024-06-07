from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import List, Optional


def _try_import(modpath: str, attr: str):
    try:
        mod = __import__(modpath, fromlist=[attr])
        return getattr(mod, attr)
    except Exception:
        return None


def _load_from_candidates(candidates: List[Path], mod_name: str, attr: str):
    for path in candidates:
        if not path.exists():
            continue
        spec = importlib.util.spec_from_file_location(mod_name, path)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            sys.modules[mod_name] = mod
            spec.loader.exec_module(mod)
            return getattr(mod, attr)
    raise ImportError(f"未找到 {attr}，候选路径：\n" + "\n".join(str(x) for x in candidates))


def get_static_plotter_cls(src_dir: Path):
    cls = _try_import("src.chart.plot_2d.static_analysis", "StaticAnalysisPlotter")
    if cls is not None:
        return cls
    candidates = [
        src_dir / "chart" / "plot_2d" / "static_analysis.py",
        src_dir / "chart" / "plot-2d" / "static_analysis.py",
        src_dir / "chart" / "2D" / "static_analysis.py",
    ]
    return _load_from_candidates(candidates, "src.chart.plot_2d.static_analysis_dyn", "StaticAnalysisPlotter")


def get_map_plotter_cls(src_dir: Path):
    candidates_mod_cls = [
        ("src.chart.plot_2d.geo_atlas", "GeoAtlas"),
        ("src.chart.plot_2d.geo_atlas", "GeoAtlasPlotter"),
        ("src.chart.plot_2d.geo_atlas", "AtlasMapPlotter"),
        ("src.chart.plot_2d.geo_atlas", "MapPlotter"),
        ("src.chart.plot_2d.geo_atlas", "DomainMapPlotter"),
        ("src.chart.plot_2d.cartography", "CartographyPlotter"),
        ("src.chart.plot_2d.cartography", "DomainMapPlotter"),
        ("src.chart.plot_2d.geo_thematic", "GeoThematicPlotter"),
        ("src.chart.plot_2d.geo_thematic", "DomainMapPlotter"),
        ("src.chart.plot_2d.domain_analysis", "DomainMapPlotter"),
    ]
    for mod, cls_name in candidates_mod_cls:
        cls = _try_import(mod, cls_name)
        if cls is not None:
            return cls

    file_attr_pairs = [
        (src_dir / "chart" / "plot_2d" / "geo_atlas.py", "GeoAtlas"),
        (src_dir / "chart" / "plot_2d" / "geo_atlas.py", "GeoAtlasPlotter"),
        (src_dir / "chart" / "plot_2d" / "geo_atlas.py", "AtlasMapPlotter"),
        (src_dir / "chart" / "plot_2d" / "geo_atlas.py", "MapPlotter"),
        (src_dir / "chart" / "plot_2d" / "geo_atlas.py", "DomainMapPlotter"),
        (src_dir / "chart" / "plot_2d" / "cartography.py", "CartographyPlotter"),
        (src_dir / "chart" / "plot_2d" / "cartography.py", "DomainMapPlotter"),
        (src_dir / "chart" / "plot_2d" / "geo_thematic.py", "GeoThematicPlotter"),
        (src_dir / "chart" / "plot_2d" / "geo_thematic.py", "DomainMapPlotter"),
        (src_dir / "chart" / "plot_2d" / "domain_analysis.py", "DomainMapPlotter"),
    ]
    last_error: Optional[Exception] = None
    for path, attr in file_attr_pairs:
        try:
            return _load_from_candidates([path], f"{path.stem}_dyn", attr)
        except Exception as e:
            last_error = e
    if last_error:
        return None
    return None


def get_3d_plotter_cls(src_dir: Path):
    cls = _try_import("src.chart.plot_3d.scatter3d", "Scatter3DPlotter")
    if cls is not None:
        return cls
    candidates = [
        src_dir / "chart" / "plot_3d" / "scatter3d.py",
        src_dir / "chart" / "plot-3d" / "scatter3d.py",
        src_dir / "chart" / "3D" / "scatter3d.py",
    ]
    try:
        return _load_from_candidates(candidates, "src.chart.plot_3d.scatter3d_dyn", "Scatter3DPlotter")
    except Exception:
        return None

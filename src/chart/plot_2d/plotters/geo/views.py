from __future__ import annotations

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines

from src.chart.plot_2d.geo_atlas import (
    THEMES,
    LineString,
    MultiLineString,
    Point,
    _centroid_or_rep_point,
    _coerce_numeric_inplace,
    _first_present,
    _halo_text,
    _nice_palette,
    _resolve_col_name,
    format_missing_dependency,
    mc,
    pd,
    rasterio,
)

def plot_world_admin0(
        self,
        title: Optional[str] = "World Countries",
        figsize: Tuple[float, float] = (9.5, 5.8),
        edgecolor: Optional[str] = None,
        linewidth: float = 0.45,
        facecolor: Optional[str] = None,
        draw_grid: bool = True,
        crs: Optional[str | int] = None,
        highlight_countries: Optional[Sequence[str]] = None,
        label: bool = False,
        label_name: Optional[str] = None,
        ax: Optional[plt.Axes] = None,
) -> Tuple[plt.Figure, plt.Axes, gpd.GeoDataFrame]:
    t = THEMES.get(self.theme, THEMES["journal"])
    edgecolor = edgecolor or t["border"]
    facecolor = facecolor or t["land_face"]

    gdf = self._load_world_admin0()
    gdf = self._maybe_to_crs(gdf, crs)
    fig, ax = self._ensure_ax(ax, figsize)
    gdf.plot(ax=ax, edgecolor=edgecolor, linewidth=linewidth, facecolor=facecolor, zorder=1)
    self._outline_overlay(ax, gdf, color=t["border2"], lw=0.35, zorder=4)

    if highlight_countries:
        cols = list(gdf.columns)
        key = _first_present(cols, ["NAME_EN", "ADMIN", "NAME", "NAME_LONG"])
        if key:
            series = gdf[key].astype(str)
            target = {c.lower() for c in highlight_countries}
            mask = series.str.lower().isin(target)
            try:
                gdf.loc[mask].plot(ax=ax, facecolor="#FFD166", edgecolor="#D97706",
                                   linewidth=0.8, alpha=0.85, zorder=6)
            except Exception:
                pass
    if label:
        name_col = label_name or _first_present(list(gdf.columns), ["NAME_EN", "ADMIN", "NAME"])
        if name_col:
            self._label_gdf(ax, gdf, name_col)

    self._finalize_ax(ax, title, bounds=gdf.total_bounds, draw_grid=draw_grid, crs=gdf.crs)
    return fig, ax, gdf


def plot_world_admin1(
        self,
        countries: Optional[Sequence[str]] = None,
        title: Optional[str] = "World Admin1",
        figsize: Tuple[float, float] = (9.5, 5.8),
        edgecolor: Optional[str] = None,
        linewidth: float = 0.35,
        facecolor: Optional[str] = None,
        draw_grid: bool = True,
        crs: Optional[str | int] = None,
        label: bool = False,
        label_name: Optional[str] = None,
        country_field: Optional[str] = None,  # 指定 admin1 中“国别”列名（大小写不敏感）
        case_insensitive: bool = True,  # 国家名匹配是否大小写不敏感
        ax: Optional[plt.Axes] = None,
) -> Tuple[plt.Figure, plt.Axes, gpd.GeoDataFrame]:
    t = THEMES.get(self.theme, THEMES["journal"])
    edgecolor = edgecolor or t["border"]
    facecolor = facecolor or t["land_face"]

    gdf = self._load_world_admin1()
    cols = list(gdf.columns)
    lower_map = {c.lower(): c for c in cols}

    # —— 确定“国别”列 —— #
    key = None
    if country_field:
        key = lower_map.get(country_field.lower())
    if key is None:
        for cand in ("adm0_name", "admin", "name_en", "name", "country", "cntry_name"):
            if cand in lower_map:
                key = lower_map[cand]
                break
    if key is None:
        raise KeyError(
            "admin1 底图缺少国别字段；请用 country_field 指定。"
            f" 可用列示例：{cols[:15]}"
        )

    # —— 按国家筛选 —— #
    if countries:
        series = gdf[key].astype(str)
        if case_insensitive:
            target = set(c.lower() for c in countries)
            mask = series.str.lower().isin(target)
        else:
            mask = series.isin(set(countries))
        sub = gdf.loc[mask]
        if sub.empty:
            sample_vals = list(series.dropna().unique()[:12])
            raise ValueError(
                f"按国家筛选后为空。使用列: {key}；期望: {list(countries)}。"
                f" 示例可选值（前12）：{sample_vals}"
            )
        gdf = sub

    gdf = self._maybe_to_crs(gdf, crs)

    fig, ax = self._ensure_ax(ax, figsize)
    gdf.plot(ax=ax, edgecolor=edgecolor, linewidth=linewidth, facecolor=facecolor, zorder=1)
    self._outline_overlay(ax, gdf, color=t["border2"], lw=0.30, zorder=4)

    if label:
        if label_name:
            name_col = lower_map.get(label_name.lower())
        else:
            name_col = lower_map.get("name_en") or lower_map.get("name")
        if name_col:
            self._label_gdf(ax, gdf, name_col, fontsize=8, max_labels=120)

    self._finalize_ax(ax, title, bounds=gdf.total_bounds, draw_grid=draw_grid, crs=gdf.crs)
    return fig, ax, gdf

# ---------------- 底图：中国（完整性） ----------------

def plot_china(
        self,
        level: int = 1,
        title: Optional[str] = "China Admin (完整)",
        figsize: Tuple[float, float] = (7.6, 7.2),
        edgecolor: Optional[str] = None,
        linewidth: float = 0.45,
        facecolor: Optional[str] = None,
        draw_grid: bool = True,
        crs: Optional[str | int] = None,
        highlight_names: Optional[Sequence[str]] = None,
        on: Literal["NAME", "GID"] = "NAME",
        label: bool = False,
        ax: Optional[plt.Axes] = None,
) -> Tuple[plt.Figure, plt.Axes, gpd.GeoDataFrame]:
    t = THEMES.get(self.theme, THEMES["journal"])
    edgecolor = edgecolor or t["border"]
    facecolor = facecolor or t["land_face"]

    gdf = self._load_china_plus(level)
    gdf = self._maybe_to_crs(gdf, crs)

    fig, ax = self._ensure_ax(ax, figsize)
    gdf.plot(ax=ax, edgecolor=edgecolor, linewidth=linewidth, facecolor=facecolor, zorder=1)
    self._outline_overlay(ax, gdf, color=t["border2"], lw=0.35, zorder=4)

    if highlight_names:
        col = f"NAME_{level}" if on == "NAME" else f"GID_{level}"
        if col in gdf.columns:
            mask = gdf[col].isin(set(highlight_names))
            try:
                gdf.loc[mask].plot(ax=ax, facecolor="#FFD166", edgecolor="#D97706",
                                   linewidth=0.8, alpha=0.85, zorder=6)
            except Exception:
                pass

    if label:
        col = f"NAME_{level}" if on == "NAME" else f"GID_{level}"
        if col in gdf.columns:
            self._label_gdf(ax, gdf, col, fontsize=9, max_labels=100)

    self._finalize_ax(ax, title or f"China L{level}", bounds=gdf.total_bounds, draw_grid=draw_grid, crs=gdf.crs)
    return fig, ax, gdf

# ---------------- 分级着色 ----------------


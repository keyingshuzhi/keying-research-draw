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

def _plot_choropleth_core(
        self,
        gdf: gpd.GeoDataFrame,
        value_col: str,
        scheme: str,
        k: int,
        cmap: str,
        ax: plt.Axes,
        missing_color: str,
        legend_loc: str = "lower center",
        legend_orientation: str = "horizontal",
        linewidth: float = 0.25,
        edgecolor: str = "#FFFFFF",
):
    # GeoPandas + Matplotlib 不同版本对 legend_kwds 支持不一致，orientation 在部分版本会报错。
    _ = legend_orientation  # 保留参数兼容旧调用，但不传递给 legend_kwds。
    legend_kwds = dict(loc=legend_loc, frameon=False, fancybox=False, fontsize=9)

    if mc is not None:
        scheme_name = {
            "quantiles": "Quantiles",
            "equal": "EqualInterval",
            "natural": "NaturalBreaks",
        }.get(scheme, "Quantiles")
        gdf.plot(
            column=value_col,
            scheme=scheme_name,
            k=k,
            cmap=cmap,
            legend=True,
            legend_kwds=legend_kwds,
            ax=ax,
            missing_kwds={"color": missing_color, "edgecolor": "none", "hatch": "///", "label": "No data"},
            linewidth=linewidth,
            edgecolor=edgecolor,
            zorder=2,
        )
    else:
        series = gdf[value_col].dropna()
        if len(series) >= 2:
            vmin, vmax = float(series.min()), float(series.max())
        else:
            vmin, vmax = 0.0, 1.0
        gdf.plot(
            column=value_col,
            cmap=cmap,
            legend=True,
            vmin=vmin, vmax=vmax,
            ax=ax,
            linewidth=linewidth,
            edgecolor=edgecolor,
            zorder=2,
        )


def choropleth_world(
        self,
        df,  # pandas.DataFrame
        key_col: str,
        value_col: str,
        on: Literal["iso_a3", "name"] = "iso_a3",
        scheme: Literal["quantiles", "equal", "natural"] = "quantiles",
        k: int = 5,
        cmap: str = "journal",
        title: Optional[str] = "World Choropleth",
        figsize: Tuple[float, float] = (9.5, 5.8),
        draw_grid: bool = True,
        crs: Optional[str | int] = None,
        label_top_n: int = 0,
        ax: Optional[plt.Axes] = None,
) -> Tuple[plt.Figure, plt.Axes, gpd.GeoDataFrame]:
    t = THEMES.get(self.theme, THEMES["journal"])
    cmap = _nice_palette(cmap)

    # ------- 鲁棒解析列名（新增） -------
    key_real = _resolve_col_name(df.columns, key_col) or key_col
    val_real = _resolve_col_name(df.columns, value_col)
    if val_real is None:
        raise KeyError(f"找不到数值列 '{value_col}'；你的列有：{list(map(str, df.columns))[:12]} ...")
    if key_real != key_col:
        print(f"ℹ️ 依据 '{key_col}' 解析到列：'{key_real}'")
    if val_real != value_col:
        print(f"ℹ️ 依据 '{value_col}' 解析到列：'{val_real}'")
    _coerce_numeric_inplace(df, val_real)

    world = self._load_world_admin0()
    if on == "iso_a3":
        join_key = _first_present(list(world.columns), ["ISO_A3", "iso_a3"])
    else:
        join_key = _first_present(list(world.columns), ["NAME_EN", "ADMIN", "NAME_LONG", "NAME"])
    if join_key is None:
        raise KeyError(f"ne_admin0 缺少对齐列（on={on}），可用列示例：{list(world.columns)[:15]}")

    gdf = world.merge(df[[key_real, val_real]], left_on=join_key, right_on=key_real, how="left")
    gdf = self._maybe_to_crs(gdf, crs)

    fig, ax = self._ensure_ax(ax, figsize)
    self._plot_choropleth_core(
        gdf, val_real, scheme, k, cmap, ax,
        missing_color=t["miss"],
    )
    self._outline_overlay(ax, gdf, color=t["border2"], lw=0.35, zorder=3)

    if label_top_n > 0 and val_real in gdf.columns:
        try:
            top = gdf[[val_real, "geometry"]].dropna(subset=[val_real]).nlargest(label_top_n, val_real)
            for _, row in top.iterrows():
                x, y = _centroid_or_rep_point(row.geometry)
                _halo_text(ax, x, y, f"{row[val_real]:.2f}", color=t["text"], fontsize=8)
        except Exception:
            pass

    self._finalize_ax(ax, title, bounds=gdf.total_bounds, draw_grid=draw_grid, crs=gdf.crs)
    return fig, ax, gdf


def choropleth_china(
        self,
        df,  # pandas.DataFrame
        key_col: str,
        value_col: str,
        level: int = 1,
        on: Literal["NAME", "GID"] = "NAME",
        scheme: Literal["quantiles", "equal", "natural"] = "quantiles",
        k: int = 5,
        cmap: str = "Reds",
        title: Optional[str] = "China Choropleth (完整)",
        figsize: Tuple[float, float] = (7.6, 7.2),
        draw_grid: bool = True,
        crs: Optional[str | int] = None,
        label_top_n: int = 0,
        ax: Optional[plt.Axes] = None,
) -> Tuple[plt.Figure, plt.Axes, gpd.GeoDataFrame]:
    t = THEMES.get(self.theme, THEMES["journal"])
    cmap = _nice_palette(cmap)

    # ------- 鲁棒解析列名（新增） -------
    key_real = _resolve_col_name(df.columns, key_col) or key_col
    val_real = _resolve_col_name(df.columns, value_col)
    if val_real is None:
        # 兜底：若只有 1 列是纯数值列，则自动当 value 列
        if pd is not None:
            numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
            if len(numeric_cols) == 1:
                val_real = numeric_cols[0]
                print(f"ℹ️ 未找到 '{value_col}'，自动采用唯一数值列：'{val_real}'")
        if val_real is None:
            raise KeyError(f"找不到数值列 '{value_col}'；你的列有：{list(map(str, df.columns))[:12]} ...")
    if key_real != key_col:
        print(f"ℹ️ 依据 '{key_col}' 解析到列：'{key_real}'")
    if val_real != value_col:
        print(f"ℹ️ 依据 '{value_col}' 解析到列：'{val_real}'")
    _coerce_numeric_inplace(df, val_real)

    gdf = self._load_china_plus(level)
    col = f"NAME_{level}" if on == "NAME" else f"GID_{level}"
    if col not in gdf.columns:
        raise KeyError(f"GADM Level{level} 缺少字段：{col}；可用列示例：{list(gdf.columns)[:12]}")

    gdf = gdf.merge(df[[key_real, val_real]], left_on=col, right_on=key_real, how="left")
    gdf = self._maybe_to_crs(gdf, crs)

    fig, ax = self._ensure_ax(ax, figsize)
    self._plot_choropleth_core(
        gdf, val_real, scheme, k, cmap, ax,
        missing_color=t["miss"],
    )
    self._outline_overlay(ax, gdf, color=t["border2"], lw=0.35, zorder=3)

    if label_top_n > 0 and val_real in gdf.columns:
        try:
            top = gdf[[val_real, "geometry"]].dropna(subset=[val_real]).nlargest(label_top_n, val_real)
            for _, row in top.iterrows():
                x, y = _centroid_or_rep_point(row.geometry)
                _halo_text(ax, x, y, f"{row[val_real]:.2f}", color=t["text"], fontsize=8)
        except Exception:
            pass

    self._finalize_ax(ax, title or f"China L{level} Choropleth", bounds=gdf.total_bounds, draw_grid=draw_grid,
                      crs=gdf.crs)
    return fig, ax, gdf

# ---------------- 研究数据叠加（点/线/面） ----------------

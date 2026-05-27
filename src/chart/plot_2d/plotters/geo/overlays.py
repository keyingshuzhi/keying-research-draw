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

def overlay_points(
        self,
        ax: plt.Axes,
        gdf_points: gpd.GeoDataFrame,
        size: float = 36,
        size_col: Optional[str] = None,
        size_range: Tuple[float, float] = (24, 160),
        hue_col: Optional[str] = None,
        cmap: str = "viridis",
        categories_palette: Optional[List[str]] = None,
        alpha: float = 0.85,
        edgecolor: Optional[str] = None,
        linewidths: float = 0.6,
        legend: bool = True,
        legend_loc: str = "upper right",
        label_col: Optional[str] = None,
        label_fontsize: float = 8.5,
        crs: Optional[str | int] = None,
        zorder: int = 8,
):
    theme = THEMES.get(self.theme, THEMES["journal"])
    edgecolor = edgecolor or theme["point_edge"]
    g = gdf_points.copy()
    if crs:
        g = self._maybe_to_crs(g, crs)

    # 尺寸映射
    sizes = None
    if size_col and size_col in g.columns and np.issubdtype(g[size_col].dropna().dtype, np.number):
        v = g[size_col].astype(float)
        lo, hi = float(np.nanmin(v)), float(np.nanmax(v))
        if np.isfinite(lo) and np.isfinite(hi) and hi > lo:
            sizes = size_range[0] + (v - lo) / (hi - lo + 1e-12) * (size_range[1] - size_range[0])

    handles = []
    if hue_col and hue_col in g.columns:
        series = g[hue_col].dropna()
        if series.empty:
            hue_col = None
        else:
            if np.issubdtype(series.dtype, np.number):
                cmap = _nice_palette(cmap)
                coll = ax.scatter(
                    g.geometry.x, g.geometry.y,
                    s=(sizes if sizes is not None else size),
                    c=g[hue_col], cmap=cmap, alpha=alpha,
                    edgecolors=edgecolor, linewidths=linewidths, zorder=zorder,
                )
                if legend:
                    cbar = plt.colorbar(coll, ax=ax, fraction=0.035, pad=0.02)
                    cbar.ax.tick_params(labelsize=8)
            else:
                if pd is not None:
                    cats = list(pd.Categorical(g[hue_col]).categories)  # type: ignore
                else:
                    cats = sorted(series.dropna().unique())
                base = plt.get_cmap("tab20")
                colors = [base(i % base.N) for i in
                          range(len(cats))] if categories_palette is None else categories_palette[:len(cats)]
                for cat, c in zip(cats, colors):
                    sub = g[g[hue_col] == cat]
                    ax.scatter(sub.geometry.x, sub.geometry.y,
                               s=(sizes.loc[sub.index] if (sizes is not None) else size),
                               color=c, alpha=alpha, edgecolors=edgecolor, linewidths=linewidths, zorder=zorder)
                    handles.append(
                        mlines.Line2D([], [], color=c, marker='o', linestyle='', markersize=6, label=str(cat)))
    if not hue_col:
        ax.scatter(g.geometry.x, g.geometry.y,
                   s=(sizes if sizes is not None else size),
                   color="#2F7ED8", alpha=alpha, edgecolors=edgecolor, linewidths=linewidths, zorder=zorder)

    if label_col and label_col in g.columns:
        for _, row in g.dropna(subset=[label_col]).iterrows():
            _halo_text(ax, row.geometry.x, row.geometry.y, str(row[label_col]),
                       color=theme["text"], fontsize=label_fontsize, zorder=zorder + 1)

    if legend and handles:
        ax.legend(handles=handles, loc=legend_loc, frameon=False, fontsize=8)


def overlay_lines(
        self,
        ax: plt.Axes,
        gdf_lines: gpd.GeoDataFrame,
        width: float = 1.2,
        width_col: Optional[str] = None,
        width_range: Tuple[float, float] = (0.8, 3.5),
        hue_col: Optional[str] = None,
        color: str = "#DD6B20",
        cmap: str = "plasma",
        alpha: float = 0.9,
        crs: Optional[str | int] = None,
        zorder: int = 7,
):
    g = gdf_lines.copy()
    if crs:
        g = self._maybe_to_crs(g, crs)

    # 预计算线宽映射
    def _width_for_row(row):
        if width_col and width_col in g.columns and np.issubdtype(g[width_col].dropna().dtype, np.number):
            vv = float(row.get(width_col, np.nan))
            lo = float(np.nanmin(g[width_col]))
            hi = float(np.nanmax(g[width_col]))
            if not np.isfinite(vv) or not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
                return width
            return width_range[0] + (vv - lo) / (hi - lo + 1e-12) * (width_range[1] - width_range[0])
        return width

    # 数值着色 or 固定颜色
    use_numeric_hue = (hue_col and hue_col in g.columns and
                       np.issubdtype(g[hue_col].dropna().dtype, np.number))
    if use_numeric_hue:
        vals = g[hue_col].astype(float)
        vmin, vmax = float(np.nanmin(vals)), float(np.nanmax(vals))
        cmap_obj = plt.get_cmap(_nice_palette(cmap))

    def _draw_geom(geom, c, w):
        try:
            if geom is None:
                return
            if isinstance(geom, LineString):
                xs, ys = geom.coords.xy
                ax.plot(xs, ys, color=c, linewidth=w, alpha=alpha, zorder=zorder)
            elif isinstance(geom, MultiLineString):
                for ls in geom.geoms:
                    xs, ys = ls.coords.xy
                    ax.plot(xs, ys, color=c, linewidth=w, alpha=alpha, zorder=zorder)
        except Exception:
            pass

    for _, row in g.iterrows():
        w = _width_for_row(row)
        if use_numeric_hue:
            v = float(row.get(hue_col, np.nan))
            if not np.isfinite(v):
                v = vmin
            c = cmap_obj((v - vmin) / (vmax - vmin + 1e-12))
        else:
            c = color
        _draw_geom(row.geometry, c, w)


def overlay_polygons(
        self,
        ax: plt.Axes,
        gdf_polys: gpd.GeoDataFrame,
        facecolor: str = "#F59E0B",
        edgecolor: str = "#9A3412",
        linewidth: float = 0.8,
        alpha: float = 0.35,
        value_col: Optional[str] = None,
        categorical: bool = False,
        cmap: str = "YlOrRd",
        crs: Optional[str | int] = None,
        zorder: int = 6,
):
    g = gdf_polys.copy()
    if crs:
        g = self._maybe_to_crs(g, crs)

    if value_col and value_col in g.columns:
        if categorical or not np.issubdtype(g[value_col].dropna().dtype, np.number):
            cats = sorted(g[value_col].dropna().unique())
            base = plt.get_cmap("tab20")
            color_map = {c: base(i % base.N) for i, c in enumerate(cats)}
            for c in cats:
                sub = g[g[value_col] == c]
                sub.plot(ax=ax, color=color_map[c], edgecolor=edgecolor, linewidth=linewidth, alpha=alpha,
                         zorder=zorder)
            handles = [mpatches.Patch(color=color_map[c], label=str(c)) for c in cats[:12]]
            if handles:
                ax.legend(handles=handles, loc="lower right", frameon=False, fontsize=8)
        else:
            cmap = _nice_palette(cmap)
            sub = g.dropna(subset=[value_col])
            coll = sub.plot(ax=ax, column=value_col, cmap=cmap, linewidth=linewidth, edgecolor=edgecolor,
                            alpha=alpha, zorder=zorder)
            # 取第一个 mappable，兼容不同版本
            mappable = None
            try:
                if hasattr(coll, "collections") and coll.collections:
                    mappable = coll.collections[0]
            except Exception:
                pass
            if mappable is not None:
                plt.colorbar(mappable, ax=ax, fraction=0.035, pad=0.02)
    else:
        g.plot(ax=ax, facecolor=facecolor, edgecolor=edgecolor, linewidth=linewidth, alpha=alpha, zorder=zorder)

# 注记/标注

def annotate(
        self,
        ax: plt.Axes,
        gdf: gpd.GeoDataFrame,
        text_col: str,
        fontsize: float = 9,
        color: Optional[str] = None,
        max_labels: int = 100,
        zorder: int = 10,
):
    theme = THEMES.get(self.theme, THEMES["journal"])
    color = color or theme["text"]
    rows = gdf.dropna(subset=[text_col]).head(max_labels)
    for _, row in rows.iterrows():
        geom = row.geometry
        if geom is None:
            continue
        x, y = (geom.x, geom.y) if isinstance(geom, Point) else _centroid_or_rep_point(geom)
        _halo_text(ax, x, y, str(row[text_col]), color=color, fontsize=fontsize, zorder=zorder)

# 指北针 & 比例尺（修复坐标变换）

def add_north_arrow(self, ax: plt.Axes, xy=(0.95, 0.15), length=0.08, width=0.02, color="#111111", text="N"):
    x, y = xy
    ax.annotate(
        "", xy=(x, y + length), xytext=(x, y),
        xycoords="axes fraction", textcoords="axes fraction",
        arrowprops=dict(facecolor=color, edgecolor=color, width=8, headwidth=16, headlength=18),
        zorder=20,
    )
    ax.text(x, y + length + 0.03, text, transform=ax.transAxes, ha="center", va="bottom", color=color, fontsize=12,
            zorder=21)


def add_scalebar(self, ax: plt.Axes, length_km: Optional[float] = None, location: str = "lower left",
                 pad=(0.06, 0.06), height=0.012, color="#111111"):
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    is_lonlat = -200 <= xmin <= 200 and -200 <= xmax <= 200 and -90 <= ymin <= 90 and -90 <= ymax <= 90
    cx, cy = 0.5 * (xmin + xmax), 0.5 * (ymin + ymax)
    if is_lonlat:
        cosphi = np.cos(np.deg2rad(cy))
        km_per_deg_lon = 111.32 * max(0.1, abs(cosphi))
        raw = ((xmax - xmin) * km_per_deg_lon * 0.2) if length_km is None else length_km
        nice = self._nice_length(raw)
        deg_len = nice / km_per_deg_lon
    else:
        raw_m = (xmax - xmin) * 0.2 if length_km is None else length_km * 1000.0
        deg_len = self._nice_length(raw_m)

    if location == "lower left":
        ax0, ay0 = pad
    elif location == "lower right":
        ax0, ay0 = (1 - pad[0], pad[1])
    else:
        ax0, ay0 = pad

    # 两步式安全变换（Axes -> display -> data）
    try:
        disp_pt = ax.transAxes.transform((ax0, ay0))
        px0, py0 = ax.transData.inverted().transform(disp_pt)
        px1 = px0 + deg_len

        ax.plot([px0, px1], [py0, py0], color=color, linewidth=2.2, zorder=20)
        ax.plot([px0, px0 + deg_len / 2], [py0, py0], color=color, linewidth=5.0, zorder=19, alpha=0.15)
        ax.plot([px0 + deg_len / 2, px1], [py0, py0], color=color, linewidth=5.0, zorder=19, alpha=0.35)
        if is_lonlat:
            ax.text(px1, py0, f" {int(round((px1 - px0) * (111.32 * np.cos(np.deg2rad(cy)))))} km",
                    ha="left", va="center", color=color, fontsize=9, zorder=21)
        else:
            lab = f"{int(round(deg_len / 1000))} km" if deg_len >= 1000 else f"{int(round(deg_len))} m"
            ax.text(px1, py0, f" {lab}", ha="left", va="center", color=color, fontsize=9, zorder=21)
    except Exception:
        pass

@staticmethod

def _nice_length(raw: float) -> float:
    if raw <= 0:
        return 1.0
    exp = np.floor(np.log10(raw))
    base = raw / (10 ** exp)
    if base < 1.5:
        nice = 1.0
    elif base < 3.5:
        nice = 2.0
    elif base < 7.5:
        nice = 5.0
    else:
        nice = 10.0
    return nice * (10 ** exp)

# ---------------- 栅格叠加（加入路径兜底搜索） ----------------

def raster_on_map(
        self,
        raster_path: str | Path,
        title: Optional[str] = "Raster Overlay",
        figsize: Tuple[float, float] = (9.5, 5.8),
        alpha: float = 0.65,
        basemap: Literal["world_admin0", "china_l1", "none"] = "world_admin0",
        basemap_style: Optional[Dict] = None,
        draw_grid: bool = True,
        ax: Optional[plt.Axes] = None,
) -> Tuple[plt.Figure, plt.Axes]:
    if rasterio is None:
        raise RuntimeError(
            format_missing_dependency(
                package="rasterio",
                feature="raster_on_map",
                recommended_extra="raster",
            )
        )

    t = THEMES.get(self.theme, THEMES["journal"])
    basemap_style = basemap_style or {}

    fig, ax = self._ensure_ax(ax, figsize)
    g_bounds = None
    basemap_crs = None

    if basemap == "world_admin0":
        _, _, g = self.plot_world_admin0(
            title=None, figsize=figsize, ax=ax,
            edgecolor=basemap_style.get("edgecolor", t["border"]),
            linewidth=basemap_style.get("linewidth", 0.35),
            facecolor=basemap_style.get("facecolor", t["land_face"]),
            draw_grid=False,
        )
        g_bounds = tuple(map(float, np.asarray(g.total_bounds).ravel()))
        basemap_crs = g.crs
    elif basemap == "china_l1":
        _, _, g = self.plot_china(
            level=1, title=None, figsize=figsize, ax=ax,
            edgecolor=basemap_style.get("edgecolor", t["border"]),
            linewidth=basemap_style.get("linewidth", 0.4),
            facecolor=basemap_style.get("facecolor", t["land_face"]),
            draw_grid=False,
        )
        g_bounds = tuple(map(float, np.asarray(g.total_bounds).ravel()))
        basemap_crs = g.crs
        try:
            ax.set_xlim(g_bounds[0], g_bounds[2])
            ax.set_ylim(g_bounds[1], g_bounds[3])
        except Exception:
            pass

    rp = Path(raster_path).expanduser()
    if not rp.is_absolute():
        rp = (Path.cwd() / rp).resolve()
    if not rp.exists():
        proj_root = Path(__file__).resolve().parents[3]
        base = self.basemap_root or (proj_root / "data" / "geo")
        name = Path(raster_path).name
        candidates = [
            base / name,
            base / "rasters" / name,
            proj_root / "data" / name,
            proj_root / "data" / "geo" / name,
            Path("data") / name,
            Path("data/geo") / name,
        ]
        found = None
        for c in candidates:
            if c.exists():
                found = c.resolve()
                break
        if found is not None:
            rp = found
        else:
            raise FileNotFoundError(
                f"栅格文件不存在：{Path(raster_path).resolve()}\n"
                "已尝试候选路径：\n - " + "\n - ".join(str(x.resolve()) for x in candidates)
            )

    with rasterio.open(rp) as ds:
        img = ds.read(1)
        img = np.where(np.isfinite(img), img, np.nan)
        bounds = ds.bounds
        extent = (bounds.left, bounds.right, bounds.bottom, bounds.top)
        im = ax.imshow(img, extent=extent, origin="upper", alpha=alpha, zorder=-1)
        plt.colorbar(im, ax=ax, fraction=0.035, pad=0.02)

    bounds_for_finalize = g_bounds if g_bounds is not None else (extent[0], extent[2], extent[1], extent[3])
    self._finalize_ax(ax, title, bounds=bounds_for_finalize, draw_grid=draw_grid, crs=basemap_crs)
    return fig, ax





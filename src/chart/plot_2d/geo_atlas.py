# -*- coding: utf-8 -*-
# File: src/chart/plot_2d/geo_atlas.py
# Author: Keying Digital Intelligence (柯影数智)
"""
GeoAtlas — 研究级制图：世界 & 中国（离线底图，出版级样式 + 研究数据叠加）

相对原 domain_analysis 的关键升级：
1) 中国地图完整性：融合 GADM-CHN 与 GADM-TWN，默认纳入 台湾/香港/澳门。
   - L0：将 CHN 与 TWN 的国家层合并绘制（保持各自几何，不做拓扑融合）
   - L1：在 CHN L1 基础上，把 TWN L1 的所有县市 union 为一个“台湾省”单一多边形并追加
   - L2/L3：按需从 TWN 对应层级直接并入（不做 union），避免细粒度丢失
2) 名称标准化：L1 下台湾默认命名为“台湾省”，可通过参数覆盖；HKG/MAC 识别常见中英别名
3) 仍然保持所有 overlay / choropleth / 栅格叠加能力；保留原函数名作为向后兼容别名

新增修复与增强：
- 经纬网格在投影 CRS 下错位 → 自动重投影绘制
- 比例尺坐标变换在部分 Matplotlib 版本下失效 → 两步式安全变换
- include_hk_mo 开关实装（L1+ 级别可剔除港澳）
- 世界高亮国家名称匹配更鲁棒（大小写/列名差异）
- 折线叠加支持 MultiLineString，线宽按列映射
- 散点叠加支持 size_col
- 多边形与分级着色的色标绘制更稳健
- 底图优先读取 GPKG，再回退 shp/geojson
"""
from __future__ import annotations

import os
import re
import threading
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence, Tuple, List, Union

import numpy as np

try:
    import geopandas as gpd
    from shapely.geometry import LineString
    from shapely.ops import unary_union
except Exception as e:
    from src.util.dependency_hints import format_missing_dependency

    raise RuntimeError(
        format_missing_dependency(
            package="geopandas",
            feature="GeoAtlas 地图功能",
            recommended_extra="maps",
            fallback_pip="pip install geopandas shapely",
        )
    ) from e

# 可选依赖
try:
    import rasterio
except Exception:
    rasterio = None  # type: ignore

try:
    import mapclassify as mc
except Exception:
    mc = None  # type: ignore

# 可选 pandas（分类调色、读表等需要）
try:
    import pandas as pd  # type: ignore
except Exception:
    pd = None  # type: ignore

# 你已有的统一绘图配置
from src.config import PlotConfig, ensure_matplotlib_backend
from src.util.dependency_hints import format_missing_dependency

ensure_matplotlib_backend()

import matplotlib.pyplot as plt

__all__ = [
    "GeoAtlas",
    # 便捷函数
    "plot_world_admin0", "plot_world_admin1", "plot_china",
    "choropleth_world", "choropleth_china", "raster_on_map",
    "read_points_from_table", "read_vector", "points_from_arrays",
    # 兼容旧名
    "DomainMapPlotter",
    # 缓存管理
    "clear_geo_read_cache",
]


_GEO_READ_CACHE_MAX_ITEMS = max(1, int(os.getenv("GEO_READ_CACHE_MAX_ITEMS", "24")))
_GEO_READ_CACHE_LOCK = threading.RLock()
_GEO_READ_CACHE: "OrderedDict[tuple[str, str, int, int], gpd.GeoDataFrame]" = OrderedDict()


def _geo_cache_key(path: Path, layer: Optional[str] = None) -> tuple[str, str, int, int]:
    resolved = path.expanduser().resolve()
    try:
        st = resolved.stat()
        return str(resolved), (layer or ""), int(st.st_mtime_ns), int(st.st_size)
    except Exception:
        return str(resolved), (layer or ""), -1, -1


def _read_vector_cached(path: Path, layer: Optional[str] = None) -> gpd.GeoDataFrame:
    key = _geo_cache_key(path, layer)
    with _GEO_READ_CACHE_LOCK:
        cached = _GEO_READ_CACHE.get(key)
        if cached is not None:
            _GEO_READ_CACHE.move_to_end(key)
            return cached.copy(deep=True)

    if layer:
        gdf = gpd.read_file(path, layer=layer)
    else:
        gdf = gpd.read_file(path)

    with _GEO_READ_CACHE_LOCK:
        _GEO_READ_CACHE[key] = gdf
        _GEO_READ_CACHE.move_to_end(key)
        while len(_GEO_READ_CACHE) > _GEO_READ_CACHE_MAX_ITEMS:
            _GEO_READ_CACHE.popitem(last=False)
    return gdf.copy(deep=True)


def clear_geo_read_cache() -> int:
    with _GEO_READ_CACHE_LOCK:
        count = len(_GEO_READ_CACHE)
        _GEO_READ_CACHE.clear()
    return count


# -----------------------------
# 小工具 & 主题
# -----------------------------

def _slugify(s: str, repl: str = "_") -> str:
    s = (s or "").strip()
    if not s:
        return "figure"
    s = re.sub(r"[\\/:*?\"<>|]+", repl, s)
    s = re.sub(r"\s+", repl, s)
    s = re.sub(rf"{repl}+", repl, s)
    return s.strip(repl)[:120] or "figure"


def _margins(ax: plt.Axes, x=0.04, y=0.04):
    try:
        ax.margins(x=x, y=y)
    except Exception:
        pass


def _first_present(cols: List[str], options: Sequence[str]) -> Optional[str]:
    s = set(cols)
    for name in options:
        if name in s:
            return name
    return None


def _nice_palette(name: str) -> str:
    maps = {
        "journal": "YlGnBu",
        "light": "Blues",
        "dark": "magma",
        "reds": "Reds",
        "greens": "Greens",
        "blues": "Blues",
        "viridis": "viridis",
        "cividis": "cividis",
        "plasma": "plasma",
        "warm": "OrRd",
        "cool": "PuBuGn",
    }
    return maps.get(name.lower(), name)


THEMES = {
    "journal": dict(
        fig_face="#FFFFFF",
        ax_face="#FBFCFE",
        land_face="#F5F7FA",
        border="#677286",
        border2="#727B8D",
        grid="#DDE3EA",
        miss="#EDEFF2",
        text="#111111",
        point_edge="#0B1220",
    ),
    "light": dict(
        fig_face="#FFFFFF",
        ax_face="#FFFFFF",
        land_face="#F6F8FB",
        border="#6B7280",
        border2="#7C8597",
        grid="#E5E9F0",
        miss="#EEF2F7",
        text="#111111",
        point_edge="#0B1220",
    ),
    "dark": dict(
        fig_face="#0B0F14",
        ax_face="#10161D",
        land_face="#1A2430",
        border="#95A3B8",
        border2="#8A97AC",
        grid="#2A3542",
        miss="#263242",
        text="#E8EEF5",
        point_edge="#E5E7EB",
    ),
}


def _apply_theme(fig: plt.Figure, ax: plt.Axes, theme: str = "journal"):
    t = THEMES.get(theme, THEMES["journal"])
    fig.patch.set_facecolor(t["fig_face"])
    ax.set_facecolor(t["ax_face"])
    try:
        ax.title.set_color(t["text"])
    except Exception:
        pass
    return t


def _halo_text(ax: plt.Axes, x: float, y: float, s: str, color: str, fontsize: float = 9,
               ha: str = "center", va: str = "center", zorder: int = 10):
    import matplotlib.patheffects as pe
    txt = ax.text(x, y, s, color=color, fontsize=fontsize, ha=ha, va=va, zorder=zorder)
    txt.set_path_effects([pe.withStroke(linewidth=3.0, foreground="white", alpha=0.9)])
    return txt


def _centroid_or_rep_point(geom):
    try:
        c = geom.representative_point()
        return c.x, c.y
    except Exception:
        c = geom.centroid
        return c.x, c.y


def _build_graticule_gdf(bounds_ll, dlon=20, dlat=10) -> gpd.GeoDataFrame:
    xmin, ymin, xmax, ymax = bounds_ll
    lines = []
    lons = np.arange(np.ceil(xmin / dlon) * dlon, xmax + 1e-9, dlon)
    for lon in lons:
        lines.append(LineString([(lon, ymin), (lon, ymax)]))
    lats = np.arange(np.ceil(ymin / dlat) * dlat, ymax + 1e-9, dlat)
    for lat in lats:
        lines.append(LineString([(xmin, lat), (xmax, lat)]))
    return gpd.GeoDataFrame(geometry=lines, crs="EPSG:4326")


# -----------------------------
# 列名鲁棒解析（新增）
# -----------------------------

def _norm_token(s: str) -> str:
    """去 BOM/空白/下划线/连字符，统一小写，便于近似匹配。"""
    s = str(s or "")
    s = s.replace("\ufeff", "")  # BOM
    s = re.sub(r"[\s_\-]+", "", s)
    return s.lower().strip()


def _resolve_col_name(df_cols: Sequence[str], wanted: str) -> Optional[str]:
    """
    在 df 的列里寻找与 wanted“等价”的列名：
    1) 完全相等
    2) 大小写相等
    3) 归一化后相等（去空白/下划线/连字符/BOM）
    4) 归一化后包含关系（前缀/子串）
    """
    if wanted in df_cols:
        return wanted
    lower_map = {str(c).lower(): str(c) for c in df_cols}
    if wanted.lower() in lower_map:
        return lower_map[wanted.lower()]
    norm_map = {_norm_token(c): str(c) for c in df_cols}
    w_norm = _norm_token(wanted)
    if w_norm in norm_map:
        return norm_map[w_norm]
    # 宽松匹配：前缀/包含（只在唯一命中时接受）
    candidates = [orig for norm, orig in norm_map.items() if norm.startswith(w_norm) or w_norm in norm]
    candidates = list(dict.fromkeys(candidates))  # 去重，保持顺序
    if len(candidates) == 1:
        return candidates[0]
    return None


def _coerce_numeric_inplace(frame, col: str):
    """把列转成数值；转不动的设为 NaN。"""
    if pd is None:
        return
    try:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    except Exception:
        pass


# -----------------------------
# 数据导入（表/矢量） & 自定义构造
# -----------------------------

def _need_pandas():
    try:
        import pandas as _  # noqa
    except Exception as e:
        raise RuntimeError(
            format_missing_dependency(
                package="pandas",
                feature="地图表格读取",
                recommended_extra="data",
            )
        ) from e


def read_points_from_table(
        file: Union[str, Path],
        lon_col: str,
        lat_col: str,
        crs: str = "EPSG:4326",
) -> gpd.GeoDataFrame:
    """
    读取 CSV/TSV/Excel 等表格，转为点 GeoDataFrame。
    """
    _need_pandas()
    import pandas as pd  # type: ignore

    file = Path(file).expanduser().resolve()
    if not file.exists():
        raise FileNotFoundError(file)

    if file.suffix.lower() in {".csv"}:
        df = pd.read_csv(file)
    elif file.suffix.lower() in {".tsv", ".txt"}:
        df = pd.read_csv(file, sep="\t")
    elif file.suffix.lower() in {".xlsx", ".xls"}:
        df = pd.read_excel(file)
    else:
        # 也可能是 geojson/gpkg/shp，直接走 read_vector
        return read_vector(file)

    if lon_col not in df.columns or lat_col not in df.columns:
        # 尝试宽松解析
        lon_real = _resolve_col_name(df.columns, lon_col)
        lat_real = _resolve_col_name(df.columns, lat_col)
        if not lon_real or not lat_real:
            raise KeyError(f"找不到经纬度列：{lon_col}, {lat_col}；实际列：{list(df.columns)[:12]} ...")
        lon_col, lat_col = lon_real, lat_real

    df = df.dropna(subset=[lon_col, lat_col])
    g = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df[lon_col].astype(float), df[lat_col].astype(float)),
        crs="EPSG:4326",
    )
    if crs and str(crs).upper() != "EPSG:4326":
        g = g.to_crs(crs)
    return g


def read_vector(file: Union[str, Path]) -> gpd.GeoDataFrame:
    """
    读取矢量：Shapefile/GeoJSON/GPKG 等。
    """
    p = Path(file).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(p)
    return _read_vector_cached(p)


def points_from_arrays(lon: Sequence[float], lat: Sequence[float], crs: str = "EPSG:4326") -> gpd.GeoDataFrame:
    """
    用数组构造点层，便于“自定义数据”直接叠加。
    """
    if len(lon) != len(lat):
        raise ValueError("lon 与 lat 长度需一致")
    g = gpd.GeoDataFrame(geometry=gpd.points_from_xy(lon, lat), crs="EPSG:4326")
    if crs and str(crs).upper() != "EPSG:4326":
        g = g.to_crs(crs)
    return g


# -----------------------------
# 主类
# -----------------------------

from src.chart.plot_2d.plotters.geo import choropleth as _choropleth
from src.chart.plot_2d.plotters.geo import overlays as _overlays
from src.chart.plot_2d.plotters.geo import views as _views


@dataclass
class GeoAtlas:
    """研究级地图绘制（世界 & 中国，离线底图，科研数据叠加；中国完整性保障）"""

    cfg: Optional[PlotConfig] = None
    basemap_root: Optional[Path] = None  # 离线底图根目录
    theme: str = "journal"  # 'journal' | 'light' | 'dark'
    # 完整性控制
    include_taiwan: bool = True
    include_hk_mo: bool = True
    taiwan_name: str = "台湾省"  # L1 union 后的命名

    # 初始化 & basemap root
    def __post_init__(self):
        if self.cfg is None:
            self.cfg = PlotConfig.from_env()
        self.cfg.apply()

        env_root = os.getenv("MAP_BASEMAP_ROOT")
        if self.basemap_root is None:
            self.basemap_root = Path(env_root).expanduser() if env_root else self._auto_find_basemap_root()

        self.basemap_root = Path(self.basemap_root).expanduser().resolve()
        print(f"🗺️ Basemap root: {self.basemap_root}")

    def _auto_find_basemap_root(self) -> Path:
        here = Path(__file__).resolve()
        # 在工程树里从近到远寻找 data/geo
        for anc in [here.parent, *here.parents]:
            cand = anc / "data" / "geo"
            if cand.exists():
                return cand
        return Path.cwd() / "data" / "geo"

    # Figure & 保存
    def _new_fig_ax(self, figsize: Tuple[float, float]) -> Tuple[plt.Figure, plt.Axes]:
        try:
            fig, ax = plt.subplots(figsize=figsize, layout="constrained")
        except TypeError:
            fig, ax = plt.subplots(figsize=figsize, constrained_layout=True)
        _apply_theme(fig, ax, self.theme)
        return fig, ax

    def save(
            self,
            name: Optional[str] = None,
            fig: Optional[plt.Figure] = None,
            fmt: Optional[str] = None,
            dpi: Optional[int] = None,
            match_screen: bool = True,
            tight: bool = False,
    ) -> str:
        fig = fig or plt.gcf()
        try:
            fig.canvas.draw()
        except Exception:
            pass

        if not name:
            title_text = None
            try:
                if getattr(fig, "_suptitle", None) is not None:
                    title_text = fig._suptitle.get_text() or None
            except Exception:
                pass
            if not title_text:
                for ax in fig.axes:
                    t = (ax.get_title() or "").strip()
                    if t:
                        title_text = t
                        break
            name = _slugify(title_text or "map")

        out_path = self.cfg.outpath(name, fmt)
        final_dpi = "figure" if (match_screen and dpi is None) else (dpi or self.cfg.dpi)
        bbox = "tight" if tight else None

        fig.savefig(
            out_path,
            dpi=final_dpi,
            bbox_inches=bbox,
            facecolor=fig.get_facecolor(),
            edgecolor="none",
        )
        return out_path

    # ---------------- 路径定位 ----------------
    def _ne_admin0_dir(self) -> Path:
        return (self.basemap_root / "world" / "natural_earth" / "admin0").resolve()

    def _ne_admin1_dir(self) -> Path:
        return (self.basemap_root / "world" / "natural_earth" / "admin1").resolve()

    def _gadm_gpkg_path(self, country: str) -> Path:
        c = country.upper()
        if c == "CHN":
            return (self.basemap_root / "china" / "gadm" / "gpkg" / "gadm41_CHN.gpkg").resolve()
        elif c == "TWN":
            return (self.basemap_root / "taiwan" / "gadm" / "gpkg" / "gadm41_TWN.gpkg").resolve()
        else:
            return (self.basemap_root / country.lower() / "gadm" / "gpkg" / f"gadm41_{c}.gpkg").resolve()

    def _gadm_shp_dir(self, country: str) -> Path:
        c = country.upper()
        base = self.basemap_root / ("china" if c == "CHN" else ("taiwan" if c == "TWN" else c.lower())) / "gadm" / "shp"
        return base.resolve()

    def _pick_file(self, directory: Path, stem_prefix: str) -> Path:
        if not directory.exists():
            raise FileNotFoundError(
                f"离线目录不存在：{directory}\n"
                f"当前 basemap_root = {self.basemap_root}\n"
                f"建议先运行 scripts/download_basemaps.py 将底图下载到 data/geo 下。"
            )
        # 优先 GPKG
        exts = [".gpkg", ".geojson", ".json", ".shp"]
        for ext in exts:
            for p in directory.glob(f"{stem_prefix}*{ext}"):
                return p
        for p in directory.glob("*.shp"):
            return p
        raise FileNotFoundError(f"未找到底图（前缀：{stem_prefix}）于 {directory}")

    # ---------------- 底图载入（NE） ----------------
    def _load_world_admin0(self) -> gpd.GeoDataFrame:
        p = self._pick_file(self._ne_admin0_dir(), "ne_10m_admin_0")
        return _read_vector_cached(p)

    def _load_world_admin1(self) -> gpd.GeoDataFrame:
        p = self._pick_file(self._ne_admin1_dir(), "ne_10m_admin_1")
        return _read_vector_cached(p)

    # ---------------- 底图载入（GADM 原始层，已修复稳健性） ----------------
    def _load_gadm_layer(self, country: str, level: int) -> gpd.GeoDataFrame:
        """
        稳健加载 GADM 层：
        - 优先在 basemap_root 下按既定目录查找 GPKG（见 _gadm_gpkg_path）
        - 自动枚举 GPKG 图层并挑选与 level 匹配的名字
        - 读失败则回退 SHP 目录（见 _gadm_shp_dir），尝试多种文件名模式
        """
        gpkg = self._gadm_gpkg_path(country)

        # 1) 先试 GPKG：列出并挑选图层
        if gpkg.exists():
            layers: List[str] = []
            try:
                from pyogrio import list_layers as _list_layers
                layers = [name for name, _ in _list_layers(gpkg)]
            except Exception:
                try:
                    import fiona  # type: ignore
                    layers = list(fiona.listlayers(gpkg))
                except Exception:
                    layers = []

            def pick_layer(layers: List[str], cc: str, lv: int) -> Optional[str]:
                cc = cc.upper()
                exact = f"gadm41_{cc}_{lv}"
                if exact in layers:
                    return exact
                for L in layers:
                    if L.endswith(f"_{lv}") and cc in L:
                        return L
                for cand in (f"ADM{lv}", f"ADM_{lv}", f"gadm41_{lv}", f"gadm_{lv}"):
                    for L in layers:
                        if L.upper() == cand.upper():
                            return L
                for L in layers:
                    if str(lv) in L:
                        return L
                return None

            if layers:
                layer = pick_layer(layers, country, level)
                if layer:
                    try:
                        return _read_vector_cached(gpkg, layer=layer)
                    except Exception as e:
                        print(f"⚠️ 读取 GPKG 图层失败（{layer}）：{e}；尝试 SHP 兜底。")
            else:
                print(f"⚠️ GPKG 无可读图层：{gpkg}；尝试 SHP 兜底。")

        # 2) 回退 SHP：尝试多种文件名
        shp_dir = self._gadm_shp_dir(country)
        candidates = (
                list(shp_dir.glob(f"gadm41_{country.upper()}_{level}*.shp")) +
                list(shp_dir.glob(f"*_{country.upper()}_{level}*.shp")) +
                list(shp_dir.glob(f"*ADM{level}*.shp"))
        )
        for shp in candidates:
            try:
                return _read_vector_cached(shp)
            except Exception:
                continue

        tried = [str(gpkg)] + [str(c) for c in candidates]
        raise FileNotFoundError(
            f"未能加载 GADM 层。国家: {country.upper()} 层级: {level}\n"
            "已尝试路径/图层：\n - " + "\n - ".join(tried)
        )

    # ---------------- 中国完整性：合并构造 ----------------
    def _load_china_plus(self, level: int) -> gpd.GeoDataFrame:
        """
        level:
          0: 国家层（CHN + TWN 作为两条记录）
          1: 省级（CHN L1 + union(TWN L1) -> “台湾省”加入）
          2/3: 直接 concat CHN 与 TWN 对应层（保留台湾细粒度县/乡）
        """
        chn = self._load_gadm_layer("CHN", level)

        # 可选去除港澳（在 L1/L2/L3 有效）
        if (not self.include_hk_mo) and level >= 1:
            name_col = f"NAME_{level}"
            if name_col in chn.columns:
                hkmo_alias = {
                    "香港", "香港特别行政区", "Hong Kong", "Hong Kong SAR",
                    "澳门", "澳门特别行政区", "Macao", "Macao SAR", "Macau"
                }
                chn = chn[~chn[name_col].astype(str).isin(hkmo_alias)]

        if not self.include_taiwan:
            return chn

        try:
            twn = self._load_gadm_layer("TWN", level)
        except Exception:
            print("ℹ️ 未找到 GADM-TWN 数据（data/geo/taiwan/...），已仅绘制 CHN。")
            return chn

        if level == 0:
            out = gpd.GeoDataFrame(pd.concat([chn, twn], ignore_index=True), crs=chn.crs) if pd is not None else chn
            return out

        if level == 1:
            name_col = f"NAME_{level}"
            gid_col = f"GID_{level}"
            try:
                geom = unary_union([g for g in twn.geometry if g is not None]).buffer(0)
            except Exception:
                geom = unary_union([g for g in twn.geometry if g is not None])

            row = {
                name_col: self.taiwan_name,
                gid_col: "TWN_L1",
                "COUNTRY": "China",
                "GID_0": "CHN",
                "NAME_0": "China",
                "geometry": geom,
            }
            twn_union = gpd.GeoDataFrame([row], crs=twn.crs or chn.crs)
            if twn_union.crs != chn.crs:
                twn_union = twn_union.to_crs(chn.crs)
            out = gpd.GeoDataFrame(pd.concat([chn, twn_union], ignore_index=True),
                                   crs=chn.crs) if pd is not None else chn
            return out

        if pd is not None:
            out = gpd.GeoDataFrame(pd.concat([chn, twn], ignore_index=True), crs=chn.crs)
        else:
            out = chn
        return out

    # ---------------- 公共绘图基元 ----------------
    def _ensure_ax(self, ax: Optional[plt.Axes], figsize: Tuple[float, float]) -> Tuple[plt.Figure, plt.Axes]:
        if ax is None:
            fig, ax = self._new_fig_ax(figsize)
        else:
            fig = ax.figure
            _apply_theme(fig, ax, self.theme)
        ax.set_axis_off()
        _margins(ax, 0.02, 0.02)
        try:
            ax.set_rasterization_zorder(0)
        except Exception:
            pass
        return fig, ax

    def _maybe_to_crs(self, gdf: gpd.GeoDataFrame, crs: Optional[str | int]) -> gpd.GeoDataFrame:
        if crs is None:
            return gdf
        try:
            if gdf.crs is None or str(gdf.crs).lower() != str(crs).lower():
                return gdf.to_crs(crs)
        except Exception:
            pass
        return gdf

    def _finalize_ax(self, ax: plt.Axes, title: Optional[str], bounds,
                     draw_grid: bool = True, grid_step: Tuple[int, int] = (20, 10), crs=None):
        theme = THEMES.get(self.theme, THEMES["journal"])
        if draw_grid and bounds is not None:
            xmin, ymin, xmax, ymax = bounds
            is_lonlat_bounds = (-200 <= xmin <= 200 and -200 <= xmax <= 200 and
                                -90 <= ymin <= 90 and -90 <= ymax <= 90)

            if is_lonlat_bounds or (crs is None) or (str(crs).upper() in {"EPSG:4326", "WGS84"}):
                # 轴就是经纬度，直接画
                self._draw_lonlat_lines_plain(ax, bounds, dlon=grid_step[0], dlat=grid_step[1],
                                              color=theme["grid"], lw=0.6)
            else:
                # 轴是投影坐标：先在 WGS84 生成网格 → 投影到当前 CRS → 再绘制
                try:
                    world_ll = (-180, -80, 180, 85)
                    grat = _build_graticule_gdf(world_ll, dlon=grid_step[0], dlat=grid_step[1])
                    grat = grat.to_crs(crs)
                    # 轻量裁剪到当前视窗范围，避免巨量线段绘制
                    try:
                        grat = grat.cx[xmin:xmax, ymin:ymax]
                    except Exception:
                        pass
                    grat.plot(ax=ax, color=theme["grid"], linewidth=0.6, zorder=0)
                except Exception:
                    pass

        if title:
            ax.set_title(title, color=theme["text"])
        try:
            ax.set_aspect("equal")
        except Exception:
            pass
        _margins(ax, 0.02, 0.02)
        for coll in getattr(ax, "collections", []):
            try:
                coll.set_antialiased(True)
            except Exception:
                pass

    @staticmethod
    def _draw_lonlat_lines_plain(ax: plt.Axes, bounds, dlon=20, dlat=10, color="#DDE3EA", lw=0.6):
        xmin, ymin, xmax, ymax = bounds
        try:
            lons = np.arange(np.ceil(xmin / dlon) * dlon, xmax + 1e-9, dlon)
            for lon in lons:
                ax.plot([lon, lon], [ymin, ymax], color=color, lw=lw, zorder=0)
            lats = np.arange(np.ceil(ymin / dlat) * dlat, ymax + 1e-9, dlat)
            for lat in lats:
                ax.plot([xmin, xmax], [lat, lat], color=color, lw=lw, zorder=0)
        except Exception:
            pass

    def _outline_overlay(self, ax: plt.Axes, gdf: gpd.GeoDataFrame, color="#666A73", lw=0.5, zorder=5):
        try:
            gdf.boundary.plot(ax=ax, color=color, linewidth=lw, zorder=zorder)
        except Exception:
            pass

    def _label_gdf(self, ax: plt.Axes, gdf: gpd.GeoDataFrame, name_col: str,
                   color=None, fontsize=9, zorder=10, max_labels=80):
        theme = THEMES.get(self.theme, THEMES["journal"])
        color = theme["text"] if color is None else color
        rows = gdf.head(max_labels)
        for _, row in rows.iterrows():
            if row.geometry is None or row.get(name_col) is None:
                continue
            x, y = _centroid_or_rep_point(row.geometry)
            _halo_text(ax, x, y, str(row[name_col]), color=color, fontsize=fontsize, zorder=zorder)

    # ---------------- 底图：世界 ----------------
    def plot_world_admin0(self, *args, **kwargs):
        return _views.plot_world_admin0(self, *args, **kwargs)

    def plot_world_admin1(self, *args, **kwargs):
        return _views.plot_world_admin1(self, *args, **kwargs)

    def plot_china(self, *args, **kwargs):
        return _views.plot_china(self, *args, **kwargs)

    # ---------------- 分级着色 ----------------
    def _plot_choropleth_core(self, *args, **kwargs):
        return _choropleth._plot_choropleth_core(self, *args, **kwargs)

    def choropleth_world(self, *args, **kwargs):
        return _choropleth.choropleth_world(self, *args, **kwargs)

    def choropleth_china(self, *args, **kwargs):
        return _choropleth.choropleth_china(self, *args, **kwargs)

    # ---------------- 研究数据叠加（点/线/面） ----------------
    def overlay_points(self, *args, **kwargs):
        return _overlays.overlay_points(self, *args, **kwargs)

    def overlay_lines(self, *args, **kwargs):
        return _overlays.overlay_lines(self, *args, **kwargs)

    def overlay_polygons(self, *args, **kwargs):
        return _overlays.overlay_polygons(self, *args, **kwargs)

    def annotate(self, *args, **kwargs):
        return _overlays.annotate(self, *args, **kwargs)

    def add_north_arrow(self, *args, **kwargs):
        return _overlays.add_north_arrow(self, *args, **kwargs)

    def add_scalebar(self, *args, **kwargs):
        return _overlays.add_scalebar(self, *args, **kwargs)

    @staticmethod
    def _nice_length(*args, **kwargs):
        return _overlays._nice_length(*args, **kwargs)

    def raster_on_map(self, *args, **kwargs):
        return _overlays.raster_on_map(self, *args, **kwargs)

# -----------------------------
# 便捷函数（向后兼容）
# -----------------------------

_default_atlas: Optional[GeoAtlas] = None


def _get_default() -> GeoAtlas:
    global _default_atlas
    if _default_atlas is None:
        _default_atlas = GeoAtlas()
    return _default_atlas


def plot_world_admin0(*args, **kwargs):
    return _get_default().plot_world_admin0(*args, **kwargs)


def plot_world_admin1(*args, **kwargs):
    return _get_default().plot_world_admin1(*args, **kwargs)


def plot_china(*args, **kwargs):
    return _get_default().plot_china(*args, **kwargs)


def choropleth_world(*args, **kwargs):
    return _get_default().choropleth_world(*args, **kwargs)


def choropleth_china(*args, **kwargs):
    return _get_default().choropleth_china(*args, **kwargs)


def raster_on_map(*args, **kwargs):
    return _get_default().raster_on_map(*args, **kwargs)


# 兼容旧类名
DomainMapPlotter = GeoAtlas

# -----------------------------
# 自测 Demo（底图就绪后可运行）
# -----------------------------
if __name__ == "__main__":
    import pandas as pd

    atlas = GeoAtlas(theme="journal", include_hk_mo=False)
    # 中国省级（完整）
    fig, ax, g = atlas.plot_china(level=1, title="China Provinces (含台/可剔港澳)", label=True)
    atlas.add_north_arrow(ax, xy=(0.9, 0.18))
    atlas.add_scalebar(ax, location="lower left")
    atlas.save(fig=fig)

    # 世界分级着色 + 高亮（大小写鲁棒）
    df = pd.DataFrame({"iso_a3": ["chn", "usa", "fra"], "val": [1, 2, 3]})
    fig, ax, g = atlas.choropleth_world(df, key_col="iso_a3", value_col="val", on="iso_a3",
                                        title="World Choropleth")
    atlas.save(fig=fig)

    # 散点尺寸映射 + 类别图例（在中国底图上）
    import geopandas as gpd

    pts = gpd.GeoDataFrame({
        "sizev": [1, 5, 10, 20],
        "cat": ["A", "B", "A", "B"]
    }, geometry=gpd.points_from_xy([110, 112, 114, 116], [30, 31, 32, 33]), crs="EPSG:4326")
    fig, ax, g = atlas.plot_china(level=1, title="Points Overlay Demo")
    atlas.overlay_points(ax, pts, size_col="sizev", hue_col="cat", label_col=None)
    atlas.save(fig=fig)
    plt.show()

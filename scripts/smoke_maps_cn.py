# scripts/smoke_maps_cn.py
# 中文地图功能测试（Basemap / 分级着色 / 点叠加 / 栅格叠加）
from __future__ import annotations

import os
import sys
import random
from pathlib import Path
from typing import List, Optional

from src.main import ResearchDrawApp

# ---------- 路径 ----------
THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parent.parent.resolve()
BASEMAP_ROOT = Path(os.environ.get("MAP_BASEMAP_ROOT") or (PROJECT_ROOT / "data" / "geo")).resolve()
DATA_DIR = (PROJECT_ROOT / "data" / "test").resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 你的栅格就在 data/ 目录
RASTER_WORLD_TIF = (PROJECT_ROOT / "data" / "demo_world.tif").resolve()
RASTER_CHINA_TIF = (PROJECT_ROOT / "data" / "demo_china.tif").resolve()

POINTS_CSV = (DATA_DIR / "points.csv").resolve()
WORLD_CHORO_CSV = (DATA_DIR / "world_values.csv").resolve()   # 需列：ISO_A3,value
CHINA_CHORO_CSV = (DATA_DIR / "china_l1_values.csv").resolve()# 需列：NAME_1,value

MAP_THEME = "journal"
NO_SHOW = True
RNG_SEED = 20251025
random.seed(RNG_SEED)


# ---------- 工具 ----------
def fail(msg: str):
    print(f"[ERROR] {msg}")
    sys.exit(1)


def ensure_basemap_dir():
    if not BASEMAP_ROOT.exists():
        fail(f"离线底图根目录不存在：{BASEMAP_ROOT}\n请设置 MAP_BASEMAP_ROOT 或将数据放到 <repo>/data/geo")


def find_ne_admin0_path(root: Path) -> Optional[Path]:
    d = (root / "world" / "natural_earth" / "admin0")
    if not d.exists():
        return None
    for ext in (".gpkg", ".geojson", ".json", ".shp"):
        for p in d.glob(f"ne_10m_admin_0*{ext}"):
            return p
    for p in d.glob("*.shp"):
        return p
    return None


def find_gadm_l1_path(root: Path) -> Optional[Path]:
    gpkg = root / "china" / "gadm" / "gpkg" / "gadm41_CHN.gpkg"
    if gpkg.exists():
        return gpkg
    shp_dir = root / "china" / "gadm" / "shp"
    for p in shp_dir.glob("gadm41_CHN_1*.shp"):
        return p
    return None


def make_world_values_csv(out_csv: Path):
    """从 NE admin0 读取 ISO_A3，生成随机 value，确保“世界分级着色”必定上色。"""
    import geopandas as gpd
    import pandas as pd
    import numpy as np

    p = find_ne_admin0_path(BASEMAP_ROOT)
    if p is None:
        fail(f"未找到世界国家底图（natural earth admin0）于 {BASEMAP_ROOT}/world/natural_earth/admin0")
    g = gpd.read_file(p)
    key = next((k for k in ["ISO_A3", "iso_a3", "ADM0_A3"] if k in g.columns), None)
    if key is None:
        fail(f"admin0 缺少 ISO_A3/ADM0_A3 列，实际列示例：{list(g.columns)[:15]}")
    rng = np.random.default_rng(RNG_SEED)
    pd.DataFrame({
        "ISO_A3": g[key],
        "value": np.round(rng.random(len(g)) * 100, 2),
    }).to_csv(out_csv, index=False, encoding="utf-8")
    print(f"[OK] 生成世界分级着色数据：{out_csv}")


def make_china_l1_values_csv(out_csv: Path):
    """从 GADM China Level-1 生成 NAME_1,value CSV。"""
    import geopandas as gpd
    import pandas as pd
    import numpy as np

    p = find_gadm_l1_path(BASEMAP_ROOT)
    if p is None:
        fail(f"未找到中国 GADM L1 数据：{BASEMAP_ROOT}/china/gadm/gpkg 或 {BASEMAP_ROOT}/china/gadm/shp")
    g = gpd.read_file(p, layer="gadm41_CHN_1") if p.suffix.lower() == ".gpkg" else gpd.read_file(p)
    if "NAME_1" not in g.columns:
        fail(f"GADM L1 缺少 NAME_1 列，实际列示例：{list(g.columns)[:15]}")
    rng = np.random.default_rng(RNG_SEED)
    pd.DataFrame({
        "NAME_1": g["NAME_1"],
        "value": np.round(rng.random(len(g)) * 100, 2),
    }).to_csv(out_csv, index=False, encoding="utf-8")
    print(f"[OK] 生成中国 L1 分级着色数据：{out_csv}")


def make_points_csv(out_csv: Path):
    """生成一批全球点（name/group/size），保证“点叠加”有颜色+大小差异。"""
    import pandas as pd
    import numpy as np
    rng = np.random.default_rng(RNG_SEED)
    n = 80
    lon = rng.uniform(-160, 160, n)
    lat = rng.uniform(-60, 75, n)
    size = np.round(rng.normal(50, 20, n).clip(5, 120), 1)
    group = rng.choice(["A 组", "B 组", "C 组"], size=n, p=[0.35, 0.35, 0.30])
    name = [f"站点{i+1}" for i in range(n)]
    pd.DataFrame({"lon": lon, "lat": lat, "size": size, "group": group, "name": name}).to_csv(out_csv, index=False)
    print(f"[OK] 生成点叠加数据：{out_csv}")


def make_demo_world_tif(out_tif: Path):
    """生成全球演示栅格（EPSG:4326）到 data/demo_world.tif。"""
    try:
        import numpy as np
        import rasterio
        from rasterio.transform import from_bounds
    except Exception:
        print("[SKIP] 未安装 rasterio，跳过生成 demo_world.tif（uv sync --extra raster）")
        return
    out_tif.parent.mkdir(parents=True, exist_ok=True)
    width, height = 720, 360
    left, bottom, right, top = -180.0, -90.0, 180.0, 90.0
    transform = from_bounds(left, bottom, right, top, width, height)
    y = np.linspace(-1, 1, height)[:, None]
    x = np.linspace(-1, 1, width)[None, :]
    data = (np.exp(-(x**2 + (y*1.3)**2)) * 120.0 + (x + 1) * 25.0 + (y + 1) * 15.0).astype("float32")
    with rasterio.open(out_tif, "w",
                       driver="GTiff", height=height, width=width, count=1, dtype="float32",
                       crs="EPSG:4326", transform=transform, compress="lzw") as dst:
        dst.write(data, 1)
    print(f"[OK] 生成演示栅格：{out_tif}")


def make_demo_china_tif(out_tif: Path):
    """生成中国范围演示栅格（EPSG:4326）到 data/demo_china.tif。"""
    try:
        import numpy as np
        import rasterio
        from rasterio.transform import from_bounds
    except Exception:
        print("[SKIP] 未安装 rasterio，跳过生成 demo_china.tif（uv sync --extra raster）")
        return
    out_tif.parent.mkdir(parents=True, exist_ok=True)
    # 大约中国本土范围
    left, right = 73.5, 135.1
    bottom, top = 18.0, 53.6
    width, height = 620, 420
    transform = from_bounds(left, bottom, right, top, width, height)
    y = np.linspace(-1, 1, height)[:, None]
    x = np.linspace(-1, 1, width)[None, :]
    data = (np.exp(-((x-0.2)**2 + (y-0.1)**2)) * 150.0 + (x + 1) * 30.0 + (1 - y) * 20.0).astype("float32")
    with rasterio.open(out_tif, "w",
                       driver="GTiff", height=height, width=width, count=1, dtype="float32",
                       crs="EPSG:4326", transform=transform, compress="lzw") as dst:
        dst.write(data, 1)
    print(f"[OK] 生成演示栅格：{out_tif}")


def ensure_demo_data():
    ensure_basemap_dir()
    if not WORLD_CHORO_CSV.exists():
        make_world_values_csv(WORLD_CHORO_CSV)
    if not CHINA_CHORO_CSV.exists():
        make_china_l1_values_csv(CHINA_CHORO_CSV)
    if not POINTS_CSV.exists():
        make_points_csv(POINTS_CSV)
    if not RASTER_WORLD_TIF.exists():
        make_demo_world_tif(RASTER_WORLD_TIF)
    if not RASTER_CHINA_TIF.exists():
        make_demo_china_tif(RASTER_CHINA_TIF)


def run(argv_list: List[str]) -> None:
    args = [str(a) for a in argv_list if a]
    printable = " ".join(args)
    print(f">>> running: {printable}")
    ResearchDrawApp(args).run()


def ensure_exists(p: Path, desc: str) -> bool:
    if p.exists():
        return True
    print(f"[SKIP] 缺少{desc}：{p}")
    return False


# ---------- 测试用例 ----------
def test_world_admin0_base():
    run([
        "--plot", "world",
        "--map-theme", MAP_THEME,
        "--basemap-root", str(BASEMAP_ROOT),
        "--title", "世界国家边界（基础底图）",
        "--label-names",
        "--crs", "EPSG:4326",
        "--tight",
        "--no-show" if NO_SHOW else None,
    ])


def test_world_admin1_subset():
    run([
        "--plot", "world_admin1",
        "--countries", "China,United States of America,India",
        "--label-names",
        "--map-theme", MAP_THEME,
        "--basemap-root", str(BASEMAP_ROOT),
        "--title", "世界一级行政区（子集）",
        "--crs", "EPSG:4326",
        "--tight",
        "--no-show" if NO_SHOW else None,
    ])


def test_china_l1_label():
    run([
        "--plot", "china",
        "--level", "1",
        "--label-names",
        "--highlight", "北京市,上海市,广东省,四川省",
        "--map-theme", MAP_THEME,
        "--basemap-root", str(BASEMAP_ROOT),
        "--title", "中国省级行政区（带标注）",
        "--crs", "EPSG:4326",
        "--tight",
        "--no-show" if NO_SHOW else None,
    ])


def test_choropleth_world():
    if not ensure_exists(WORLD_CHORO_CSV, "世界分级着色数据 CSV（ISO_A3,value）"):
        return
    run([
        "--plot", "choropleth_world",
        "--mode", "file",
        "--file", str(WORLD_CHORO_CSV),
        "--key-col", "ISO_A3",
        "--value-col", "value",
        "--on", "iso_a3",
        "--scheme", "natural",
        "--k", "6",
        "--cmap", MAP_THEME,
        "--map-theme", MAP_THEME,
        "--basemap-root", str(BASEMAP_ROOT),
        "--title", "世界分级着色（自然断点）",
        "--crs", "EPSG:4326",
        "--tight",
        "--no-show" if NO_SHOW else None,
    ])


def test_choropleth_china_l1():
    if not ensure_exists(CHINA_CHORO_CSV, "中国省级分级着色数据 CSV（NAME_1,value）"):
        return
    run([
        "--plot", "choropleth_china",
        "--mode", "file",
        "--file", str(CHINA_CHORO_CSV),
        "--level", "1",
        "--key-col", "NAME_1",
        "--value-col", "value",
        "--on", "NAME",
        "--scheme", "quantiles",
        "--k", "5",
        "--cmap", "Reds",
        "--map-theme", MAP_THEME,
        "--basemap-root", str(BASEMAP_ROOT),
        "--title", "中国省级分级着色（五分位）",
        "--crs", "EPSG:4326",
        "--tight",
        "--no-show" if NO_SHOW else None,
    ])


def test_raster_overlay_world():
    if not ensure_exists(RASTER_WORLD_TIF, "演示栅格 data/demo_world.tif"):
        return
    run([
        "--plot", "raster",
        "--raster-file", str(RASTER_WORLD_TIF),
        "--basemap", "world_admin0",
        "--alpha", "0.60",
        "--map-theme", MAP_THEME,
        "--basemap-root", str(BASEMAP_ROOT),
        "--title", "世界底图 + 栅格叠加",
        "--tight",
        "--no-show" if NO_SHOW else None,
    ])


def test_raster_overlay_china():
    if not ensure_exists(RASTER_CHINA_TIF, "演示栅格 data/demo_china.tif"):
        return
    run([
        "--plot", "raster",
        "--raster-file", str(RASTER_CHINA_TIF),
        "--basemap", "china_l1",
        "--alpha", "0.60",
        "--map-theme", MAP_THEME,
        "--basemap-root", str(BASEMAP_ROOT),
        "--title", "中国底图 + 栅格叠加",
        "--tight",
        "--no-show" if NO_SHOW else None,
    ])


def test_points_overlay_world():
    if not ensure_exists(POINTS_CSV, "点叠加 CSV（lon,lat,name,group,size）"):
        return
    run([
        "--plot", "points",
        "--mode", "file",
        "--file", str(POINTS_CSV),
        "--lon-col", "lon",
        "--lat-col", "lat",
        "--label-col", "name",
        "--size-col", "size",
        "--hue-col", "group",
        "--basemap", "world_admin0",
        "--size-range", "36,220",
        "--map-theme", MAP_THEME,
        "--basemap-root", str(BASEMAP_ROOT),
        "--title", "全球研究点位叠加（分类着色 + 比例符号）",
        "--crs", "EPSG:4326",
        "--tight",
        "--no-show" if NO_SHOW else None,
    ])


# ---------- 主入口 ----------
if __name__ == "__main__":
    print(f"PROJECT_ROOT : {PROJECT_ROOT}")
    print(f"BASEMAP_ROOT : {BASEMAP_ROOT}")
    print(f"DATA_DIR     : {DATA_DIR}")
    print("开始中文地图功能测试……")
    ensure_demo_data()

    # A. 基础底图
    test_world_admin0_base()
    test_world_admin1_subset()
    test_china_l1_label()

    # B. 分级着色
    test_choropleth_world()
    test_choropleth_china_l1()

    # C. 栅格 & 点叠加（使用 data/demo_world.tif / data/demo_china.tif）
    test_raster_overlay_world()
    test_raster_overlay_china()
    test_points_overlay_world()

    print("✅ 全部中文地图测试执行完毕。")

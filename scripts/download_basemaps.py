#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
download_basemaps.py — 下载离线底图 + 可选自动“港澳提取”（仅下载用标准库；提取用 geopandas）

包含：
  - Natural Earth 1:10m：Admin 0（国家）/ Admin 1（州省）
  - GADM v4.1：CHN（含香港/澳门在 L1）、TWN（台湾）
  - 自动提取：从 GADM-CHN L1 中提取 [Hong Kong / Macao]；从 NE admin0 中提取 [HKG/MAC]

用法：
  uv run python scripts/download_basemaps.py --dir data/geo
  uv run python scripts/download_basemaps.py --dir data/geo --only ne
  uv run python scripts/download_basemaps.py --dir data/geo --only gadm
  uv run python scripts/download_basemaps.py --dir data/geo --skip-gadm
  # 关闭提取：
  uv run python scripts/download_basemaps.py --dir data/geo --no-extract-hkmo
"""

from __future__ import annotations
import argparse
import sys
import time
import urllib.request
import zipfile
from pathlib import Path
from typing import Optional

# ---------------- 数据源（TWN 需单独下载；HKG/MAC 没有独立官方包） ----------------
DATASETS = [
    # Natural Earth 1:10m
    {
        "name": "ne_10m_admin_0_countries",
        "url": "https://naturalearth.s3.amazonaws.com/10m_cultural/ne_10m_admin_0_countries.zip",
        "rel_dir": "world/natural_earth/admin0",
        "is_zip": True,
        "marker": "ne_10m_admin_0_countries.shp",
    },
    {
        "name": "ne_10m_admin_1_states_provinces",
        "url": "https://naturalearth.s3.amazonaws.com/10m_cultural/ne_10m_admin_1_states_provinces.zip",
        "rel_dir": "world/natural_earth/admin1",
        "is_zip": True,
        "marker": "ne_10m_admin_1_states_provinces.shp",
    },
    # GADM v4.1（中国 + 台湾）
    {
        "name": "gadm41_CHN_shp",
        "url": "https://geodata.ucdavis.edu/gadm/gadm4.1/shp/gadm41_CHN_shp.zip",
        "rel_dir": "china/gadm/shp",
        "is_zip": True,
        "marker": "gadm41_CHN_1.shp",  # L1
    },
    {
        "name": "gadm41_CHN_gpkg",
        "url": "https://geodata.ucdavis.edu/gadm/gadm4.1/gpkg/gadm41_CHN.gpkg",
        "rel_dir": "china/gadm/gpkg",
        "is_zip": False,
        "marker": "gadm41_CHN.gpkg",
    },
    {
        "name": "gadm41_TWN_shp",
        "url": "https://geodata.ucdavis.edu/gadm/gadm4.1/shp/gadm41_TWN_shp.zip",
        "rel_dir": "taiwan/gadm/shp",
        "is_zip": True,
        "marker": "gadm41_TWN_1.shp",
    },
    {
        "name": "gadm41_TWN_gpkg",
        "url": "https://geodata.ucdavis.edu/gadm/gadm4.1/gpkg/gadm41_TWN.gpkg",
        "rel_dir": "taiwan/gadm/gpkg",
        "is_zip": False,
        "marker": "gadm41_TWN.gpkg",
    },
]

# ---------------- 基础工具（仅标准库） ----------------
def human_size(num: float) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if num < 1024.0:
            return f"{num:3.1f}{unit}"
        num /= 1024.0
    return f"{num:.1f}PB"

def _progress_hook(fname: str):
    def _hook(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            percent = downloaded / total_size * 100
            sys.stdout.write(
                f"\r  -> {fname}: {human_size(downloaded)} / {human_size(total_size)} ({percent:5.1f}%)"
            )
        else:
            sys.stdout.write(f"\r  -> {fname}: {human_size(downloaded)}")
        sys.stdout.flush()
    return _hook

def download(url: str, out_path: Path, retries: int = 3, timeout: int = 60) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    last_err: Optional[Exception] = None
    for attempt in range(1, retries + 1):
        try:
            print(f"⬇️  下载 {url}")
            urllib.request.urlretrieve(url, out_path.as_posix(), reporthook=_progress_hook(out_path.name))
            sys.stdout.write("\n")
            if out_path.exists() and out_path.stat().st_size > 0:
                return
            raise RuntimeError("文件大小为 0")
        except Exception as e:
            last_err = e
            print(f"  ⚠️  第 {attempt}/{retries} 次尝试失败：{e}")
            if attempt < retries:
                time.sleep(2 * attempt)
    raise RuntimeError(f"下载失败：{url}\n最后错误：{last_err}")

def unzip(zip_path: Path, to_dir: Path, keep_zip: bool = True) -> None:
    print(f"📦 解压 {zip_path.name} -> {to_dir}")
    to_dir.mkdir(parents=True, exist_ok=True)
    if not zipfile.is_zipfile(zip_path):
        print(f"  ❌ 非有效 Zip：{zip_path}，删除后重下")
        try:
            zip_path.unlink()
        except Exception:
            pass
        raise RuntimeError("无效 zip，将触发上层重下")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(to_dir)
    if not keep_zip:
        try:
            zip_path.unlink()
        except Exception:
            pass

def _marker_exists(dir_: Path, marker: str) -> bool:
    return (dir_ / marker).exists()

# ---------------- 提取（可选，需 geopandas） ----------------
def _have_geopandas() -> bool:
    try:
        import geopandas as _  # noqa
        return True
    except Exception:
        return False

def _subset_save_gadm_hk_mo(base_dir: Path) -> None:
    """
    从 GADM 中国 L1 中提取 Hong Kong / Macao，另存为 GPKG/GeoJSON。
    """
    import geopandas as gpd

    # 1) 找 CHN 源
    chn_gpkg = base_dir / "china" / "gadm" / "gpkg" / "gadm41_CHN.gpkg"
    chn_shp_dir = base_dir / "china" / "gadm" / "shp"
    gdf = None
    if chn_gpkg.exists():
        try:
            gdf = gpd.read_file(chn_gpkg, layer="gadm41_CHN_1")
        except Exception:
            pass
    if gdf is None:
        shp = chn_shp_dir / "gadm41_CHN_1.shp"
        if shp.exists():
            gdf = gpd.read_file(shp)

    if gdf is None:
        print("  ⚠️ 未找到 GADM 中国 L1（gadm41_CHN_1.*），跳过港澳提取")
        return

    # 2) 名称规范与筛选
    col = "NAME_1" if "NAME_1" in gdf.columns else None
    if col is None:
        print(f"  ⚠️ GADM L1 未找到 NAME_1 列，实际列示例：{list(gdf.columns)[:10]}，跳过")
        return

    def _norm(s: str) -> str:
        return (str(s) or "").strip().lower()

    name_norm = gdf[col].apply(_norm)
    hk_mask = name_norm.isin({"hong kong", "hong-kong", "hongkong", "香港", "香港特别行政区"})
    mo_mask = name_norm.isin({"macao", "macau", "澳门", "澳門", "澳门特别行政区", "macao sar"})

    gdf_hk = gdf.loc[hk_mask].copy()
    gdf_mo = gdf.loc[mo_mask].copy()

    regions = [
        ("hkg", "Hong Kong", gdf_hk, base_dir / "china" / "regions" / "hkg"),
        ("mac", "Macao",     gdf_mo, base_dir / "china" / "regions" / "mac"),
    ]
    for code, nice, gsub, outdir in regions:
        outdir.mkdir(parents=True, exist_ok=True)
        if gsub.empty:
            print(f"  ⚠️ GADM 未匹配到 {nice}（请确认 GADM 数据列值）")
            continue
        # 保存为单图层 GPKG + GeoJSON
        gpkg_path = outdir / f"gadm41_{code.upper()}_1.gpkg"
        geojson_path = outdir / f"gadm41_{code.upper()}_1.geojson"
        try:
            gsub.to_file(gpkg_path, driver="GPKG", layer=f"gadm41_{code.upper()}_1")
        except Exception as e:
            print(f"  ⚠️ 写入 GPKG 失败：{e}，尝试只写 GeoJSON")
        try:
            gsub.to_file(geojson_path, driver="GeoJSON")
        except Exception as e:
            print(f"  ⚠️ 写入 GeoJSON 失败：{e}")
        print(f"  ✅ 提取完成：{nice} → {gpkg_path}")

def _subset_save_ne_hk_mo(base_dir: Path) -> None:
    """
    从 Natural Earth admin0 中提取 HKG/MAC（国家层级），另存为 GPKG/GeoJSON。
    """
    import geopandas as gpd

    ne_dir = base_dir / "world" / "natural_earth" / "admin0"
    shp = ne_dir / "ne_10m_admin_0_countries.shp"
    if not shp.exists():
        print("  ⚠️ 未找到 NE admin0，跳过 NE 港澳提取")
        return

    g = gpd.read_file(shp)
    cols = [c.lower() for c in g.columns]
    # 优先 ADM0_A3；备选 SOVEREIGNT/NAME
    key_adm0 = "adm0_a3" if "adm0_a3" in cols else None
    key_name = "name" if "name" in cols else None
    key_sov = "sovereignt" if "sovereignt" in cols else None

    def _norm(s): return (str(s) or "").strip().lower()

    def _pick_mask(code: str, names: set[str]):
        if key_adm0:
            m = (g[[c for c in g.columns if c.lower() == key_adm0][0]].astype(str).str.upper() == code)
            if m.any():
                return m
        m = None
        if key_name:
            m1 = g[[c for c in g.columns if c.lower() == key_name][0]].apply(_norm).isin(names)
            m = m1 if m is None else (m | m1)
        if key_sov:
            m2 = g[[c for c in g.columns if c.lower() == key_sov][0]].apply(_norm).isin(names)
            m = m2 if m is None else (m | m2)
        return m if m is not None else g.index == -1

    hk_names = {"hong kong", "hong kong s.a.r.", "hong-kong", "hongkong"}
    mo_names = {"macao", "macau", "macau s.a.r.", "macao s.a.r."}

    mask_hk = _pick_mask("HKG", hk_names)
    mask_mo = _pick_mask("MAC", mo_names)

    pairs = [
        ("hkg", "Hong Kong", g.loc[mask_hk].copy(), base_dir / "world" / "regions" / "hkg"),
        ("mac", "Macao",     g.loc[mask_mo].copy(), base_dir / "world" / "regions" / "mac"),
    ]
    for code, nice, gsub, outdir in pairs:
        outdir.mkdir(parents=True, exist_ok=True)
        if gsub.empty:
            print(f"  ⚠️ NE 未匹配到 {nice}（列名/值可能与版本有关）")
            continue
        gpkg_path = outdir / f"ne_{code.upper()}_admin0.gpkg"
        geojson_path = outdir / f"ne_{code.upper()}_admin0.geojson"
        try:
            gsub.to_file(gpkg_path, driver="GPKG", layer=f"ne_{code.upper()}_admin0")
        except Exception as e:
            print(f"  ⚠️ 写入 GPKG 失败：{e}，尝试只写 GeoJSON")
        try:
            gsub.to_file(geojson_path, driver="GeoJSON")
        except Exception as e:
            print(f"  ⚠️ 写入 GeoJSON 失败：{e}")
        print(f"  ✅ 提取完成（NE）：{nice} → {gpkg_path}")

# ---------------- 任务编排 ----------------
def run(
    target_dir: Path,
    only: Optional[str],
    skip_gadm: bool,
    keep_zip: bool,
    force: bool,
    extract_hkmo: bool,
) -> None:
    target_dir = target_dir.resolve()
    print(f"📁 目标目录：{target_dir}")

    # 选择下载集
    selected = DATASETS
    if only:
        ok = only.lower()
        if ok == "ne":
            selected = DATASETS[:2]
        elif ok == "gadm":
            selected = DATASETS[2:]
        else:
            raise SystemExit("only 仅支持 'ne' 或 'gadm'")
    elif skip_gadm:
        selected = DATASETS[:2]

    # 下载 + 解压
    for ds in selected:
        url = ds["url"]
        rel_dir = ds["rel_dir"]
        is_zip = ds["is_zip"]
        marker = ds["marker"]

        out_dir = target_dir / rel_dir
        out_dir.mkdir(parents=True, exist_ok=True)

        filename = ds.get("name", "data") + (".zip" if is_zip else ("" if marker.endswith(".gpkg") else "")) \
            if is_zip else Path(url).name
        out_path = out_dir / filename

        # 跳过逻辑（已存在/已解压）
        if not force:
            if not is_zip and (out_dir / marker).exists():
                print(f"✅ 已存在（gpkg）：{out_dir/marker}")
                continue
            if is_zip and _marker_exists(out_dir, marker):
                print(f"✅ 已解压（shp）：{out_dir/marker}")
                continue

        # 下载
        try:
            if out_path.exists() and out_path.stat().st_size == 0:
                out_path.unlink()
            download(url, out_path)
        except Exception as e:
            print(f"  ⏳ 重试触发：{e}")
            download(url, out_path)

        # 解压 / 完成提示
        if is_zip:
            try:
                unzip(out_path, out_dir, keep_zip=keep_zip)
            except Exception as e:
                print(f"  ⚠️ 解压失败，尝试重下：{e}")
                try:
                    out_path.unlink()
                except Exception:
                    pass
                download(url, out_path)
                unzip(out_path, out_dir, keep_zip=keep_zip)
            print(f"   └─ 完成：{out_dir}")
        else:
            print(f"   └─ 完成：{out_path}")

    # 提取港澳
    if extract_hkmo:
        if _have_geopandas():
            print("\n🔎 执行港澳提取（GADM L1 + NE admin0）…")
            try:
                _subset_save_gadm_hk_mo(target_dir)
            except Exception as e:
                print(f"  ⚠️ GADM 港澳提取失败：{e}")
            try:
                _subset_save_ne_hk_mo(target_dir)
            except Exception as e:
                print(f"  ⚠️ NE 港澳提取失败：{e}")
        else:
            print("\nℹ️ 未安装 geopandas，跳过港澳提取。需要时请：uv sync --extra maps")

    print("\n🎉 全部完成！")
    print("📌 说明：")
    print("  • 香港/澳门：在 GADM 中国 L1（gadm41_CHN_1.*）中，NAME_1=Hong Kong / Macao。")
    print("  • 台湾：使用 TWN 包（gadm41_TWN_*）。")
    print("  • Natural Earth：admin0/admin1 已含香港/澳门/台湾几何。")
    print("\n在你的项目中：")
    print("  — basemap_root 指向此目录，例如： --basemap-root data/geo")
    print("  — 世界底图：world/natural_earth/admin0 / admin1")
    print("  — 中国分级：china/gadm/(gpkg|shp) ；台湾：taiwan/gadm/(gpkg|shp)")
    print("  — 港澳单独文件：")
    print("      china/regions/hkg/gadm41_HKG_1.gpkg  / …/gadm41_HKG_1.geojson")
    print("      china/regions/mac/gadm41_MAC_1.gpkg  / …/gadm41_MAC_1.geojson")
    print("      world/regions/hkg/ne_HKG_admin0.gpkg / …/ne_HKG_admin0.geojson")
    print("      world/regions/mac/ne_MAC_admin0.gpkg / …/ne_MAC_admin0.geojson")

def main():
    ap = argparse.ArgumentParser(description="下载离线底图（NE + GADM 中国/台湾）并可选提取港澳")
    ap.add_argument("--dir", required=True, help="输出目录，如 data/geo")
    ap.add_argument("--only", choices=["ne", "gadm"], help="仅下载 'ne' 或 'gadm'")
    ap.add_argument("--skip-gadm", action="store_true", help="仅下载 Natural Earth")
    ap.add_argument("--keep-zip", action="store_true", help="保留下载的 .zip（默认保留）")
    ap.add_argument("--force", action="store_true", help="强制重新下载/解压（忽略已存在标记）")
    ap.add_argument("--no-extract-hkmo", dest="extract_hkmo", action="store_false",
                    help="不要执行港澳提取（默认会提取）")
    ap.set_defaults(extract_hkmo=True)
    args = ap.parse_args()

    run(
        Path(args.dir),
        args.only,
        args.skip_gadm,
        keep_zip=args.keep_zip or True,
        force=args.force or False,
        extract_hkmo=args.extract_hkmo,
    )

if __name__ == "__main__":
    main()

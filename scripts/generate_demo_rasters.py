# -*- coding: utf-8 -*-
# 更“专业 & 酷炫”的演示栅格生成脚本（COG-like 写出、fBm 程序化地形）
# 依赖：pip install rasterio numpy
from __future__ import annotations
from pathlib import Path
import argparse
import numpy as np

try:
    import rasterio
    from rasterio.transform import from_bounds
    from rasterio.enums import Resampling
except Exception as e:
    raise SystemExit("需要 rasterio：请先 `pip install rasterio`") from e


# -----------------------------
# 工具：稳健写 GeoTIFF（COG-like；失败自动降级）
# -----------------------------
def _write_geotiff(out_path: Path, arr: np.ndarray, bounds, compress: str | None = "deflate"):
    left, bottom, right, top = bounds
    height, width = arr.shape
    transform = from_bounds(left, bottom, right, top, width, height)

    profile = {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": 1,
        "dtype": "float32",
        "crs": "EPSG:4326",
        "transform": transform,
        # COG-like 关键参数
        "BIGTIFF": "IF_SAFER",
        "tiled": True,
        "blockxsize": 256,
        "blockysize": 256,
        "interleave": "band",
    }
    if compress:
        profile["compress"] = compress
        # 浮点 + deflate 建议 predictor=2
        profile["predictor"] = 2

    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with rasterio.open(out_path, "w", **profile) as dst:
            dst.write(arr.astype("float32"), 1)
            # 可选：构建多级概览，提高浏览/叠加性能
            try:
                dst.build_overviews([2, 4, 8, 16], Resampling.average)
                dst.update_tags(ns="rio_overview", resampling="average")
            except Exception:
                # 某些最小化 GDAL 构建不支持概览，忽略即可
                pass
    except Exception:
        # 压缩/瓦片等选项不被当前 GDAL 支持时 → 退化为最小配置
        fallback = {k: v for k, v in profile.items()
                    if k not in {"compress", "predictor", "tiled", "blockxsize", "blockysize", "interleave", "BIGTIFF"}}
        with rasterio.open(out_path, "w", **fallback) as dst:
            dst.write(arr.astype("float32"), 1)


# -----------------------------
# 程序化地形：多谱段 fBm + 山脊噪声 + 热点 + 纬向梯度
# -----------------------------
def _spectral_fbm(shape: tuple[int, int], betas=(1.7, 2.0, 2.5), weights=(0.55, 0.3, 0.15), rng=None) -> np.ndarray:
    """频域滤波合成 fBm：对白噪声做 FFT → 乘以 |k|^-beta → iFFT；多 beta 混合"""
    if rng is None:
        rng = np.random.default_rng(42)
    h, w = shape
    ky = np.fft.fftfreq(h).reshape(-1, 1)
    kx = np.fft.fftfreq(w).reshape(1, -1)
    k = np.sqrt(kx * kx + ky * ky)
    k[0, 0] = 1.0  # 避免除零

    acc = np.zeros((h, w), dtype=np.float64)
    for beta, wgt in zip(betas, weights):
        white = rng.standard_normal((h, w))
        F = np.fft.fft2(white)
        Hk = 1.0 / (k ** float(beta))
        field = np.fft.ifft2(F * Hk).real
        # 每层标准化后再加权
        fmin, fmax = float(np.min(field)), float(np.max(field))
        fptp = max(fmax - fmin, 1e-12)
        field = (field - fmin) / fptp
        acc += wgt * field
    # 全局归一
    amin, amax = float(np.min(acc)), float(np.max(acc))
    rngv = max(amax - amin, 1e-12)
    acc = (acc - amin) / rngv
    return acc.astype(np.float32)


def _ridged(x: np.ndarray) -> np.ndarray:
    """山脊噪声：把中间低、两侧高的纹理转换成脊线（类似 terrain ridges）"""
    y = 1.0 - np.abs(2.0 * x - 1.0)
    return np.clip(y, 0.0, 1.0).astype(np.float32)


def _gaussian_bump(LON, LAT, lon0, lat0, sx, sy):
    return np.exp(-(((LON - lon0) ** 2) / (2 * sx ** 2) + ((LAT - lat0) ** 2) / (2 * sy ** 2)))


def _normalize01(a: np.ndarray, robust: bool = True) -> np.ndarray:
    """兼容旧版 NumPy：不用 np.nanptp，改用 nanmax-nanmin。"""
    if robust:
        p2, p98 = np.nanpercentile(a, [2, 98])
        rngv = max(float(p98 - p2), 1e-12)
        a = (a - p2) / rngv
    else:
        amin = float(np.nanmin(a))
        amax = float(np.nanmax(a))
        rngv = max(amax - amin, 1e-12)
        a = (a - amin) / rngv
    return np.clip(a, 0.0, 1.0).astype(np.float32)


def _make_demo_array(width: int, height: int, bounds, seed: int = 42) -> np.ndarray:
    left, bottom, right, top = bounds
    lon = np.linspace(left, right, width, dtype=np.float64)
    lat = np.linspace(top, bottom, height, dtype=np.float64)  # 从上到下
    LON, LAT = np.meshgrid(lon, lat)

    rng = np.random.default_rng(seed)

    # 1) 多谱段 fBm 基础地形
    base = _spectral_fbm((height, width), betas=(1.6, 1.9, 2.3, 2.7), weights=(0.45, 0.3, 0.18, 0.07), rng=rng)

    # 2) 山脊噪声（凸显山脉/脊线）
    ridged = _ridged(_spectral_fbm((height, width), betas=(2.2, 2.6, 3.0), weights=(0.6, 0.3, 0.1), rng=rng))

    # 3) 热点（区域可识别度）：中国范围用华北/华东，全球用大西洋与印度洋附近
    if left >= 70 and right <= 136 and bottom >= 15 and top <= 55:
        hot = 0.75 * _gaussian_bump(LON, LAT, 105.0, 37.0, 8.0, 5.2) + 0.55 * _gaussian_bump(LON, LAT, 120.0, 31.0, 6.2, 4.2)
    else:
        hot = 0.65 * _gaussian_bump(LON, LAT, -60.0, 10.0, 20.0, 12.0) + 0.55 * _gaussian_bump(LON, LAT, 90.0, 30.0, 24.0, 14.0)

    # 4) 纬向（气候/温度）渐变：|lat| 越低越高（赤道高、两极低）
    lat_grad = np.cos(np.deg2rad(np.clip(LAT, -85, 85)))  # [0,1] 附近
    lat_grad = _normalize01(lat_grad, robust=False)

    # 5) 微噪声（纹理）
    micro = rng.normal(0.0, 1.0, size=(height, width)).astype(np.float32)
    # 低通一下（通过下采样/上采样实现简易平滑）
    shrink = micro[::4, ::4]
    micro = np.repeat(np.repeat(shrink, 4, axis=0), 4, axis=1)
    micro = micro[:height, :width]
    micro = _normalize01(micro, robust=True)

    # 6) 线性混合（可按需调整权重）→ 更像真实地形/气候叠加
    arr = (
        0.50 * base +
        0.25 * ridged +
        0.15 * hot +
        0.08 * lat_grad +
        0.02 * micro
    ).astype(np.float32)

    # 7) 亮度/对比度微调（S 型曲线）
    arr = np.clip(arr, 0.0, 1.0)
    arr = 1.0 / (1.0 + np.exp(-6.0 * (arr - 0.5)))
    return _normalize01(arr.astype(np.float32), robust=True)


# -----------------------------
# 对外：生成示例栅格（世界 & 中国）
# -----------------------------
def make_demo_raster(out_path: Path, width: int, height: int, bounds, seed: int = 42):
    arr = _make_demo_array(width, height, bounds, seed)
    _write_geotiff(out_path, arr, bounds, compress="deflate")
    print(f"✅ 写出：{out_path.resolve()}  |  size={width}x{height}  |  bounds={bounds}  |  range=[{arr.min():.3f},{arr.max():.3f}]")
    if not out_path.exists():
        raise RuntimeError(f"❌ 文件未生成：{out_path.resolve()}")


def main():
    ap = argparse.ArgumentParser(description="生成示例 GeoTIFF（全球 & 中国），更专业更酷炫")
    ap.add_argument("--out-dir", type=str, default=str(Path.cwd() / "data" / "geo"),
                    help="输出目录（默认：当前目录下 data/geo）")
    ap.add_argument("--skip-world", action="store_true", help="跳过生成全球示例")
    ap.add_argument("--skip-china", action="store_true", help="跳过生成中国示例")
    ap.add_argument("--seed", type=int, default=42, help="随机种子（可复现实验）")
    ap.add_argument("--world-size", type=str, default="1200x700", help="全球尺寸，形如 1200x700")
    ap.add_argument("--china-size", type=str, default="900x700", help="中国尺寸，形如 900x700")
    args = ap.parse_args()

    def _parse_size(s: str) -> tuple[int, int]:
        try:
            w, h = s.lower().split("x")
            return int(w), int(h)
        except Exception:
            return (1200, 700)

    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if not args.skip_world:
        w, h = _parse_size(args.world_size)
        make_demo_raster(
            out_path=out_dir / "demo_world.tif",
            width=w, height=h,
            bounds=(-180.0, -60.0, 180.0, 85.0),
            seed=args.seed,
        )

    if not args.skip_china:
        w, h = _parse_size(args.china_size)
        make_demo_raster(
            out_path=out_dir / "demo_china.tif",
            width=w, height=h,
            bounds=(73.5, 18.0, 134.8, 53.6),
            seed=args.seed + 7,  # 稍微变个种子，两个栅格风格有差异
        )

    print("\n完成。可直接叠加测试：")
    print(f"  - {(out_dir / 'demo_world.tif').resolve()} （basemap='world_admin0'）")
    print(f"  - {(out_dir / 'demo_china.tif').resolve()} （basemap='china_l1'）")


if __name__ == "__main__":
    main()
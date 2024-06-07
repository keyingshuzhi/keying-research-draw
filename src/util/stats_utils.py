# -*- coding: utf-8 -*-
# @Time: 2025/10/23 上午10:20
# @Author: 柯影数智
# @File: stats_utils.py
# @Email: 1090461393@qq.com
# @SoftWare: PyCharm

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Optional, Sequence, Tuple, Union, Callable

import numpy as np

try:
    from scipy import stats as _stats  # type: ignore
except Exception:  # 兼容无 SciPy 环境
    _stats = None  # type: ignore


ArrayLike = Union[Sequence[float], np.ndarray]


# ==============================
# 统计：Pearson 等
# ==============================
@dataclass(frozen=True)
class PearsonResult:
    """Pearson 相关结果统一返回结构。"""
    r: float
    p: Optional[float]
    n: int
    method: str  # 'scipy' | 'approx' | 'invalid'
    t_stat: Optional[float] = None


class StatsUtils:
    """统计与清洗工具类。"""

    # ========== 数值清洗 ==========
    @staticmethod
    def ensure_1d(a: ArrayLike) -> np.ndarray:
        """
        展平为 1D 并去除 NaN；统一为 float。
        兼容 list/tuple/np.ndarray/pandas.Series 等序列类型。
        """
        arr = np.asarray(a, dtype=float).ravel()
        return arr[~np.isnan(arr)]

    # ========== Pearson 相关 ==========
    @staticmethod
    def pearson_r_p(x: ArrayLike, y: ArrayLike) -> PearsonResult:
        """
        计算 Pearson r 与 p 值。
        - 优先使用 SciPy (scipy.stats.pearsonr) 得到精确 p；
        - 无 SciPy 时：返回 r 与 t 统计量近似（p=None）。
        - 边界/退化情形（如零方差、样本量 < 3）：返回 method='invalid'。
        """
        xx = np.asarray(x, dtype=float).ravel()
        yy = np.asarray(y, dtype=float).ravel()
        if xx.size != yy.size:
            n = int(min(xx.size, yy.size))
            return PearsonResult(r=float("nan"), p=None, n=n, method="invalid", t_stat=None)

        pairwise_mask = np.isfinite(xx) & np.isfinite(yy)
        xx = xx[pairwise_mask]
        yy = yy[pairwise_mask]

        n = int(xx.size)
        if n < 3:
            return PearsonResult(r=float("nan"), p=None, n=n, method="invalid", t_stat=None)

        # 零方差直接判 invalid
        if np.isclose(np.std(xx), 0.0) or np.isclose(np.std(yy), 0.0):
            return PearsonResult(r=float("nan"), p=None, n=n, method="invalid", t_stat=None)

        # 计算 r
        with np.errstate(all="ignore"):
            r = float(np.corrcoef(xx, yy)[0, 1])
        if not np.isnan(r):
            r = max(-1.0, min(1.0, r))

        # SciPy 路径
        if _stats is not None:
            try:
                pr = _stats.pearsonr(xx, yy)
                if hasattr(pr, "statistic") and hasattr(pr, "pvalue"):
                    r_sci = float(pr.statistic);
                    pval = float(pr.pvalue)
                else:
                    r_sci, pval = float(pr[0]), float(pr[1])
                return PearsonResult(r=r_sci, p=pval, n=n, method="scipy", t_stat=None)
            except Exception:
                pass

        # 近似路径
        if n <= 2 or np.isnan(r) or abs(r) >= 1:
            return PearsonResult(r=r, p=None, n=n, method="approx", t_stat=None)

        t = abs(r) * math.sqrt((n - 2) / max(1e-12, 1 - r * r))
        return PearsonResult(r=r, p=None, n=n, method="approx", t_stat=t)

    @staticmethod
    def fisher_ci(r: float, n: int, alpha: float = 0.05) -> Tuple[float, float]:
        """
        Pearson r 的 (1-alpha) 置信区间（Fisher z 近似，无需 SciPy）。
        """
        if n < 4 or np.isnan(r):
            return (float("nan"), float("nan"))

        r = max(-0.999999, min(0.999999, float(r)))
        z = 0.5 * math.log((1 + r) / (1 - r))
        se = 1.0 / math.sqrt(max(1.0, n - 3))
        z_quant = 1.959963984540054  # ~= norm.isf(0.025)

        z_low = z - z_quant * se
        z_high = z + z_quant * se

        def inv_z(zz: float) -> float:
            ee = math.exp(2 * zz)
            return (ee - 1) / (ee + 1)

        return (inv_z(z_low), inv_z(z_high))


# ========== 兼容层：保留旧函数名 ==========
def ensure_1d(a: ArrayLike) -> np.ndarray:
    return StatsUtils.ensure_1d(a)


def pearson_r_p(x: ArrayLike, y: ArrayLike) -> Tuple[float, Optional[float]]:
    res = StatsUtils.pearson_r_p(x, y)
    return res.r, res.p


# ==============================
# 绘图保存工具（与标题同名 + 所见即所得）
# ==============================
def slugify_filename(title: Optional[str], maxlen: int = 120) -> str:
    """
    将标题转为文件系统友好的文件名：
    - 保留中文、英文字母、数字、空格与常见符号（_-.）
    - 去掉非法字符，空白压缩为单个下划线
    - 截断到 maxlen
    """
    s = (title or "").strip()
    s = re.sub(r'[<>:"/\\|?*\t]+', " ", s)  # Windows 非法字符
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^\w\-\.\u4e00-\u9fff ]+", " ", s, flags=re.UNICODE)
    s = s.strip()
    s = re.sub(r"\s+", "_", s)
    if not s:
        s = "figure"
    if len(s) > maxlen:
        s = s[:maxlen].rstrip("_")
    return s


def pick_figure_title(fig) -> Optional[str]:
    """
    从 Figure 提取标题：优先 suptitle，其次第一个有标题的 Axes。
    """
    if fig is None:
        return None
    # suptitle
    try:
        if getattr(fig, "_suptitle", None) is not None:
            t = fig._suptitle.get_text()
            if t and t.strip():
                return t.strip()
    except Exception:
        pass
    # axes title
    for ax in getattr(fig, "axes", []):
        try:
            t = (ax.get_title() or "").strip()
            if t:
                return t
        except Exception:
            continue
    return None


def save_figure(
        outpath_func: Callable[[str, Optional[str]], str],
        name: Optional[str] = None,
        fig: Optional["plt.Figure"] = None,
        fmt: Optional[str] = None,
        dpi: Optional[int] = None,
        match_screen: bool = True,
        tight: bool = False,
) -> str:
    """
    保存图像（工具函数版）：
    - outpath_func: 形如 cfg.outpath(name, fmt) -> 完整路径字符串
    - 若 name 未提供，则自动使用图标题（suptitle/axes.title）生成“与标题一致”的文件名
    - match_screen=True：保存与屏幕显示一致（DPI='figure' 且不 tight 裁剪）
    - tight=True：期刊导出使用 bbox_inches='tight'（与 match_screen 不建议同开）
    """
    try:
        import matplotlib.pyplot as plt  # type: ignore
    except Exception as e:
        raise RuntimeError("matplotlib 未安装，无法保存图像。") from e

    fig = fig or plt.gcf()

    # 让布局计算收敛，确保与窗口一致
    try:
        fig.canvas.draw()
    except Exception:
        pass

    # 自动从标题生成文件名
    if not name:
        title_text = pick_figure_title(fig)
        name = slugify_filename(title_text or "figure")

    path = outpath_func(name, fmt)

    # DPI：WYSIWYG 用 'figure'；否则按参数/配置
    final_dpi = "figure" if (match_screen and dpi is None) else (dpi or 300)
    # bbox：WYSIWYG 不裁剪；期刊导出可 tight
    bbox = "tight" if tight else None

    fig.savefig(
        path,
        dpi=final_dpi,
        bbox_inches=bbox,
        facecolor=fig.get_facecolor(),
        edgecolor="none",
    )
    return path


__all__ = [
    "ArrayLike",
    "PearsonResult",
    "StatsUtils",
    "ensure_1d",
    "pearson_r_p",
    "slugify_filename",
    "pick_figure_title",
    "save_figure",
]

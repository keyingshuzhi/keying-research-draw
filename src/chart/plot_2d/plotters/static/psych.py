from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from src.chart.plot_2d.static_analysis import _apply_axes_text
from src.util.dependency_hints import format_missing_dependency

def likert_plot(
    self,
    item: ArrayLike,
    response: ArrayLike,
    counts: Optional[ArrayLike] = None,
    title: Optional[str] = None,
    figsize: Tuple[float, float] = (7.2, 5.4),
) -> Tuple[plt.Figure, plt.Axes]:
    try:
        import pandas as pd  # type: ignore
    except Exception as e:
        raise RuntimeError(
            format_missing_dependency(
                package="pandas",
                feature="likert_plot",
                recommended_extra="data",
            )
        ) from e
    df = pd.DataFrame({"item": item, "resp": response})
    if counts is None:
        df["count"] = 1
    else:
        df["count"] = counts

    pivot = df.groupby(["item", "resp"])["count"].sum().unstack(fill_value=0)
    resp_vals = list(pivot.columns)
    try:
        resp_vals = sorted(resp_vals, key=lambda x: float(x))
    except Exception:
        resp_vals = sorted(resp_vals)
    pivot = pivot[resp_vals]
    total = pivot.sum(axis=1).replace(0, 1)
    pct = pivot.div(total, axis=0)

    mid = len(resp_vals) // 2
    neg = resp_vals[:mid]
    pos = resp_vals[mid + 1:]
    neutral = resp_vals[mid] if len(resp_vals) % 2 == 1 else None

    fig, ax = self._new_subplots(figsize)
    y = np.arange(pct.shape[0])

    left = np.zeros(pct.shape[0])
    for r in neg[::-1]:
        vals = -pct[r].values
        ax.barh(y, vals, left=left, label=str(r))
        left += vals

    right = np.zeros(pct.shape[0])
    if neutral is not None:
        vals = pct[neutral].values
        ax.barh(y, vals / 2, left=-vals / 2, color="#9CA3AF", label=str(neutral))
    for r in pos:
        vals = pct[r].values
        ax.barh(y, vals, left=right, label=str(r))
        right += vals

    ax.set_yticks(y)
    ax.set_yticklabels(pct.index.astype(str))
    ax.set_xlabel("Proportion")
    if title:
        ax.set_title(title)
    ax.legend(frameon=False, ncol=3, fontsize=8)
    ax.grid(axis="x", alpha=0.2, linestyle=":")
    return fig, ax

# -----------------------------
# 31) Raincloud（心理）
# -----------------------------

def raincloud_plot(
    self,
    group: ArrayLike,
    value: ArrayLike,
    title: Optional[str] = None,
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    figsize: Tuple[float, float] = (7.0, 4.8),
) -> Tuple[plt.Figure, plt.Axes]:
    g = np.asarray(group)
    v = np.asarray(value, dtype=float)
    mask = np.isfinite(v)
    g, v = g[mask], v[mask]
    uniq = list(dict.fromkeys(g.tolist()))
    data = [v[g == u] for u in uniq]

    fig, ax = self._new_subplots(figsize)
    parts = ax.violinplot(data, showmeans=False, showmedians=False, showextrema=False)
    for pc in parts["bodies"]:
        pc.set_alpha(0.5)
        pc.set_facecolor("#93C5FD")

    ax.boxplot(data, widths=0.15, patch_artist=True,
               boxprops=dict(facecolor="#111827", alpha=0.6, edgecolor="none"))
    for i, vals in enumerate(data, start=1):
        jitter = (np.random.rand(len(vals)) - 0.5) * 0.1
        ax.scatter(np.full_like(vals, i, dtype=float) + jitter, vals,
                   s=10, alpha=0.6, color="#2563EB", edgecolors="none")

    ax.set_xticks(range(1, len(uniq) + 1))
    ax.set_xticklabels([str(u) for u in uniq])
    _apply_axes_text(ax, title, xlabel, ylabel)
    ax.grid(axis="y", alpha=0.2, linestyle=":")
    return fig, ax

# -----------------------------
# 32) IRT ICC（心理）
# -----------------------------

def irt_icc_plot(
    self,
    item: ArrayLike,
    a: ArrayLike,
    b: ArrayLike,
    c: Optional[ArrayLike] = None,
    theta_min: float = -4.0,
    theta_max: float = 4.0,
    title: Optional[str] = None,
    figsize: Tuple[float, float] = (7.2, 5.0),
) -> Tuple[plt.Figure, plt.Axes]:
    item = np.asarray(item, dtype=object)
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    n = min(item.size, a.size, b.size)
    item, a, b = item[:n], a[:n], b[:n]
    if c is None:
        c = np.zeros_like(a)
    else:
        c = np.asarray(c, dtype=float)[:n]

    theta = np.linspace(theta_min, theta_max, 200)
    fig, ax = self._new_subplots(figsize)
    for it, aa, bb, cc in zip(item, a, b, c):
        p = cc + (1 - cc) / (1 + np.exp(-aa * (theta - bb)))
        ax.plot(theta, p, lw=1.6, label=str(it))
    ax.set_xlabel("Theta")
    ax.set_ylabel("P(theta)")
    if title:
        ax.set_title(title)
    ax.legend(frameon=False, fontsize=8, ncol=2)
    ax.grid(alpha=0.2, linestyle=":")
    return fig, ax

# -----------------------------
# 33) Factor Loadings（心理）
# -----------------------------

def factor_loadings_plot(
    self,
    factor: ArrayLike,
    item: ArrayLike,
    loading: ArrayLike,
    title: Optional[str] = None,
    figsize: Tuple[float, float] = (7.2, 5.0),
) -> Tuple[plt.Figure, plt.Axes]:
    f = np.asarray(factor, dtype=object)
    it = np.asarray(item, dtype=object)
    ld = np.asarray(loading, dtype=float)
    n = min(f.size, it.size, ld.size)
    f, it, ld = f[:n], it[:n], ld[:n]
    uniq = list(dict.fromkeys(f.tolist()))

    fig, axes = plt.subplots(len(uniq), 1, figsize=figsize, constrained_layout=True, sharex=True)
    if len(uniq) == 1:
        axes = [axes]
    for ax, u in zip(axes, uniq):
        m = f == u
        items = it[m]
        vals = ld[m]
        order = np.argsort(vals)
        items, vals = items[order], vals[order]
        y = np.arange(len(items))
        ax.hlines(y, 0, vals, color="#2563EB", lw=2.0)
        ax.scatter(vals, y, color="#2563EB", s=20)
        ax.set_yticks(y)
        ax.set_yticklabels(items.astype(str))
        ax.axvline(0, color="#9CA3AF", lw=1.0, ls="--")
        ax.set_title(str(u))
        ax.grid(axis="x", alpha=0.2, linestyle=":")
    if title:
        fig.suptitle(title)
    return fig, axes[0]

# -----------------------------
# 34) Interaction Plot（心理）
# -----------------------------

def interaction_plot(
    self,
    x: ArrayLike,
    group: ArrayLike,
    value: ArrayLike,
    title: Optional[str] = None,
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    figsize: Tuple[float, float] = (6.8, 5.0),
) -> Tuple[plt.Figure, plt.Axes]:
    try:
        import pandas as pd  # type: ignore
    except Exception as e:
        raise RuntimeError(
            format_missing_dependency(
                package="pandas",
                feature="interaction_plot",
                recommended_extra="data",
            )
        ) from e
    df = pd.DataFrame({"x": x, "group": group, "y": value})
    fig, ax = self._new_subplots(figsize)
    for gname, sub in df.groupby("group"):
        stats = sub.groupby("x")["y"].agg(["mean", "count", "std"])
        mean = stats["mean"].values
        n = stats["count"].values
        sd = stats["std"].fillna(0).values
        ci = 1.96 * sd / np.maximum(np.sqrt(n), 1)
        xs = stats.index.values
        ax.errorbar(xs, mean, yerr=ci, marker="o", lw=1.6, label=str(gname))
    _apply_axes_text(ax, title, xlabel, ylabel)
    ax.legend(frameon=False, fontsize=9)
    ax.grid(alpha=0.2, linestyle=":")
    return fig, ax




from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from src.chart.plot_2d.static_analysis import _apply_axes_text
from src.util.dependency_hints import format_missing_dependency

def stress_strain_plot(
    self,
    strain: ArrayLike,
    stress: ArrayLike,
    title: Optional[str] = None,
    elastic_max: Optional[float] = None,
    yield_offset: Optional[float] = None,
    figsize: Tuple[float, float] = (6.6, 5.0),
) -> Tuple[plt.Figure, plt.Axes]:
    x = np.asarray(strain, dtype=float).ravel()
    y = np.asarray(stress, dtype=float).ravel()
    n = min(x.size, y.size)
    x, y = x[:n], y[:n]
    mask = np.isfinite(x) & np.isfinite(y)
    x, y = x[mask], y[mask]

    fig, ax = self._new_subplots(figsize)
    ax.plot(x, y, color="#2563EB", lw=2.0)

    if elastic_max is not None:
        m = x <= elastic_max
        if np.any(m):
            coeff = np.polyfit(x[m], y[m], 1)
            slope = coeff[0]
            ax.plot(x[m], np.polyval(coeff, x[m]), color="#111827", ls="--", lw=1.2,
                    label=f"E={slope:.3g}")
            if yield_offset is not None:
                y_offset = slope * (x - yield_offset)
                idx = np.argmax(y >= y_offset)
                ax.plot(x, y_offset, color="#6B7280", ls=":", lw=1.0, label="0.2% offset")
                if idx > 0:
                    ax.scatter([x[idx]], [y[idx]], color="#EF4444", zorder=3)

    ax.set_xlabel("Strain")
    ax.set_ylabel("Stress")
    if title:
        ax.set_title(title)
    ax.grid(alpha=0.2, linestyle=":")
    ax.legend(frameon=False)
    return fig, ax

# -----------------------------
# 17) XRD（材料）
# -----------------------------

def xrd_plot(
    self,
    two_theta: ArrayLike,
    intensity: ArrayLike,
    group: Optional[ArrayLike] = None,
    title: Optional[str] = None,
    xlabel: str = "2θ",
    ylabel: str = "Intensity",
    figsize: Tuple[float, float] = (7.0, 5.0),
) -> Tuple[plt.Figure, plt.Axes]:
    x = np.asarray(two_theta, dtype=float).ravel()
    y = np.asarray(intensity, dtype=float).ravel()
    n = min(x.size, y.size)
    x, y = x[:n], y[:n]
    mask = np.isfinite(x) & np.isfinite(y)
    x, y = x[mask], y[mask]
    g = np.asarray(group)[mask] if group is not None else None

    fig, ax = self._new_subplots(figsize)
    if g is None:
        ax.plot(x, y, lw=1.6, color="#2563EB")
    else:
        uniq = list(dict.fromkeys(g.tolist()))
        for u in uniq:
            m = g == u
            ax.plot(x[m], y[m], lw=1.4, label=str(u))
        ax.legend(frameon=False, fontsize=9)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)
    ax.grid(alpha=0.2, linestyle=":")
    return fig, ax

# -----------------------------
# 18) Raman/FTIR（材料）
# -----------------------------

def raman_plot(
    self,
    x: ArrayLike,
    y: ArrayLike,
    group: Optional[ArrayLike] = None,
    title: Optional[str] = None,
    invert_x: bool = False,
    xlabel: str = "Raman Shift",
    ylabel: str = "Intensity",
    figsize: Tuple[float, float] = (7.0, 5.0),
) -> Tuple[plt.Figure, plt.Axes]:
    xx = np.asarray(x, dtype=float).ravel()
    yy = np.asarray(y, dtype=float).ravel()
    n = min(xx.size, yy.size)
    xx, yy = xx[:n], yy[:n]
    mask = np.isfinite(xx) & np.isfinite(yy)
    xx, yy = xx[mask], yy[mask]
    g = np.asarray(group)[mask] if group is not None else None

    fig, ax = self._new_subplots(figsize)
    if g is None:
        ax.plot(xx, yy, lw=1.6, color="#2563EB")
    else:
        uniq = list(dict.fromkeys(g.tolist()))
        for u in uniq:
            m = g == u
            ax.plot(xx[m], yy[m], lw=1.4, label=str(u))
        ax.legend(frameon=False, fontsize=9)
    if invert_x:
        ax.invert_xaxis()
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)
    ax.grid(alpha=0.2, linestyle=":")
    return fig, ax

# -----------------------------
# 19) Phase Diagram（材料）
# -----------------------------

def phase_plot(
    self,
    x: ArrayLike,
    y: ArrayLike,
    z: Optional[ArrayLike] = None,
    title: Optional[str] = None,
    xlabel: str = "X",
    ylabel: str = "Y",
    figsize: Tuple[float, float] = (6.8, 5.4),
) -> Tuple[plt.Figure, plt.Axes]:
    xx = np.asarray(x, dtype=float).ravel()
    yy = np.asarray(y, dtype=float).ravel()
    n = min(xx.size, yy.size)
    xx, yy = xx[:n], yy[:n]
    mask = np.isfinite(xx) & np.isfinite(yy)
    xx, yy = xx[mask], yy[mask]
    zz = np.asarray(z, dtype=float).ravel()[:n][mask] if z is not None else None

    fig, ax = self._new_subplots(figsize)
    if zz is None:
        ax.scatter(xx, yy, s=16, alpha=0.8, color="#2563EB")
    else:
        ux, uy = np.unique(xx), np.unique(yy)
        if ux.size * uy.size == zz.size:
            try:
                import pandas as pd  # type: ignore
                df = pd.DataFrame({"x": xx, "y": yy, "z": zz})
                pivot = df.pivot(index="y", columns="x", values="z")
                X, Y = np.meshgrid(pivot.columns.values, pivot.index.values)
                c = ax.contourf(X, Y, pivot.values, levels=12, cmap="viridis")
                fig.colorbar(c, ax=ax, label="Value")
            except Exception:
                sc = ax.scatter(xx, yy, c=zz, s=18, cmap="viridis")
                fig.colorbar(sc, ax=ax, label="Value")
        else:
            sc = ax.scatter(xx, yy, c=zz, s=18, cmap="viridis")
            fig.colorbar(sc, ax=ax, label="Value")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)
    ax.grid(alpha=0.2, linestyle=":")
    return fig, ax

# -----------------------------
# 20) Hysteresis（材料）
# -----------------------------

def hysteresis_plot(
    self,
    x: ArrayLike,
    y: ArrayLike,
    group: Optional[ArrayLike] = None,
    title: Optional[str] = None,
    figsize: Tuple[float, float] = (6.6, 5.0),
) -> Tuple[plt.Figure, plt.Axes]:
    xx = np.asarray(x, dtype=float).ravel()
    yy = np.asarray(y, dtype=float).ravel()
    n = min(xx.size, yy.size)
    xx, yy = xx[:n], yy[:n]
    mask = np.isfinite(xx) & np.isfinite(yy)
    xx, yy = xx[mask], yy[mask]
    g = np.asarray(group)[mask] if group is not None else None

    fig, ax = self._new_subplots(figsize)
    if g is None:
        ax.plot(xx, yy, lw=1.6, color="#2563EB")
    else:
        uniq = list(dict.fromkeys(g.tolist()))
        for u in uniq:
            m = g == u
            ax.plot(xx[m], yy[m], lw=1.4, label=str(u))
        ax.legend(frameon=False, fontsize=9)
    ax.set_xlabel("Field / Voltage")
    ax.set_ylabel("Response")
    if title:
        ax.set_title(title)
    ax.grid(alpha=0.2, linestyle=":")
    return fig, ax

# -----------------------------
# 21) Spectral Signature（遥感）
# -----------------------------


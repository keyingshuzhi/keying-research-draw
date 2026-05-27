from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from src.chart.plot_2d.static_analysis import _apply_axes_text
from src.util.dependency_hints import format_missing_dependency

def spectral_signature_plot(
    self,
    wavelength: ArrayLike,
    reflectance: ArrayLike,
    group: Optional[ArrayLike] = None,
    title: Optional[str] = None,
    xlabel: str = "Wavelength",
    ylabel: str = "Reflectance",
    figsize: Tuple[float, float] = (7.2, 5.0),
) -> Tuple[plt.Figure, plt.Axes]:
    x = np.asarray(wavelength, dtype=float).ravel()
    y = np.asarray(reflectance, dtype=float).ravel()
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
# 22) Index Time Series（遥感）
# -----------------------------

def index_time_series_plot(
    self,
    time: ArrayLike,
    value: ArrayLike,
    group: Optional[ArrayLike] = None,
    title: Optional[str] = None,
    xlabel: str = "Time",
    ylabel: str = "Value",
    figsize: Tuple[float, float] = (7.2, 4.8),
) -> Tuple[plt.Figure, plt.Axes]:
    t = np.asarray(time)
    v = np.asarray(value, dtype=float).ravel()
    n = min(t.size, v.size)
    t, v = t[:n], v[:n]
    mask = np.isfinite(v)
    t, v = t[mask], v[mask]
    g = np.asarray(group)[mask] if group is not None else None

    try:
        import pandas as pd  # type: ignore
        t = pd.to_datetime(t)
    except Exception:
        pass

    fig, ax = self._new_subplots(figsize)
    if g is None:
        ax.plot(t, v, lw=1.6, color="#2563EB")
    else:
        uniq = list(dict.fromkeys(g.tolist()))
        for u in uniq:
            m = g == u
            ax.plot(t[m], v[m], lw=1.4, label=str(u))
        ax.legend(frameon=False, fontsize=9)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)
    ax.grid(alpha=0.2, linestyle=":")
    return fig, ax

# -----------------------------
# 23) Confusion Matrix（遥感）
# -----------------------------

def confusion_matrix_plot(
    self,
    y_true: ArrayLike,
    y_pred: Optional[ArrayLike] = None,
    labels: Optional[Sequence[str]] = None,
    normalize: Optional[str] = None,
    title: Optional[str] = None,
    figsize: Tuple[float, float] = (5.6, 5.0),
) -> Tuple[plt.Figure, plt.Axes]:
    if y_pred is None:
        cm = np.asarray(y_true, dtype=float)
        labs = labels or [str(i) for i in range(cm.shape[0])]
    else:
        yt = np.asarray(y_true)
        yp = np.asarray(y_pred)
        uniq = labels or sorted(set(yt.tolist()) | set(yp.tolist()))
        idx = {k: i for i, k in enumerate(uniq)}
        cm = np.zeros((len(uniq), len(uniq)), dtype=float)
        for a, b in zip(yt, yp):
            cm[idx[a], idx[b]] += 1
        labs = [str(x) for x in uniq]

    if normalize:
        norm = normalize.lower()
        if norm == "true":
            cm = cm / (cm.sum(axis=1, keepdims=True) + 1e-12)
        elif norm == "pred":
            cm = cm / (cm.sum(axis=0, keepdims=True) + 1e-12)
        elif norm == "all":
            cm = cm / (cm.sum() + 1e-12)

    fig, ax = self._new_subplots(figsize)
    im = ax.imshow(cm, cmap="Blues")
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, f"{cm[i, j]:.2f}" if normalize else f"{cm[i, j]:.0f}",
                    ha="center", va="center", fontsize=9)
    ax.set_xticks(range(len(labs)))
    ax.set_yticks(range(len(labs)))
    ax.set_xticklabels(labs, rotation=45, ha="right")
    ax.set_yticklabels(labs)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    if title:
        ax.set_title(title)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    return fig, ax

# -----------------------------
# 24) Class Distribution（遥感）
# -----------------------------

def class_distribution_plot(
    self,
    classes: ArrayLike,
    values: Optional[ArrayLike] = None,
    group: Optional[ArrayLike] = None,
    title: Optional[str] = None,
    figsize: Tuple[float, float] = (7.0, 4.8),
) -> Tuple[plt.Figure, plt.Axes]:
    cls = np.asarray(classes)
    val = np.asarray(values, dtype=float).ravel() if values is not None else None
    g = np.asarray(group) if group is not None else None

    fig, ax = self._new_subplots(figsize)
    if g is None:
        if val is None:
            uniq, counts = np.unique(cls, return_counts=True)
            ax.bar(uniq.astype(str), counts, color="#2563EB")
        else:
            import pandas as pd  # type: ignore
            df = pd.DataFrame({"class": cls, "value": val})
            agg = df.groupby("class")["value"].sum()
            ax.bar(agg.index.astype(str), agg.values, color="#2563EB")
    else:
        import pandas as pd  # type: ignore
        df = pd.DataFrame({"class": cls, "group": g, "value": val if val is not None else 1})
        agg = df.groupby(["group", "class"])["value"].sum().unstack(fill_value=0)
        x = np.arange(agg.shape[1])
        width = 0.8 / max(1, agg.shape[0])
        for i, (grp, row) in enumerate(agg.iterrows()):
            ax.bar(x + i * width, row.values, width=width, label=str(grp))
        ax.set_xticks(x + width * (agg.shape[0] - 1) / 2)
        ax.set_xticklabels(agg.columns.astype(str))
        ax.legend(frameon=False, fontsize=9)
    ax.set_ylabel("Count")
    if title:
        ax.set_title(title)
    ax.grid(axis="y", alpha=0.2, linestyle=":")
    return fig, ax

# -----------------------------
# 25) Candlestick（金融）
# -----------------------------


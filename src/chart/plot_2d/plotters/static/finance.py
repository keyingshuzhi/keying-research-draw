from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from src.chart.plot_2d.static_analysis import _apply_axes_text
from src.util.dependency_hints import format_missing_dependency

def candlestick_plot(
    self,
    dates: ArrayLike,
    open_: ArrayLike,
    high: ArrayLike,
    low: ArrayLike,
    close: ArrayLike,
    volume: Optional[ArrayLike] = None,
    title: Optional[str] = None,
    figsize: Tuple[float, float] = (7.4, 5.6),
) -> Tuple[plt.Figure, plt.Axes]:
    d = np.asarray(dates)
    o = np.asarray(open_, dtype=float).ravel()
    h = np.asarray(high, dtype=float).ravel()
    l = np.asarray(low, dtype=float).ravel()
    c = np.asarray(close, dtype=float).ravel()
    n = min(d.size, o.size, h.size, l.size, c.size)
    d, o, h, l, c = d[:n], o[:n], h[:n], l[:n], c[:n]
    mask = np.isfinite(o) & np.isfinite(h) & np.isfinite(l) & np.isfinite(c)
    d, o, h, l, c = d[mask], o[mask], h[mask], l[mask], c[mask]

    try:
        import pandas as pd  # type: ignore
        d = pd.to_datetime(d)
    except Exception:
        pass

    import matplotlib.dates as mdates
    x = mdates.date2num(d)
    width = (x[1] - x[0]) * 0.6 if x.size > 1 else 0.6

    if volume is not None:
        import matplotlib.gridspec as gridspec
        fig = plt.figure(figsize=figsize)
        gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1], hspace=0.05)
        ax = fig.add_subplot(gs[0])
        axv = fig.add_subplot(gs[1], sharex=ax)
        vol = np.asarray(volume, dtype=float).ravel()[:n][mask]
    else:
        fig, ax = self._new_subplots(figsize)
        axv = None

    for xi, oi, hi, li, ci in zip(x, o, h, l, c):
        color = "#16A34A" if ci >= oi else "#DC2626"
        ax.vlines(xi, li, hi, color=color, linewidth=1.0)
        ax.add_patch(
            plt.Rectangle(
                (xi - width / 2, min(oi, ci)),
                width,
                max(abs(ci - oi), 1e-6),
                facecolor=color,
                edgecolor=color,
                alpha=0.8,
            )
        )

    ax.xaxis_date()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    fig.autofmt_xdate()
    ax.set_ylabel("Price")
    if title:
        ax.set_title(title)
    ax.grid(alpha=0.2, linestyle=":")

    if axv is not None:
        axv.bar(x, vol, width=width, color="#9CA3AF", alpha=0.6)
        axv.set_ylabel("Volume")
        axv.grid(alpha=0.2, linestyle=":")

    return fig, ax

# -----------------------------
# 26) Cumulative Return + Drawdown（金融）
# -----------------------------

def cum_return_drawdown_plot(
    self,
    dates: ArrayLike,
    returns: Optional[ArrayLike] = None,
    price: Optional[ArrayLike] = None,
    title: Optional[str] = None,
    figsize: Tuple[float, float] = (7.2, 5.8),
) -> Tuple[plt.Figure, plt.Axes]:
    d = np.asarray(dates)
    if returns is None and price is None:
        raise ValueError("需要 returns 或 price")

    try:
        import pandas as pd  # type: ignore
        d = pd.to_datetime(d)
    except Exception:
        pass

    if returns is None:
        p = np.asarray(price, dtype=float).ravel()
        ret = np.diff(p) / np.maximum(p[:-1], 1e-12)
        d = d[1:]
    else:
        ret = np.asarray(returns, dtype=float).ravel()
        n = min(d.size, ret.size)
        d, ret = d[:n], ret[:n]

    import matplotlib.gridspec as gridspec
    fig = plt.figure(figsize=figsize)
    gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1.2], hspace=0.08)
    ax = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1], sharex=ax)

    cum = np.cumprod(1 + ret)
    dd = cum / np.maximum.accumulate(cum) - 1

    ax.plot(d, cum - 1, color="#2563EB", lw=1.8, label="Cumulative Return")
    ax.legend(frameon=False)
    ax.grid(alpha=0.2, linestyle=":")

    ax2.fill_between(d, dd, 0, color="#DC2626", alpha=0.4)
    ax2.set_ylabel("Drawdown")
    ax2.grid(alpha=0.2, linestyle=":")

    if title:
        ax.set_title(title)
    return fig, ax

# -----------------------------
# 27) Rolling Volatility + Sharpe（金融）
# -----------------------------

def rolling_stats_plot(
    self,
    dates: ArrayLike,
    returns: ArrayLike,
    window: int = 20,
    risk_free: float = 0.0,
    title: Optional[str] = None,
    figsize: Tuple[float, float] = (7.2, 5.8),
) -> Tuple[plt.Figure, plt.Axes]:
    try:
        import pandas as pd  # type: ignore
    except Exception as e:
        raise RuntimeError(
            format_missing_dependency(
                package="pandas",
                feature="rolling_stats_plot",
                recommended_extra="data",
            )
        ) from e
    d = pd.to_datetime(dates)
    r = pd.Series(np.asarray(returns, dtype=float).ravel(), index=d)
    r = r.sort_index()

    roll_mean = r.rolling(window).mean()
    roll_std = r.rolling(window).std()
    sharpe = (roll_mean - risk_free) / roll_std.replace(0, np.nan)

    import matplotlib.gridspec as gridspec
    fig = plt.figure(figsize=figsize)
    gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1.2], hspace=0.08)
    ax = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1], sharex=ax)

    ax.plot(roll_std.index, roll_std.values, color="#2563EB", lw=1.6, label="Volatility")
    ax.legend(frameon=False)
    ax.grid(alpha=0.2, linestyle=":")
    ax2.plot(sharpe.index, sharpe.values, color="#111827", lw=1.2, label="Sharpe")
    ax2.axhline(0, color="#9CA3AF", lw=1.0, ls="--")
    ax2.legend(frameon=False)
    ax2.grid(alpha=0.2, linestyle=":")

    if title:
        ax.set_title(title)
    return fig, ax

# -----------------------------
# 28) Efficient Frontier（金融）
# -----------------------------

def efficient_frontier_plot(
    self,
    returns_matrix: ArrayLike,
    labels: Optional[Sequence[str]] = None,
    n_portfolios: int = 4000,
    title: Optional[str] = None,
    figsize: Tuple[float, float] = (6.8, 5.4),
) -> Tuple[plt.Figure, plt.Axes]:
    R = np.asarray(returns_matrix, dtype=float)
    if R.ndim != 2 or R.shape[1] < 2:
        raise ValueError("returns_matrix 需为二维且至少两资产列")
    mu = np.mean(R, axis=0)
    cov = np.cov(R, rowvar=False)

    weights = np.random.dirichlet(np.ones(R.shape[1]), size=int(n_portfolios))
    rets = weights @ mu
    vols = np.sqrt(np.einsum("ij,jk,ik->i", weights, cov, weights))
    sharpe = rets / np.maximum(vols, 1e-12)
    best = int(np.argmax(sharpe))

    fig, ax = self._new_subplots(figsize)
    sc = ax.scatter(vols, rets, c=sharpe, cmap="viridis", s=12, alpha=0.8)
    ax.scatter(vols[best], rets[best], color="#EF4444", s=40, label="Max Sharpe")
    fig.colorbar(sc, ax=ax, label="Sharpe")
    ax.set_xlabel("Volatility")
    ax.set_ylabel("Return")
    if title:
        ax.set_title(title)
    ax.legend(frameon=False)
    ax.grid(alpha=0.2, linestyle=":")
    return fig, ax

# -----------------------------
# 29) ACF / PACF（金融）
# -----------------------------

def acf_pacf_plot(
    self,
    series: ArrayLike,
    lags: int = 40,
    title: Optional[str] = None,
    figsize: Tuple[float, float] = (7.2, 4.8),
) -> Tuple[plt.Figure, plt.Axes]:
    x = np.asarray(series, dtype=float).ravel()
    x = x[np.isfinite(x)]
    try:
        from statsmodels.tsa.stattools import acf, pacf  # type: ignore
        acf_vals = acf(x, nlags=lags, fft=True)
        pacf_vals = pacf(x, nlags=lags)
    except Exception:
        x = x - np.mean(x)
        acf_vals = [1.0]
        for k in range(1, lags + 1):
            acf_vals.append(np.corrcoef(x[:-k], x[k:])[0, 1])
        pacf_vals = None

    if pacf_vals is None:
        fig, ax = self._new_subplots(figsize)
        ax.stem(range(len(acf_vals)), acf_vals, basefmt=" ")
        ax.set_title(title or "ACF")
        ax.set_xlabel("Lag")
        ax.set_ylabel("ACF")
        ax.grid(alpha=0.2, linestyle=":")
        return fig, ax

    fig, axes = plt.subplots(1, 2, figsize=figsize, constrained_layout=True)
    axes[0].stem(range(len(acf_vals)), acf_vals, basefmt=" ")
    axes[0].set_title("ACF")
    axes[0].set_xlabel("Lag")
    axes[0].set_ylabel("ACF")
    axes[0].grid(alpha=0.2, linestyle=":")

    axes[1].stem(range(len(pacf_vals)), pacf_vals, basefmt=" ")
    axes[1].set_title("PACF")
    axes[1].set_xlabel("Lag")
    axes[1].set_ylabel("PACF")
    axes[1].grid(alpha=0.2, linestyle=":")
    if title:
        fig.suptitle(title)
    return fig, axes[0]

# -----------------------------
# 30) Likert（心理）
# -----------------------------


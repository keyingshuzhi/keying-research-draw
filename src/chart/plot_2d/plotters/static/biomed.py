from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from src.chart.plot_2d.static_analysis import _apply_axes_text
from src.util.dependency_hints import format_missing_dependency

def ma_plot(
    self,
    mean,
    log2fc,
    pvals: Optional[ArrayLike] = None,
    fc_thresh: float = 1.0,
    p_thresh: float = 0.05,
    title: Optional[str] = None,
    xlabel: str = "Mean",
    ylabel: str = "log2FC",
    figsize: Tuple[float, float] = (6.6, 5.0),
) -> Tuple[plt.Figure, plt.Axes]:
    x = np.asarray(mean, dtype=float).ravel()
    y = np.asarray(log2fc, dtype=float).ravel()
    n = min(x.size, y.size)
    x, y = x[:n], y[:n]
    mask = np.isfinite(x) & np.isfinite(y)
    x, y = x[mask], y[mask]

    fig, ax = self._new_subplots(figsize)
    if pvals is not None:
        pv = np.asarray(pvals, dtype=float).ravel()[:n][mask]
        sig = (pv <= p_thresh) & (np.abs(y) >= fc_thresh)
        ax.scatter(x[~sig], y[~sig], s=16, alpha=0.6, color="#9CA3AF")
        ax.scatter(x[sig], y[sig], s=18, alpha=0.85, color="#EF4444")
    else:
        ax.scatter(x, y, s=16, alpha=0.75, color="#2563EB")

    ax.axhline(+fc_thresh, color="#6B7280", lw=1.0, ls="--")
    ax.axhline(-fc_thresh, color="#6B7280", lw=1.0, ls="--")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)
    ax.grid(alpha=0.25, linestyle=":", linewidth=0.8)
    return fig, ax

# -----------------------------
# 7) 富集 Dotplot（生物）
# -----------------------------

def enrichment_dotplot(
    self,
    terms: Sequence[str],
    pvals: ArrayLike,
    counts: ArrayLike,
    ratio: Optional[ArrayLike] = None,
    top_n: int = 20,
    title: Optional[str] = None,
    figsize: Tuple[float, float] = (7.5, 5.6),
) -> Tuple[plt.Figure, plt.Axes]:
    terms = np.asarray(terms, dtype=object)
    pv = np.asarray(pvals, dtype=float)
    cnt = np.asarray(counts, dtype=float)
    n = min(terms.size, pv.size, cnt.size)
    terms, pv, cnt = terms[:n], pv[:n], cnt[:n]
    mask = np.isfinite(pv) & np.isfinite(cnt)
    terms, pv, cnt = terms[mask], pv[mask], cnt[mask]
    neglogp = -np.log10(np.clip(pv, np.finfo(float).tiny, 1.0))

    order = np.argsort(pv)[: int(max(1, top_n))]
    terms = terms[order]
    cnt = cnt[order]
    neglogp = neglogp[order]
    if ratio is not None:
        rr = np.asarray(ratio, dtype=float)[:n][mask][order]
        x = rr
    else:
        x = cnt

    y = np.arange(len(terms))
    sizes = 40 + 160 * (cnt / (np.max(cnt) + 1e-12))
    fig, ax = self._new_subplots(figsize)
    sc = ax.scatter(x, y, s=sizes, c=neglogp, cmap="viridis", alpha=0.9, edgecolors="none")
    ax.set_yticks(y)
    ax.set_yticklabels(terms)
    ax.invert_yaxis()
    ax.set_xlabel("Gene Ratio" if ratio is not None else "Gene Count")
    ax.set_ylabel("Term")
    if title:
        ax.set_title(title)
    fig.colorbar(sc, ax=ax, label="-log10(p)")
    ax.grid(axis="x", alpha=0.2, linestyle=":")
    return fig, ax

# -----------------------------
# 8) GSEA Running Enrichment（生物）
# -----------------------------

def gsea_running_plot(
    self,
    rank: ArrayLike,
    running_es: ArrayLike,
    hits: Optional[ArrayLike] = None,
    title: Optional[str] = None,
    figsize: Tuple[float, float] = (7.2, 4.6),
) -> Tuple[plt.Figure, plt.Axes]:
    r = np.asarray(rank, dtype=float).ravel()
    es = np.asarray(running_es, dtype=float).ravel()
    n = min(r.size, es.size)
    r, es = r[:n], es[:n]
    mask = np.isfinite(r) & np.isfinite(es)
    r, es = r[mask], es[mask]
    order = np.argsort(r)
    r, es = r[order], es[order]

    fig, ax = self._new_subplots(figsize)
    ax.plot(r, es, color="#2563EB", lw=1.6)
    ax.axhline(0, color="#6B7280", lw=1.0, ls="--")
    if hits is not None:
        h = np.asarray(hits)
        if h.dtype == bool and h.size == n:
            h = h[:n][mask][order]
            hit_pos = r[h]
        else:
            hit_pos = np.asarray(h, dtype=float).ravel()
        for x in hit_pos:
            ax.axvline(x, ymin=0.0, ymax=0.08, color="#111827", lw=0.7, alpha=0.5)

    ax.set_xlabel("Rank")
    ax.set_ylabel("Running ES")
    if title:
        ax.set_title(title)
    ax.grid(alpha=0.25, linestyle=":")
    return fig, ax

# -----------------------------
# 9) Embedding（PCA/UMAP）
# -----------------------------

def embedding_plot(
    self,
    X: ArrayLike,
    labels: Optional[ArrayLike] = None,
    method: str = "pca",
    title: Optional[str] = None,
    figsize: Tuple[float, float] = (6.8, 5.4),
) -> Tuple[plt.Figure, plt.Axes]:
    X = np.asarray(X, dtype=float)
    if X.ndim != 2 or X.shape[1] < 2:
        raise ValueError("X 需为二维矩阵且至少两列特征")
    mask = np.all(np.isfinite(X), axis=1)
    X = X[mask]
    lab = np.asarray(labels)[mask] if labels is not None else None

    method = method.lower()
    if method == "pca":
        Xc = X - np.mean(X, axis=0, keepdims=True)
        _, _, vt = np.linalg.svd(Xc, full_matrices=False)
        Z = Xc @ vt.T[:, :2]
    elif method == "umap":
        try:
            import umap  # type: ignore
        except Exception as e:
            raise RuntimeError(
                format_missing_dependency(
                    package="umap-learn",
                    feature="embedding_plot(method='umap')",
                    recommended_extra="ml",
                )
            ) from e
        reducer = umap.UMAP(n_components=2, random_state=42)
        Z = reducer.fit_transform(X)
    else:
        raise ValueError(f"未知 embedding 方法: {method}")

    fig, ax = self._new_subplots(figsize)
    if lab is None:
        ax.scatter(Z[:, 0], Z[:, 1], s=22, alpha=0.85, color="#2563EB")
    else:
        lab = np.asarray(lab)
        if np.issubdtype(lab.dtype, np.number):
            sc = ax.scatter(Z[:, 0], Z[:, 1], s=22, c=lab, cmap="viridis", alpha=0.85)
            fig.colorbar(sc, ax=ax, label="label")
        else:
            uniq = list(dict.fromkeys(lab.tolist()))
            for u in uniq:
                m = lab == u
                ax.scatter(Z[m, 0], Z[m, 1], s=22, alpha=0.85, label=str(u))
            ax.legend(frameon=False, fontsize=9)
    ax.set_xlabel("Dim 1")
    ax.set_ylabel("Dim 2")
    if title:
        ax.set_title(title)
    ax.grid(alpha=0.2, linestyle=":")
    return fig, ax

# -----------------------------
# 10) UpSet
# -----------------------------

def upset_plot(
    self,
    sets_df,
    top_n: int = 20,
    title: Optional[str] = None,
    figsize: Tuple[float, float] = (7.2, 4.8),
) -> Tuple[plt.Figure, plt.Axes]:
    fig = None
    try:
        from upsetplot import UpSet, from_indicators  # type: ignore
        fig = plt.figure(figsize=figsize)
        data = from_indicators(list(sets_df.columns), sets_df.astype(bool))
        upset = UpSet(data, show_counts=True, sort_by="cardinality")
        upset.plot(fig=fig)
        if title:
            fig.suptitle(title)
        # 部分环境在 savefig 阶段才会触发 upsetplot 渲染异常，这里提前 draw 以便自动回退。
        fig.canvas.draw()
        ax = fig.axes[0] if fig.axes else plt.gca()
        return fig, ax
    except Exception:
        if fig is not None:
            try:
                plt.close(fig)
            except Exception:
                pass
        cols = list(sets_df.columns)
        mat = sets_df.astype(bool).to_numpy()
        labels = []
        for row in mat:
            active = [c for c, v in zip(cols, row) if v]
            labels.append("&".join(active) if active else "None")
        uniq, counts = np.unique(labels, return_counts=True)
        order = np.argsort(counts)[::-1][: int(max(1, top_n))]
        uniq, counts = uniq[order], counts[order]

        fig, ax = self._new_subplots(figsize)
        ax.bar(range(len(uniq)), counts, color="#2563EB")
        ax.set_xticks(range(len(uniq)))
        ax.set_xticklabels(uniq, rotation=45, ha="right")
        ax.set_ylabel("Count")
        if title:
            ax.set_title(title)
        ax.grid(axis="y", alpha=0.2, linestyle=":")
        return fig, ax

# -----------------------------
# 11) Kaplan-Meier（临床）
# -----------------------------

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import numpy as np

from src.dispatch.routes import (
    apply_plot_side_effects,
    is_3d_plot,
    is_extended_plot,
    is_map_plot,
    normalize_mode,
    normalize_plot_name,
)
from src.loaders.data_loader import (
    auto_sep,
    df_from_custom_data,
    load_custom_json,
    parse_csv_list,
    parse_group_arg,
    parse_label_list,
    parse_numeric_list,
    parse_size_range,
    pick_col,
    read_dataframe,
    read_points_from_table,
)
from src.registry import demo_data_path_for_plot, demo_defaults_for_map_plot
from src.save.export import apply_outdir_override, autosave_name, fig_ax_from, resolve_match_screen


class PlotDispatchExecutor:
    def __init__(self, args, static_plotter_cls, map_plotter_cls, plot3d_plotter_cls, project_root: Path) -> None:
        self.args = args
        self.static_plotter_cls = static_plotter_cls
        self.map_plotter_cls = map_plotter_cls
        self.plot3d_plotter_cls = plot3d_plotter_cls
        self.project_root = Path(project_root).resolve()

    def _demo_file_for_plot(self, plot: str) -> Optional[Path]:
        return demo_data_path_for_plot(plot, self.project_root)

    def _apply_demo_map_defaults(self, plot: str) -> None:
        defaults = demo_defaults_for_map_plot(plot, self.project_root)
        if not defaults:
            return

        for key, value in defaults.items():
            if not hasattr(self.args, key):
                continue
            current = getattr(self.args, key)
            if current in (None, ""):
                setattr(self.args, key, value)

    def run_demo_static(self) -> None:
        import matplotlib.pyplot as plt

        rng = np.random.default_rng(int(self.args.seed or 42))
        apply_outdir_override(self.args)
        p = self.static_plotter_cls()

        plot = normalize_plot_name(self.args.plot)
        title = self.args.title
        match_screen = resolve_match_screen(self.args)

        if is_extended_plot(plot):
            demo_file = self._demo_file_for_plot(plot)
            if not demo_file or not demo_file.exists():
                raise FileNotFoundError(f"未找到 demo 数据文件：{demo_file}")
            self.args.file = str(demo_file)
            self.run_file_static()
            return

        if plot in {"box", "violin"}:
            groups = {
                "Ctrl": rng.normal(0, 1, 80),
                "TreatA": rng.normal(0.4, 1.1, 90),
                "TreatB": rng.normal(-0.2, 0.9, 85),
            }
            if plot == "box":
                ret = p.boxplot(groups, title=title or "箱线图演示", ylabel=self.args.ylabel or "Value", xlabel=self.args.xlabel)
            else:
                ret = p.violin_plot(groups, title=title or "小提琴图演示", ylabel=self.args.ylabel or "Value", xlabel=self.args.xlabel)
            fig, _ax = fig_ax_from(ret)
        elif plot == "scatter":
            x = rng.normal(0, 1, 120)
            y = 1.5 * x + 0.6 + rng.normal(0, 0.8, 120)
            ret = p.scatter_with_fit(
                x,
                y,
                title=title or "散点 + 拟合",
                xlabel=self.args.xlabel or "X",
                ylabel=self.args.ylabel or "Y",
                ci=float(self.args.ci or 0.95),
                equal=bool(self.args.equal),
            )
            fig, _ax = fig_ax_from(ret)
        elif plot == "volcano":
            log2fc = rng.normal(0, 1, 400)
            pvals = rng.uniform(0, 1, 400) ** 3
            genes = [f"G{i}" for i in range(400)]
            ret = p.volcano_plot(
                log2fc,
                pvals,
                title=title or "火山图演示",
                fc_thresh=self.args.fc_thresh,
                p_thresh=self.args.p_thresh,
                annotate_top_n=self.args.top_n,
                gene_labels=genes,
                fdr=self.args.fdr,
            )
            fig, _ax = fig_ax_from(ret)
        elif plot == "forest":
            k = 8
            eff = rng.normal(0.1, 0.25, k)
            ci_w = rng.uniform(0.15, 0.45, k)
            lo = eff - ci_w
            hi = eff + ci_w
            labs = [f"Study {i + 1}" for i in range(k)]
            ret = p.forest_plot(
                labs,
                eff,
                lo,
                hi,
                title=title or "森林图演示",
                xlabel=self.args.xlabel or "Effect (95% CI)",
                ref_line=self.args.ref_line,
            )
            fig, _ax = fig_ax_from(ret)
        else:
            raise ValueError(f"未知图类型 / Unknown plot: {self.args.plot}")

        save_name = autosave_name(fig, self.args.save_name, plot, title)
        out = p.save(name=save_name, fig=fig, fmt=self.args.fmt, dpi=self.args.dpi, match_screen=match_screen, tight=self.args.tight)
        print(f"✅ Saved: {out}")
        if not self.args.no_show and os.environ.get("MPLBACKEND", "").lower() != "agg":
            try:
                plt.show()
            except Exception:
                pass
        else:
            try:
                plt.close(fig)
            except Exception:
                pass

    def _run_extended_from_df(self, p, plot: str, df):
        title = self.args.title
        if plot == "ma":
            mean_col = self.args.mean_col or pick_col(df, ["mean", "avg", "A", "base_mean"])
            fc_col = self.args.log2fc_col or pick_col(df, ["log2fc", "log2FC", "M"])
            p_col = self.args.p_col if self.args.p_col and self.args.p_col in df.columns else None
            pvals = df[p_col].values if p_col else None
            return p.ma_plot(
                df[mean_col].values,
                df[fc_col].values,
                pvals=pvals,
                fc_thresh=self.args.fc_thresh,
                p_thresh=self.args.p_thresh,
                title=title or "MA Plot",
                xlabel=self.args.xlabel or mean_col,
                ylabel=self.args.ylabel or "log2FC",
            )
        if plot == "enrich_dot":
            term_col = self.args.term_col or pick_col(df, ["term", "pathway", "description", "name"])
            p_col = self.args.p_col or pick_col(df, ["p", "pval", "pvalue", "p_value"])
            count_col = self.args.count_col or pick_col(df, ["count", "gene_count", "n_genes"])
            ratio_col = self.args.ratio_col if self.args.ratio_col and self.args.ratio_col in df.columns else None
            return p.enrichment_dotplot(
                df[term_col].astype(str).values,
                df[p_col].values,
                df[count_col].values,
                ratio=df[ratio_col].values if ratio_col else None,
                top_n=int(self.args.top_n or 20),
                title=title or "Enrichment Dotplot",
            )
        if plot == "gsea":
            x_col = self.args.x_col or pick_col(df, ["rank", "position", "index"])
            y_col = self.args.y_col or pick_col(df, ["running_es", "es", "enrichment_score"])
            hit_col = self.args.hit_col if self.args.hit_col and self.args.hit_col in df.columns else None
            hits = df[hit_col].values if hit_col else None
            return p.gsea_running_plot(df[x_col].values, df[y_col].values, hits=hits, title=title or "GSEA Running Enrichment")
        if plot == "embedding":
            label_col = self.args.group_col if self.args.group_col in df.columns else None
            if label_col:
                labels = df[label_col].values
                feat_df = df.drop(columns=[label_col])
            else:
                labels = None
                feat_df = df
            numeric = feat_df.select_dtypes(include=["number"])
            if numeric.shape[1] < 2:
                raise ValueError("embedding 需要至少两列数值特征")
            method = (self.args.embed_method or "pca").lower()
            return p.embedding_plot(numeric.values, labels=labels, method=method, title=title or f"Embedding ({method.upper()})")
        if plot == "upset":
            set_cols = parse_csv_list(self.args.set_cols) if self.args.set_cols else None
            if not set_cols:
                bool_cols = [c for c in df.columns if str(df[c].dtype).lower() in {"bool"}]
                if not bool_cols:
                    bool_cols = [c for c in df.columns if set(df[c].dropna().unique()).issubset({0, 1, True, False})]
                if not bool_cols:
                    bool_cols = [c for c in df.columns if set(str(v).strip().lower() for v in df[c].dropna().unique()).issubset({"0", "1", "true", "false"})]
                set_cols = bool_cols
            if not set_cols:
                raise ValueError("UpSet 需要 --set-cols 或布尔列")
            return p.upset_plot(df[set_cols], top_n=int(self.args.top_n or 20), title=title or "UpSet")
        if plot == "km":
            time_col = self.args.time_col or pick_col(df, ["time", "survival_time", "t"])
            event_col = self.args.event_col or pick_col(df, ["event", "status", "censor"])
            group_col = self.args.group_col if self.args.group_col in df.columns else None
            return p.kaplan_meier_plot(
                df[time_col].values,
                df[event_col].values,
                group=df[group_col].values if group_col else None,
                title=title or "Kaplan-Meier",
                risk_table=bool(self.args.risk_table),
            )
        if plot == "roc":
            true_col = self.args.true_col or (self.args.label_col if self.args.label_col in df.columns else None)
            if not true_col:
                true_col = pick_col(df, ["y", "label", "true", "target"])
            score_col = self.args.score_col or self.args.prob_col
            if not score_col or score_col not in df.columns:
                score_col = pick_col(df, ["score", "prob", "pred", "y_score"])
            curve = (self.args.curve or "roc").lower()
            return p.roc_pr_plot(
                df[true_col].values,
                df[score_col].values,
                curve=curve,
                pos_label=self.args.pos_label,
                title=title or ("ROC Curve" if curve == "roc" else "PR Curve"),
            )
        if plot == "calibration":
            true_col = self.args.true_col or (self.args.label_col if self.args.label_col in df.columns else None)
            if not true_col:
                true_col = pick_col(df, ["y", "label", "true", "target"])
            prob_col = self.args.prob_col or pick_col(df, ["prob", "score", "y_prob"])
            return p.calibration_plot(
                df[true_col].values,
                df[prob_col].values,
                n_bins=int(self.args.n_bins or 10),
                strategy=str(self.args.calib_strategy or "uniform"),
                title=title or "Calibration Curve",
            )
        if plot == "bland_altman":
            x_col = self.args.x_col or pick_col(df, ["x", "method1", "a"])
            y_col = self.args.y_col or pick_col(df, ["y", "method2", "b"])
            return p.bland_altman_plot(
                df[x_col].values,
                df[y_col].values,
                title=title or "Bland-Altman",
                xlabel=self.args.xlabel or "Mean",
                ylabel=self.args.ylabel or "Diff",
            )
        if plot == "dca":
            true_col = self.args.true_col or (self.args.label_col if self.args.label_col in df.columns else None)
            if not true_col:
                true_col = pick_col(df, ["y", "label", "true", "target"])
            prob_col = self.args.prob_col or pick_col(df, ["prob", "score", "y_prob"])
            thresholds = parse_numeric_list(self.args.thresholds) if self.args.thresholds else None
            return p.decision_curve_plot(df[true_col].values, df[prob_col].values, thresholds=thresholds, title=title or "Decision Curve")
        if plot == "stress_strain":
            x_col = self.args.x_col or pick_col(df, ["strain", "x"])
            y_col = self.args.y_col or pick_col(df, ["stress", "y"])
            return p.stress_strain_plot(
                df[x_col].values,
                df[y_col].values,
                title=title or "Stress-Strain",
                elastic_max=self.args.elastic_max,
                yield_offset=self.args.yield_offset,
            )
        if plot == "xrd":
            x_col = self.args.x_col or pick_col(df, ["2theta", "two_theta", "theta"])
            y_col = self.args.y_col or pick_col(df, ["intensity", "I", "y"])
            group_col = self.args.group_col if self.args.group_col in df.columns else None
            return p.xrd_plot(
                df[x_col].values,
                df[y_col].values,
                group=df[group_col].values if group_col else None,
                title=title or "XRD Pattern",
                xlabel=self.args.xlabel or x_col,
                ylabel=self.args.ylabel or y_col,
            )
        if plot == "raman":
            x_col = self.args.x_col or pick_col(df, ["shift", "wavenumber", "x"])
            y_col = self.args.y_col or pick_col(df, ["intensity", "y"])
            group_col = self.args.group_col if self.args.group_col in df.columns else None
            return p.raman_plot(
                df[x_col].values,
                df[y_col].values,
                group=df[group_col].values if group_col else None,
                title=title or "Raman/FTIR",
                invert_x=bool(self.args.invert_x),
                xlabel=self.args.xlabel or x_col,
                ylabel=self.args.ylabel or y_col,
            )
        if plot == "phase":
            x_col = self.args.x_col or pick_col(df, ["x", "composition"])
            y_col = self.args.y_col or pick_col(df, ["y", "temperature", "temp"])
            z_col = self.args.z_col if self.args.z_col and self.args.z_col in df.columns else None
            z = df[z_col].values if z_col else None
            return p.phase_plot(
                df[x_col].values,
                df[y_col].values,
                z=z,
                title=title or "Phase Diagram",
                xlabel=self.args.xlabel or x_col,
                ylabel=self.args.ylabel or y_col,
            )
        if plot == "hysteresis":
            x_col = self.args.x_col or pick_col(df, ["field", "voltage", "x"])
            y_col = self.args.y_col or pick_col(df, ["magnetization", "polarization", "y"])
            group_col = self.args.group_col if self.args.group_col in df.columns else None
            return p.hysteresis_plot(df[x_col].values, df[y_col].values, group=df[group_col].values if group_col else None, title=title or "Hysteresis Loop")
        if plot == "spectral_signature":
            x_col = self.args.x_col or pick_col(df, ["wavelength", "wl", "x"])
            y_col = self.args.y_col or pick_col(df, ["reflectance", "value", "y"])
            class_col = self.args.class_col or self.args.group_col
            if not class_col or class_col not in df.columns:
                class_col = None
            return p.spectral_signature_plot(
                df[x_col].values,
                df[y_col].values,
                group=df[class_col].values if class_col else None,
                title=title or "Spectral Signature",
                xlabel=self.args.xlabel or x_col,
                ylabel=self.args.ylabel or y_col,
            )
        if plot == "index_ts":
            time_col = self.args.time_col or pick_col(df, ["date", "time", "t"])
            value_col = self.args.value_col or pick_col(df, ["value", "index", "ndvi", "ndwi"])
            group_col = self.args.group_col if self.args.group_col in df.columns else None
            return p.index_time_series_plot(
                df[time_col].values,
                df[value_col].values,
                group=df[group_col].values if group_col else None,
                title=title or "Index Time Series",
                xlabel=self.args.xlabel or time_col,
                ylabel=self.args.ylabel or value_col,
            )
        if plot == "confusion":
            lower_map = {str(c).lower(): c for c in df.columns}

            def _resolve_col(name: Optional[str]) -> Optional[str]:
                if not name:
                    return None
                if name in df.columns:
                    return name
                return lower_map.get(str(name).lower())

            def _guess_col(candidates: tuple[str, ...]) -> Optional[str]:
                for cand in candidates:
                    hit = _resolve_col(cand)
                    if hit is not None:
                        return hit
                return None

            true_col = _resolve_col(self.args.true_col) or _resolve_col(self.args.label_col) or _guess_col(("true", "label", "y", "target"))
            pred_col = _resolve_col(self.args.pred_col) or _guess_col(("pred", "predict", "prediction", "y_pred"))
            if true_col and pred_col:
                return p.confusion_matrix_plot(df[true_col].values, df[pred_col].values, normalize=self.args.normalize, title=title or "Confusion Matrix")
            if df.shape[0] == df.shape[1]:
                return p.confusion_matrix_plot(df.values, None, labels=list(df.columns), normalize=self.args.normalize, title=title or "Confusion Matrix")
            raise ValueError("confusion 需要 true/pred 列或方阵文件")
        if plot == "class_dist":
            class_col = self.args.class_col or pick_col(df, ["class", "label", "category"])
            value_col = self.args.value_col if self.args.value_col and self.args.value_col in df.columns else None
            group_col = self.args.group_col if self.args.group_col in df.columns else None
            return p.class_distribution_plot(
                df[class_col].values,
                values=df[value_col].values if value_col else None,
                group=df[group_col].values if group_col else None,
                title=title or "Class Distribution",
            )
        if plot == "candlestick":
            date_col = self.args.date_col or pick_col(df, ["date", "time", "datetime"])
            open_col = self.args.open_col or pick_col(df, ["open", "o"])
            high_col = self.args.high_col or pick_col(df, ["high", "h"])
            low_col = self.args.low_col or pick_col(df, ["low", "l"])
            close_col = self.args.close_col or pick_col(df, ["close", "c"])
            volume_col = self.args.volume_col if self.args.volume_col and self.args.volume_col in df.columns else None
            return p.candlestick_plot(
                df[date_col].values,
                df[open_col].values,
                df[high_col].values,
                df[low_col].values,
                df[close_col].values,
                volume=df[volume_col].values if volume_col else None,
                title=title or "Candlestick",
            )
        if plot == "cum_return":
            date_col = self.args.date_col or pick_col(df, ["date", "time", "datetime"])
            ret_col = self.args.return_col if self.args.return_col and self.args.return_col in df.columns else None
            price_col = self.args.price_col if self.args.price_col and self.args.price_col in df.columns else None
            if not ret_col and not price_col:
                ret_col = pick_col(df, ["return", "ret", "r"])
            return p.cum_return_drawdown_plot(
                df[date_col].values,
                returns=df[ret_col].values if ret_col else None,
                price=df[price_col].values if price_col else None,
                title=title or "Cumulative Return & Drawdown",
            )
        if plot == "rolling_stats":
            date_col = self.args.date_col or pick_col(df, ["date", "time", "datetime"])
            ret_col = self.args.return_col if self.args.return_col and self.args.return_col in df.columns else None
            if not ret_col:
                ret_col = pick_col(df, ["return", "ret", "r"])
            return p.rolling_stats_plot(
                df[date_col].values,
                df[ret_col].values,
                window=int(self.args.window or 20),
                risk_free=float(self.args.risk_free or 0.0),
                title=title or "Rolling Volatility & Sharpe",
            )
        if plot == "frontier":
            numeric = df.select_dtypes(include=["number"])
            if numeric.shape[1] < 2:
                raise ValueError("frontier 需要多列资产收益率")
            return p.efficient_frontier_plot(
                numeric.values,
                labels=list(numeric.columns),
                n_portfolios=int(self.args.n_portfolios or 4000),
                title=title or "Efficient Frontier",
            )
        if plot == "acf_pacf":
            value_col = self.args.value_col if self.args.value_col and self.args.value_col in df.columns else None
            if not value_col:
                value_col = self.args.y_col or pick_col(df, ["value", "y", "series"])
            return p.acf_pacf_plot(df[value_col].values, lags=int(self.args.lags or 40), title=title or "ACF/PACF")
        if plot == "likert":
            item_col = self.args.item_col or pick_col(df, ["item", "question"])
            resp_col = self.args.response_col or pick_col(df, ["response", "rating", "score"])
            count_col = self.args.count_col if self.args.count_col and self.args.count_col in df.columns else None
            return p.likert_plot(
                df[item_col].values,
                df[resp_col].values,
                counts=df[count_col].values if count_col else None,
                title=title or "Likert",
            )
        if plot == "raincloud":
            group_col = self.args.group_col or pick_col(df, ["group", "condition", "category"])
            value_col = self.args.value_col or pick_col(df, ["value", "score", "y"])
            return p.raincloud_plot(
                df[group_col].values,
                df[value_col].values,
                title=title or "Raincloud",
                xlabel=self.args.xlabel or group_col,
                ylabel=self.args.ylabel or value_col,
            )
        if plot == "irt_icc":
            item_col = self.args.item_col or pick_col(df, ["item", "question"])
            a_col = self.args.a_col or pick_col(df, ["a", "disc", "discrimination"])
            b_col = self.args.b_col or pick_col(df, ["b", "diff", "difficulty"])
            c_col = self.args.c_col if self.args.c_col and self.args.c_col in df.columns else None
            return p.irt_icc_plot(
                df[item_col].values,
                df[a_col].values,
                df[b_col].values,
                c=df[c_col].values if c_col else None,
                theta_min=float(self.args.theta_min or -4.0),
                theta_max=float(self.args.theta_max or 4.0),
                title=title or "IRT ICC",
            )
        if plot == "factor_loadings":
            factor_col = self.args.factor_col or pick_col(df, ["factor", "component"])
            item_col = self.args.item_col or pick_col(df, ["item", "variable"])
            loading_col = self.args.loading_col or pick_col(df, ["loading", "value"])
            return p.factor_loadings_plot(df[factor_col].values, df[item_col].values, df[loading_col].values, title=title or "Factor Loadings")
        if plot == "interaction":
            x_col = self.args.x_col or pick_col(df, ["x", "factor1", "level"])
            group_col = self.args.group_col or pick_col(df, ["group", "factor2", "condition"])
            value_col = self.args.value_col or pick_col(df, ["value", "y", "score"])
            return p.interaction_plot(
                df[x_col].values,
                df[group_col].values,
                df[value_col].values,
                title=title or "Interaction",
                xlabel=self.args.xlabel or x_col,
                ylabel=self.args.ylabel or value_col,
            )
        raise ValueError(f"未知领域图类型: {plot}")

    def run_custom_static(self) -> None:
        import matplotlib.pyplot as plt

        apply_outdir_override(self.args)
        p = self.static_plotter_cls()
        plot = normalize_plot_name(self.args.plot)
        title = self.args.title
        match_screen = resolve_match_screen(self.args)

        if is_extended_plot(plot):
            data = load_custom_json(self.args)
            if data is None:
                raise ValueError("自定义领域图需要 --custom-json 或 --custom-json-file")
            df = df_from_custom_data(data)
            ret = self._run_extended_from_df(p, plot, df)
            fig, _ax = fig_ax_from(ret)
        elif plot in {"box", "violin"}:
            if not self.args.group:
                raise ValueError("自定义箱线图/小提琴图需要至少一个 --group 'Label: 1,2,3'")
            groups = {}
            for g in self.args.group:
                label, arr = parse_group_arg(g)
                groups[label] = arr
            if plot == "box":
                ret = p.boxplot(groups, title=title or "箱线图", ylabel=self.args.ylabel, xlabel=self.args.xlabel)
            else:
                ret = p.violin_plot(groups, title=title or "小提琴图", ylabel=self.args.ylabel, xlabel=self.args.xlabel)
            fig, _ax = fig_ax_from(ret)
        elif plot == "scatter":
            if not (self.args.x and self.args.y):
                raise ValueError("自定义散点图需要 --x 与 --y")
            x = parse_numeric_list(self.args.x)
            y = parse_numeric_list(self.args.y)
            ret = p.scatter_with_fit(
                x,
                y,
                title=title or "散点图",
                xlabel=self.args.xlabel or "X",
                ylabel=self.args.ylabel or "Y",
                ci=float(self.args.ci or 0.95),
                equal=bool(self.args.equal),
            )
            fig, _ax = fig_ax_from(ret)
        elif plot == "volcano":
            if not (self.args.log2fc and self.args.pvals):
                raise ValueError("自定义火山图需要 --log2fc 与 --pvals")
            x = parse_numeric_list(self.args.log2fc)
            pv = parse_numeric_list(self.args.pvals)
            labels = parse_label_list(self.args.labels) if self.args.labels else None
            ret = p.volcano_plot(
                x,
                pv,
                title=title or "火山图",
                fc_thresh=self.args.fc_thresh,
                p_thresh=self.args.p_thresh,
                annotate_top_n=self.args.top_n,
                gene_labels=labels,
                fdr=self.args.fdr,
            )
            fig, _ax = fig_ax_from(ret)
        elif plot == "forest":
            required = (self.args.forest_labels, self.args.effects, self.args.ci_low, self.args.ci_high)
            if not all(required):
                raise ValueError("自定义森林图需要 --forest-labels --effects --ci-low --ci-high")
            labels = parse_label_list(self.args.forest_labels)
            eff = parse_numeric_list(self.args.effects)
            lo = parse_numeric_list(self.args.ci_low)
            hi = parse_numeric_list(self.args.ci_high)
            w = parse_numeric_list(self.args.weights) if self.args.weights else None
            ret = p.forest_plot(
                labels,
                eff,
                lo,
                hi,
                title=title or "森林图",
                xlabel=self.args.xlabel or "Effect (95% CI)",
                ref_line=self.args.ref_line,
                weights=w,
            )
            fig, _ax = fig_ax_from(ret)
        else:
            raise ValueError(f"未知图类型 / Unknown plot: {self.args.plot}")

        save_name = autosave_name(fig, self.args.save_name, plot, title)
        out = p.save(name=save_name, fig=fig, fmt=self.args.fmt, dpi=self.args.dpi, match_screen=match_screen, tight=self.args.tight)
        print(f"✅ Saved: {out}")
        if not self.args.no_show and os.environ.get("MPLBACKEND", "").lower() != "agg":
            try:
                plt.show()
            except Exception:
                pass
        else:
            try:
                plt.close(fig)
            except Exception:
                pass

    def run_file_static(self) -> None:
        import matplotlib.pyplot as plt

        if not self.args.file:
            raise ValueError("--mode file 需要提供 --file")
        path = Path(self.args.file).expanduser().resolve()
        sep = auto_sep(path, self.args.sep)
        df = read_dataframe(path, sep)

        apply_outdir_override(self.args)
        p = self.static_plotter_cls()
        plot = normalize_plot_name(self.args.plot)
        title = self.args.title
        match_screen = resolve_match_screen(self.args)

        if is_extended_plot(plot):
            ret = self._run_extended_from_df(p, plot, df)
            fig, _ax = fig_ax_from(ret)
        elif plot in {"box", "violin"}:
            if self.args.group_col and self.args.value_col:
                groups = {
                    g: df[df[self.args.group_col] == g][self.args.value_col].dropna().values
                    for g in df[self.args.group_col].dropna().unique()
                }
            else:
                numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
                if not numeric_cols:
                    raise ValueError("未检测到数值列，请提供 --group-col 与 --value-col")
                groups = {col: df[col].dropna().values for col in numeric_cols}
            if plot == "box":
                ret = p.boxplot(groups, title=title or "箱线图", ylabel=self.args.ylabel, xlabel=self.args.xlabel)
            else:
                ret = p.violin_plot(groups, title=title or "小提琴图", ylabel=self.args.ylabel, xlabel=self.args.xlabel)
            fig, _ax = fig_ax_from(ret)
        elif plot == "scatter":
            if not (self.args.x_col and self.args.y_col):
                raise ValueError("文件模式散点图需要 --x-col 与 --y-col")
            ret = p.scatter_with_fit(
                df[self.args.x_col].values,
                df[self.args.y_col].values,
                title=title or "散点图",
                xlabel=self.args.xlabel or self.args.x_col,
                ylabel=self.args.ylabel or self.args.y_col,
                ci=float(self.args.ci or 0.95),
                equal=bool(self.args.equal),
            )
            fig, _ax = fig_ax_from(ret)
        elif plot == "volcano":
            if not (self.args.log2fc_col and self.args.p_col):
                raise ValueError("文件模式火山图需要 --log2fc-col 与 --p-col")
            labels = df[self.args.label_col].astype(str).values if self.args.label_col and self.args.label_col in df.columns else None
            ret = p.volcano_plot(
                df[self.args.log2fc_col].values,
                df[self.args.p_col].values,
                title=title or "火山图",
                fc_thresh=self.args.fc_thresh,
                p_thresh=self.args.p_thresh,
                annotate_top_n=self.args.top_n,
                gene_labels=labels,
                fdr=self.args.fdr,
            )
            fig, _ax = fig_ax_from(ret)
        elif plot == "forest":
            for col in (self.args.forest_label_col, self.args.effect_col, self.args.ci_low_col, self.args.ci_high_col):
                if not col:
                    raise ValueError("文件模式森林图需要 --forest-label-col --effect-col --ci-low-col --ci-high-col")
            weights = df[self.args.weight_col].values if self.args.weight_col and self.args.weight_col in df.columns else None
            ret = p.forest_plot(
                df[self.args.forest_label_col].astype(str).values,
                df[self.args.effect_col].values,
                df[self.args.ci_low_col].values,
                df[self.args.ci_high_col].values,
                title=title or "森林图",
                xlabel=self.args.xlabel or "Effect (95% CI)",
                ref_line=self.args.ref_line,
                weights=weights,
            )
            fig, _ax = fig_ax_from(ret)
        else:
            raise ValueError(f"未知图类型 / Unknown plot: {self.args.plot}")

        save_name = autosave_name(fig, self.args.save_name, plot, title)
        out = p.save(name=save_name, fig=fig, fmt=self.args.fmt, dpi=self.args.dpi, match_screen=match_screen, tight=self.args.tight)
        print(f"✅ Saved: {out}")
        if not self.args.no_show and os.environ.get("MPLBACKEND", "").lower() != "agg":
            try:
                plt.show()
            except Exception:
                pass
        else:
            try:
                plt.close(fig)
            except Exception:
                pass

    def run_3d(self) -> None:
        import matplotlib.pyplot as plt

        if self.plot3d_plotter_cls is None:
            raise ImportError("3D 模块未找到：请确认存在 src/chart/plot_3d/scatter3d.py")

        apply_outdir_override(self.args)
        p = self.plot3d_plotter_cls()
        plot = normalize_plot_name(self.args.plot)
        title = self.args.title
        mode = normalize_mode(self.args.mode)
        match_screen = resolve_match_screen(self.args)

        plot_titles = {
            "plot3d_scatter": "3D Scatter",
            "plot3d_surface": "3D Surface",
            "plot3d_wireframe": "3D Wireframe",
            "plot3d_contour": "3D Contour",
            "plot3d_line": "3D Trajectory",
            "plot3d_isosurface": "3D Isosurface",
            "plot3d_slice": "3D Orthogonal Slices",
            "plot3d_quiver": "3D Vector Field",
            "plot3d_waterfall": "3D Waterfall",
            "plot3d_embedding": "3D Embedding",
            "plot3d_mesh": "3D Mesh",
        }
        if plot not in plot_titles:
            raise ValueError(f"未知 3D 图类型 / Unknown 3D plot: {self.args.plot}")

        if mode not in {"demo", "custom", "file"}:
            raise ValueError(f"未知模式 / Unknown mode: {self.args.mode}")

        z_col_name = self.args.z_col or self.args.z3d_col
        xlabel = self.args.xlabel or (self.args.x_col if mode == "file" and self.args.x_col else "X")
        ylabel = self.args.ylabel or (self.args.y_col if mode == "file" and self.args.y_col else "Y")
        zlabel = self.args.zlabel or (z_col_name if mode == "file" and z_col_name else "Z")
        elev = float(self.args.elev) if self.args.elev is not None else 24.0
        azim = float(self.args.azim) if self.args.azim is not None else 38.0
        cmap = self.args.cmap or "viridis"
        rng = np.random.default_rng(int(self.args.seed or 42))

        def _read_file_df():
            if not self.args.file:
                raise ValueError("--mode file 需要提供 --file")
            path = Path(self.args.file).expanduser().resolve()
            sep = auto_sep(path, self.args.sep)
            return read_dataframe(path, sep)

        ret = None

        if plot == "plot3d_embedding":
            method = (self.args.embed_method or "pca").lower()
            if mode == "demo":
                n = 260
                y_cls = rng.integers(0, 4, size=n)
                X = rng.normal(0, 0.8, size=(n, 6))
                for k in range(4):
                    X[y_cls == k, :3] += np.array([k * 1.6, (k % 2) * 1.4, (-1) ** k * 0.9])
                ret = p.embedding3d(
                    X,
                    labels=y_cls,
                    method=method,
                    title=title or "3D Embedding (Demo)",
                    elev=elev,
                    azim=azim,
                    cmap=cmap,
                )
            else:
                if mode == "custom":
                    data = load_custom_json(self.args)
                    if data is None:
                        raise ValueError("embedding3d 自定义模式需要 --custom-json 或 --custom-json-file")
                    df = df_from_custom_data(data)
                else:
                    df = _read_file_df()
                group_col = self.args.group_col if self.args.group_col and self.args.group_col in df.columns else None
                labels = df[group_col].values if group_col else None
                feat_df = df.drop(columns=[group_col]) if group_col else df
                numeric = feat_df.select_dtypes(include=["number"])
                if numeric.shape[1] < 2:
                    raise ValueError("embedding3d 需要至少两列数值特征")
                ret = p.embedding3d(
                    numeric.values,
                    labels=labels,
                    method=method,
                    title=title or "3D Embedding",
                    elev=elev,
                    azim=azim,
                    cmap=cmap,
                )
        elif plot in {"plot3d_isosurface", "plot3d_slice"}:
            if mode == "demo":
                axis = np.linspace(-2.2, 2.2, 22)
                xg, yg, zg = np.meshgrid(axis, axis, axis, indexing="xy")
                scalar = np.exp(-(xg ** 2 + yg ** 2 + zg ** 2) / 3.0) + 0.28 * np.sin(2.1 * xg) * np.cos(1.8 * yg)
                x = xg.reshape(-1)
                y = yg.reshape(-1)
                z = zg.reshape(-1)
                s = scalar.reshape(-1)
            elif mode == "custom":
                if not (self.args.x and self.args.y and self.args.z and self.args.scalar):
                    raise ValueError("isosurface3d/slice3d 自定义模式需要 --x --y --z --scalar")
                x = parse_numeric_list(self.args.x)
                y = parse_numeric_list(self.args.y)
                z = parse_numeric_list(self.args.z)
                s = parse_numeric_list(self.args.scalar)
            else:
                if not (self.args.x_col and self.args.y_col and z_col_name):
                    raise ValueError("3D 文件模式需要 --x-col --y-col --z-col（或 --z3d-col）")
                df = _read_file_df()
                scalar_col = self.args.scalar_col or self.args.value_col
                if not scalar_col:
                    scalar_col = pick_col(df, ["value", "scalar", "intensity", "val"])
                if scalar_col not in df.columns:
                    raise ValueError(f"未找到标量列：{scalar_col}")
                x = df[self.args.x_col].values
                y = df[self.args.y_col].values
                z = df[z_col_name].values
                s = df[scalar_col].values

            if plot == "plot3d_isosurface":
                ret = p.isosurface3d(
                    x,
                    y,
                    z,
                    s,
                    iso_level=self.args.iso_level,
                    title=title or ("3D Isosurface (Demo)" if mode == "demo" else "3D Isosurface"),
                    xlabel=xlabel,
                    ylabel=ylabel,
                    zlabel=zlabel,
                    elev=elev,
                    azim=azim,
                    cmap=cmap,
                )
            else:
                ret = p.slice3d(
                    x,
                    y,
                    z,
                    s,
                    slice_x=self.args.slice_x,
                    slice_y=self.args.slice_y,
                    slice_z=self.args.slice_z,
                    title=title or ("3D Orthogonal Slices (Demo)" if mode == "demo" else "3D Orthogonal Slices"),
                    xlabel=xlabel,
                    ylabel=ylabel,
                    zlabel=zlabel,
                    elev=elev,
                    azim=azim,
                    cmap=cmap,
                )
        elif plot == "plot3d_quiver":
            if mode == "demo":
                axis = np.linspace(-1.2, 1.2, 9)
                xg, yg, zg = np.meshgrid(axis, axis, axis[::2], indexing="xy")
                x = xg.reshape(-1)
                y = yg.reshape(-1)
                z = zg.reshape(-1)
                u = -y
                v = x
                w = 0.8 * np.sin(np.pi * z)
            elif mode == "custom":
                if not (self.args.x and self.args.y and self.args.z and self.args.u and self.args.v and self.args.w):
                    raise ValueError("quiver3d 自定义模式需要 --x --y --z --u --v --w")
                x = parse_numeric_list(self.args.x)
                y = parse_numeric_list(self.args.y)
                z = parse_numeric_list(self.args.z)
                u = parse_numeric_list(self.args.u)
                v = parse_numeric_list(self.args.v)
                w = parse_numeric_list(self.args.w)
            else:
                if not (self.args.x_col and self.args.y_col and z_col_name):
                    raise ValueError("3D 文件模式需要 --x-col --y-col --z-col（或 --z3d-col）")
                df = _read_file_df()
                u_col = self.args.u_col or pick_col(df, ["u", "ux", "vx", "dx"])
                v_col = self.args.v_col or pick_col(df, ["v", "uy", "vy", "dy"])
                w_col = self.args.w_col or pick_col(df, ["w", "uz", "vz", "dz"])
                x = df[self.args.x_col].values
                y = df[self.args.y_col].values
                z = df[z_col_name].values
                u = df[u_col].values
                v = df[v_col].values
                w = df[w_col].values
            ret = p.quiver3d(
                x,
                y,
                z,
                u,
                v,
                w,
                title=title or ("3D Vector Field (Demo)" if mode == "demo" else "3D Vector Field"),
                xlabel=xlabel,
                ylabel=ylabel,
                zlabel=zlabel,
                elev=elev,
                azim=azim,
                cmap=cmap,
                max_arrows=max(int(self.args.max_arrows or 600), 50),
            )
        else:
            if mode == "demo":
                if plot == "plot3d_scatter":
                    x = rng.normal(0.0, 1.0, 160)
                    y = 0.9 * x + rng.normal(0.0, 0.55, 160)
                    z = 1.2 * x - 0.4 * y + rng.normal(0.0, 0.35, 160)
                elif plot == "plot3d_line":
                    t = np.linspace(0.0, 10.0 * np.pi, 420)
                    x = np.cos(t)
                    y = np.sin(t)
                    z = t / (2.0 * np.pi)
                elif plot == "plot3d_waterfall":
                    x_base = np.linspace(0.0, 10.0, 180)
                    curves = 8
                    xs, ys, zs = [], [], []
                    for i in range(curves):
                        y0 = float(i)
                        z0 = np.sin(x_base * (0.9 + 0.08 * i)) * np.exp(-x_base / (10.0 + i)) + 0.12 * i
                        xs.append(x_base)
                        ys.append(np.full_like(x_base, y0))
                        zs.append(z0)
                    x = np.concatenate(xs)
                    y = np.concatenate(ys)
                    z = np.concatenate(zs)
                elif plot == "plot3d_mesh":
                    x = rng.uniform(-3.0, 3.0, 1300)
                    y = rng.uniform(-3.0, 3.0, 1300)
                    r = np.sqrt(x ** 2 + y ** 2) + 1e-9
                    z = np.sin(r) / r + 0.06 * rng.normal(size=r.size)
                else:
                    gx = np.linspace(-3.2, 3.2, 70)
                    gy = np.linspace(-3.2, 3.2, 70)
                    xg, yg = np.meshgrid(gx, gy)
                    r = np.sqrt(xg ** 2 + yg ** 2) + 1e-9
                    zg = np.sin(r) / r
                    x = xg.reshape(-1)
                    y = yg.reshape(-1)
                    z = zg.reshape(-1)
            elif mode == "custom":
                if not (self.args.x and self.args.y and self.args.z):
                    raise ValueError("3D 自定义模式需要 --x --y --z")
                x = parse_numeric_list(self.args.x)
                y = parse_numeric_list(self.args.y)
                z = parse_numeric_list(self.args.z)
            else:
                if not (self.args.x_col and self.args.y_col and z_col_name):
                    raise ValueError("3D 文件模式需要 --x-col --y-col --z-col（或 --z3d-col）")
                df = _read_file_df()
                x = df[self.args.x_col].values
                y = df[self.args.y_col].values
                z = df[z_col_name].values

            if plot == "plot3d_scatter":
                ret = p.scatter3d(
                    x,
                    y,
                    z,
                    title=title or ("3D Scatter (Demo)" if mode == "demo" else "3D Scatter"),
                    xlabel=xlabel,
                    ylabel=ylabel,
                    zlabel=zlabel,
                    elev=elev,
                    azim=azim,
                    cmap=cmap,
                )
            elif plot == "plot3d_surface":
                ret = p.surface3d(
                    x,
                    y,
                    z,
                    title=title or ("3D Surface (Demo)" if mode == "demo" else "3D Surface"),
                    xlabel=xlabel,
                    ylabel=ylabel,
                    zlabel=zlabel,
                    elev=elev,
                    azim=azim,
                    cmap=cmap,
                )
            elif plot == "plot3d_wireframe":
                ret = p.wireframe3d(
                    x,
                    y,
                    z,
                    title=title or ("3D Wireframe (Demo)" if mode == "demo" else "3D Wireframe"),
                    xlabel=xlabel,
                    ylabel=ylabel,
                    zlabel=zlabel,
                    elev=elev,
                    azim=azim,
                    rstride=max(int(self.args.rstride or 2), 1),
                    cstride=max(int(self.args.cstride or 2), 1),
                )
            elif plot == "plot3d_contour":
                contour_elev = float(self.args.elev) if self.args.elev is not None else 30.0
                contour_azim = float(self.args.azim) if self.args.azim is not None else 42.0
                ret = p.contour3d(
                    x,
                    y,
                    z,
                    title=title or ("3D Contour (Demo)" if mode == "demo" else "3D Contour"),
                    xlabel=xlabel,
                    ylabel=ylabel,
                    zlabel=zlabel,
                    elev=contour_elev,
                    azim=contour_azim,
                    cmap=cmap,
                    levels=max(int(self.args.levels or 18), 3),
                )
            elif plot == "plot3d_line":
                ret = p.line3d(
                    x,
                    y,
                    z,
                    title=title or ("3D Trajectory (Demo)" if mode == "demo" else "3D Trajectory"),
                    xlabel=xlabel,
                    ylabel=ylabel,
                    zlabel=zlabel,
                    elev=elev,
                    azim=azim,
                )
            elif plot == "plot3d_waterfall":
                ret = p.waterfall3d(
                    x,
                    y,
                    z,
                    title=title or ("3D Waterfall (Demo)" if mode == "demo" else "3D Waterfall"),
                    xlabel=xlabel,
                    ylabel=ylabel,
                    zlabel=zlabel,
                    elev=elev,
                    azim=float(self.args.azim) if self.args.azim is not None else -62.0,
                    cmap=cmap,
                )
            else:
                values = None
                if mode == "custom" and self.args.scalar:
                    values = parse_numeric_list(self.args.scalar)
                elif mode == "file":
                    scalar_col = self.args.scalar_col or self.args.value_col
                    if scalar_col and scalar_col in df.columns:
                        values = df[scalar_col].values
                ret = p.mesh3d(
                    x,
                    y,
                    z,
                    values=values,
                    title=title or ("3D Mesh (Demo)" if mode == "demo" else "3D Mesh"),
                    xlabel=xlabel,
                    ylabel=ylabel,
                    zlabel=zlabel,
                    elev=elev,
                    azim=azim,
                    cmap=cmap,
                )

        if ret is None:
            raise RuntimeError(f"3D 分发失败：{plot}")

        fig, _ax = fig_ax_from(ret)
        save_name = autosave_name(fig, self.args.save_name, plot, title)
        out = p.save(name=save_name, fig=fig, fmt=self.args.fmt, dpi=self.args.dpi, match_screen=match_screen, tight=self.args.tight)
        print(f"✅ Saved: {out}")
        if not self.args.no_show and os.environ.get("MPLBACKEND", "").lower() != "agg":
            try:
                plt.show()
            except Exception:
                pass
        else:
            try:
                plt.close(fig)
            except Exception:
                pass

    def run_map(self) -> None:
        import matplotlib.pyplot as plt

        if self.map_plotter_cls is None:
            raise ImportError("地图模块未找到：请确认存在 src/chart/plot_2d/geo_atlas.py（或 cartography/geo_thematic/domain_analysis）")

        plot = normalize_plot_name(self.args.plot)
        mode = normalize_mode(self.args.mode)
        if mode == "demo":
            self._apply_demo_map_defaults(plot)
        title = self.args.title
        match_screen = resolve_match_screen(self.args)

        kwargs = {
            "theme": self.args.map_theme,
            "include_taiwan": bool(getattr(self.args, "include_taiwan", True)),
            "include_hk_mo": bool(getattr(self.args, "include_hk_mo", True)),
        }
        if self.args.basemap_root:
            kwargs["basemap_root"] = Path(self.args.basemap_root)
        if getattr(self.args, "taiwan_name", None):
            kwargs["taiwan_name"] = self.args.taiwan_name

        apply_outdir_override(self.args)
        p = self.map_plotter_cls(**kwargs)

        if plot == "map_world":
            fig, ax, _ = p.plot_world_admin0(
                title=title or "World Countries",
                crs=self.args.crs,
                highlight_countries=parse_csv_list(self.args.highlight),
                label=self.args.label_names,
            )
            if hasattr(p, "add_north_arrow"):
                p.add_north_arrow(ax)
            if hasattr(p, "add_scalebar"):
                p.add_scalebar(ax)
        elif plot == "map_world_admin1":
            fig, ax, _ = p.plot_world_admin1(
                countries=parse_csv_list(self.args.countries),
                title=title or "World Admin1",
                crs=self.args.crs,
                label=self.args.label_names,
                country_field=self.args.country_field,
                case_insensitive=not self.args.case_sensitive,
            )
            if hasattr(p, "add_north_arrow"):
                p.add_north_arrow(ax)
            if hasattr(p, "add_scalebar"):
                p.add_scalebar(ax)
        elif plot == "map_china":
            fig, ax, _ = p.plot_china(
                level=int(self.args.level or 1),
                title=title or f"China L{int(self.args.level or 1)}",
                crs=self.args.crs,
                highlight_names=parse_csv_list(self.args.highlight),
                label=self.args.label_names,
            )
            if hasattr(p, "add_north_arrow"):
                p.add_north_arrow(ax)
            if hasattr(p, "add_scalebar"):
                p.add_scalebar(ax)
        elif plot == "map_choropleth_world":
            if not self.args.file:
                raise ValueError("choropleth_world 需要 --file 指向含数据的 CSV/TSV/Excel")
            path = Path(self.args.file).expanduser().resolve()
            df = read_dataframe(path, auto_sep(path, self.args.sep))
            key_col = self.args.key_col or "ISO_A3"
            value_col = self.args.value_col or "value"
            on = (self.args.on or "iso_a3").lower()
            cmap = self.args.cmap or self.args.map_theme
            fig, ax, _ = p.choropleth_world(
                df,
                key_col=key_col,
                value_col=value_col,
                on="name" if on == "name" else "iso_a3",
                scheme=self.args.scheme,
                k=int(self.args.k or 5),
                cmap=cmap,
                title=title or "World Choropleth",
                crs=self.args.crs,
                label_top_n=int(self.args.label_top_n or 0),
            )
            if hasattr(p, "add_north_arrow"):
                p.add_north_arrow(ax)
            if hasattr(p, "add_scalebar"):
                p.add_scalebar(ax)
        elif plot == "map_choropleth_china":
            if not self.args.file:
                raise ValueError("choropleth_china 需要 --file 指向含数据的 CSV/TSV/Excel")
            path = Path(self.args.file).expanduser().resolve()
            df = read_dataframe(path, auto_sep(path, self.args.sep))
            key_col = self.args.key_col or (f"NAME_{int(self.args.level or 1)}")
            value_col = self.args.value_col or "value"
            on = (self.args.on or "NAME").upper()
            cmap = self.args.cmap or "Reds"
            fig, ax, _ = p.choropleth_china(
                df,
                key_col=key_col,
                value_col=value_col,
                level=int(self.args.level or 1),
                on="GID" if on == "GID" else "NAME",
                scheme=self.args.scheme,
                k=int(self.args.k or 5),
                cmap=cmap,
                title=title or "China Choropleth",
                crs=self.args.crs,
                label_top_n=int(self.args.label_top_n or 0),
            )
            if hasattr(p, "add_north_arrow"):
                p.add_north_arrow(ax)
            if hasattr(p, "add_scalebar"):
                p.add_scalebar(ax)
        elif plot == "map_raster":
            raster_path = self.args.raster_file or ""
            if not raster_path:
                raise ValueError("raster 模式需要提供 --raster-file")
            fig, ax = p.raster_on_map(
                raster_path=raster_path,
                title=title or "Raster Overlay",
                alpha=float(self.args.alpha or 0.65),
                basemap=self.args.basemap,
            )
            if hasattr(p, "add_north_arrow"):
                p.add_north_arrow(ax)
            if hasattr(p, "add_scalebar"):
                p.add_scalebar(ax)
        elif plot == "map_points":
            base = (self.args.basemap or "world_admin0").lower()
            if base == "china_l1":
                fig, ax, _ = p.plot_china(level=1, title=title or "Points on China", crs=self.args.crs)
            elif base == "none":
                fig = plt.figure(figsize=(9.5, 5.8))
                ax = plt.gca()
                ax.set_axis_off()
            else:
                fig, ax, _ = p.plot_world_admin0(title=title or "Points on World", crs=self.args.crs)

            if not self.args.file:
                raise ValueError("points 模式需要 --file（CSV/TSV/Excel/GeoJSON/GPKG/SHP）与 --lon-col/--lat-col（表格）")
            data_path = Path(self.args.file).expanduser().resolve()
            if data_path.suffix.lower() in {".csv", ".tsv", ".txt", ".xlsx", ".xls"}:
                if not (self.args.lon_col and self.args.lat_col):
                    raise ValueError("表格叠加请提供 --lon-col 与 --lat-col")
                gpts = read_points_from_table(data_path, self.args.lon_col, self.args.lat_col)
            else:
                import geopandas as gpd

                gpts = gpd.read_file(data_path)
                if gpts.crs is None:
                    gpts.set_crs("EPSG:4326", inplace=True)

            p.overlay_points(
                ax,
                gpts,
                size_col=self.args.size_col,
                size_range=parse_size_range(self.args.size_range),
                hue_col=self.args.hue_col,
                label_col=self.args.label_col,
                legend=True,
            )
            if hasattr(p, "add_north_arrow"):
                p.add_north_arrow(ax)
            if hasattr(p, "add_scalebar"):
                p.add_scalebar(ax)
        else:
            raise ValueError(f"未知地图类型 / Unknown map plot: {self.args.plot}")

        save_name = autosave_name(plt.gcf(), self.args.save_name, plot, title)
        out = p.save(name=save_name, fig=plt.gcf(), fmt=self.args.fmt, dpi=self.args.dpi, match_screen=match_screen, tight=self.args.tight)
        print(f"✅ Saved: {out}")
        if not self.args.no_show and os.environ.get("MPLBACKEND", "").lower() != "agg":
            try:
                plt.show()
            except Exception:
                pass
        else:
            try:
                plt.close(plt.gcf())
            except Exception:
                pass

    def run(self) -> None:
        apply_plot_side_effects(self.args)
        plot_key = normalize_plot_name(self.args.plot)
        mode = normalize_mode(self.args.mode)

        if os.environ.get("CI") or os.environ.get("HEADLESS"):
            import matplotlib

            self.args.no_show = True
            backend = matplotlib.get_backend().lower()
            if "agg" not in backend:
                try:
                    matplotlib.use("Agg")
                except Exception:
                    pass

        if is_map_plot(plot_key):
            self.run_map()
            return

        if is_3d_plot(plot_key):
            self.run_3d()
            return

        if mode == "demo":
            self.run_demo_static()
        elif mode == "custom":
            self.run_custom_static()
        elif mode == "file":
            self.run_file_static()
        else:
            raise ValueError(f"未知模式 / Unknown mode: {self.args.mode}")

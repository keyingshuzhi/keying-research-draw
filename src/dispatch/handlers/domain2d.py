from __future__ import annotations

from pathlib import Path
from typing import Optional

from src.dispatch.handlers.base import HandlerContext, HandlerResult
from src.dispatch.handlers.helpers import demo_file_for_plot
from src.loaders.data_loader import (
    auto_sep,
    df_from_custom_data,
    load_custom_json,
    parse_csv_list,
    parse_numeric_list,
    pick_col,
    read_dataframe,
)


class Domain2DHandler:
    key = "domain2d"

    def __init__(self, ctx: HandlerContext) -> None:
        self.ctx = ctx
        self.args = ctx.args

    def render(self, plot_key: str, mode: str) -> HandlerResult:
        if self.ctx.static_plotter_cls is None:
            raise ImportError("二维领域绘图模块未找到。")

        plotter = self.ctx.static_plotter_cls()
        df = self._load_df_for_mode(mode, plot_key)
        rendered = self._render_from_df(plotter, plot_key, df)
        return HandlerResult(plotter=plotter, rendered=rendered, plot_key=plot_key, title=self.args.title)

    def _load_df_for_mode(self, mode: str, plot_key: str):
        if mode == "custom":
            data = load_custom_json(self.args)
            if data is None:
                raise ValueError("自定义领域图需要 --custom-json 或 --custom-json-file")
            return df_from_custom_data(data)

        if mode == "demo":
            demo_file = demo_file_for_plot(plot_key, self.ctx.project_root)
            if not demo_file or not demo_file.exists():
                raise FileNotFoundError(f"未找到 demo 数据文件：{demo_file}")
            self.args.file = str(demo_file)

        if not self.args.file:
            raise ValueError("--mode file 需要提供 --file")
        path = Path(self.args.file).expanduser().resolve()
        sep = auto_sep(path, self.args.sep)
        return read_dataframe(path, sep)

    def _render_from_df(self, p, plot: str, df):
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

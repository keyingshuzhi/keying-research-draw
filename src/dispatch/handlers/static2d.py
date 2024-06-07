from __future__ import annotations

from pathlib import Path

import numpy as np

from src.dispatch.handlers.base import HandlerContext, HandlerResult
from src.loaders.data_loader import (
    parse_group_arg,
    parse_label_list,
    parse_numeric_list,
    read_dataframe,
    auto_sep,
)


class Static2DHandler:
    key = "static2d"

    def __init__(self, ctx: HandlerContext) -> None:
        self.ctx = ctx
        self.args = ctx.args

    def render(self, plot_key: str, mode: str) -> HandlerResult:
        if self.ctx.static_plotter_cls is None:
            raise ImportError("二维统计绘图模块未找到。")

        plotter = self.ctx.static_plotter_cls()
        if mode == "demo":
            rendered = self._render_demo(plotter, plot_key)
        elif mode == "custom":
            rendered = self._render_custom(plotter, plot_key)
        elif mode == "file":
            rendered = self._render_file(plotter, plot_key)
        else:
            raise ValueError(f"未知模式 / Unknown mode: {self.args.mode}")
        return HandlerResult(plotter=plotter, rendered=rendered, plot_key=plot_key, title=self.args.title)

    def _render_demo(self, plotter, plot_key: str):
        rng = np.random.default_rng(int(self.args.seed or 42))
        title = self.args.title
        if plot_key in {"box", "violin"}:
            groups = {
                "Ctrl": rng.normal(0, 1, 80),
                "TreatA": rng.normal(0.4, 1.1, 90),
                "TreatB": rng.normal(-0.2, 0.9, 85),
            }
            if plot_key == "box":
                return plotter.boxplot(groups, title=title or "箱线图演示", ylabel=self.args.ylabel or "Value", xlabel=self.args.xlabel)
            return plotter.violin_plot(groups, title=title or "小提琴图演示", ylabel=self.args.ylabel or "Value", xlabel=self.args.xlabel)

        if plot_key == "scatter":
            x = rng.normal(0, 1, 120)
            y = 1.5 * x + 0.6 + rng.normal(0, 0.8, 120)
            return plotter.scatter_with_fit(
                x,
                y,
                title=title or "散点 + 拟合",
                xlabel=self.args.xlabel or "X",
                ylabel=self.args.ylabel or "Y",
                ci=float(self.args.ci or 0.95),
                equal=bool(self.args.equal),
            )

        if plot_key == "volcano":
            log2fc = rng.normal(0, 1, 400)
            pvals = rng.uniform(0, 1, 400) ** 3
            genes = [f"G{i}" for i in range(400)]
            return plotter.volcano_plot(
                log2fc,
                pvals,
                title=title or "火山图演示",
                fc_thresh=self.args.fc_thresh,
                p_thresh=self.args.p_thresh,
                annotate_top_n=self.args.top_n,
                gene_labels=genes,
                fdr=self.args.fdr,
            )

        if plot_key == "forest":
            k = 8
            eff = rng.normal(0.1, 0.25, k)
            ci_w = rng.uniform(0.15, 0.45, k)
            lo = eff - ci_w
            hi = eff + ci_w
            labs = [f"Study {i + 1}" for i in range(k)]
            return plotter.forest_plot(
                labs,
                eff,
                lo,
                hi,
                title=title or "森林图演示",
                xlabel=self.args.xlabel or "Effect (95% CI)",
                ref_line=self.args.ref_line,
            )
        raise ValueError(f"未知图类型 / Unknown plot: {self.args.plot}")

    def _render_custom(self, plotter, plot_key: str):
        title = self.args.title
        if plot_key in {"box", "violin"}:
            if not self.args.group:
                raise ValueError("自定义箱线图/小提琴图需要至少一个 --group 'Label: 1,2,3'")
            groups = {}
            for g in self.args.group:
                label, arr = parse_group_arg(g)
                groups[label] = arr
            if plot_key == "box":
                return plotter.boxplot(groups, title=title or "箱线图", ylabel=self.args.ylabel, xlabel=self.args.xlabel)
            return plotter.violin_plot(groups, title=title or "小提琴图", ylabel=self.args.ylabel, xlabel=self.args.xlabel)

        if plot_key == "scatter":
            if not (self.args.x and self.args.y):
                raise ValueError("自定义散点图需要 --x 与 --y")
            x = parse_numeric_list(self.args.x)
            y = parse_numeric_list(self.args.y)
            return plotter.scatter_with_fit(
                x,
                y,
                title=title or "散点图",
                xlabel=self.args.xlabel or "X",
                ylabel=self.args.ylabel or "Y",
                ci=float(self.args.ci or 0.95),
                equal=bool(self.args.equal),
            )

        if plot_key == "volcano":
            if not (self.args.log2fc and self.args.pvals):
                raise ValueError("自定义火山图需要 --log2fc 与 --pvals")
            x = parse_numeric_list(self.args.log2fc)
            pv = parse_numeric_list(self.args.pvals)
            labels = parse_label_list(self.args.labels) if self.args.labels else None
            return plotter.volcano_plot(
                x,
                pv,
                title=title or "火山图",
                fc_thresh=self.args.fc_thresh,
                p_thresh=self.args.p_thresh,
                annotate_top_n=self.args.top_n,
                gene_labels=labels,
                fdr=self.args.fdr,
            )

        if plot_key == "forest":
            required = (self.args.forest_labels, self.args.effects, self.args.ci_low, self.args.ci_high)
            if not all(required):
                raise ValueError("自定义森林图需要 --forest-labels --effects --ci-low --ci-high")
            labels = parse_label_list(self.args.forest_labels)
            eff = parse_numeric_list(self.args.effects)
            lo = parse_numeric_list(self.args.ci_low)
            hi = parse_numeric_list(self.args.ci_high)
            w = parse_numeric_list(self.args.weights) if self.args.weights else None
            return plotter.forest_plot(
                labels,
                eff,
                lo,
                hi,
                title=title or "森林图",
                xlabel=self.args.xlabel or "Effect (95% CI)",
                ref_line=self.args.ref_line,
                weights=w,
            )
        raise ValueError(f"未知图类型 / Unknown plot: {self.args.plot}")

    def _render_file(self, plotter, plot_key: str):
        if not self.args.file:
            raise ValueError("--mode file 需要提供 --file")
        path = Path(self.args.file).expanduser().resolve()
        sep = auto_sep(path, self.args.sep)
        df = read_dataframe(path, sep)
        title = self.args.title

        if plot_key in {"box", "violin"}:
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
            if plot_key == "box":
                return plotter.boxplot(groups, title=title or "箱线图", ylabel=self.args.ylabel, xlabel=self.args.xlabel)
            return plotter.violin_plot(groups, title=title or "小提琴图", ylabel=self.args.ylabel, xlabel=self.args.xlabel)

        if plot_key == "scatter":
            if not (self.args.x_col and self.args.y_col):
                raise ValueError("文件模式散点图需要 --x-col 与 --y-col")
            return plotter.scatter_with_fit(
                df[self.args.x_col].values,
                df[self.args.y_col].values,
                title=title or "散点图",
                xlabel=self.args.xlabel or self.args.x_col,
                ylabel=self.args.ylabel or self.args.y_col,
                ci=float(self.args.ci or 0.95),
                equal=bool(self.args.equal),
            )

        if plot_key == "volcano":
            if not (self.args.log2fc_col and self.args.p_col):
                raise ValueError("文件模式火山图需要 --log2fc-col 与 --p-col")
            labels = df[self.args.label_col].astype(str).values if self.args.label_col and self.args.label_col in df.columns else None
            return plotter.volcano_plot(
                df[self.args.log2fc_col].values,
                df[self.args.p_col].values,
                title=title or "火山图",
                fc_thresh=self.args.fc_thresh,
                p_thresh=self.args.p_thresh,
                annotate_top_n=self.args.top_n,
                gene_labels=labels,
                fdr=self.args.fdr,
            )

        if plot_key == "forest":
            for col in (self.args.forest_label_col, self.args.effect_col, self.args.ci_low_col, self.args.ci_high_col):
                if not col:
                    raise ValueError("文件模式森林图需要 --forest-label-col --effect-col --ci-low-col --ci-high-col")
            weights = df[self.args.weight_col].values if self.args.weight_col and self.args.weight_col in df.columns else None
            return plotter.forest_plot(
                df[self.args.forest_label_col].astype(str).values,
                df[self.args.effect_col].values,
                df[self.args.ci_low_col].values,
                df[self.args.ci_high_col].values,
                title=title or "森林图",
                xlabel=self.args.xlabel or "Effect (95% CI)",
                ref_line=self.args.ref_line,
                weights=weights,
            )
        raise ValueError(f"未知图类型 / Unknown plot: {self.args.plot}")

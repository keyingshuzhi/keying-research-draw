# -*- coding: utf-8 -*-
# scripts/smoke_statics_cn.py
from __future__ import annotations

import os
from pathlib import Path
from typing import List, Sequence, Optional

import pandas as pd

from src.main import ResearchDrawApp

# ---------- 路径 ----------
THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parent.parent.resolve()
DATA_DIR = (PROJECT_ROOT / "data").resolve()
OUT_DIR = (PROJECT_ROOT / "outputs" / "figures").resolve()

try:
    os.chdir(PROJECT_ROOT)
    print(f"[cwd] {Path.cwd()}")
except Exception as e:
    print(f"[WARN] chdir failed: {e}")

OUT_DIR.mkdir(parents=True, exist_ok=True)

# 中文 / “weird” 列名数据
LONG_BOX_ZH = DATA_DIR / "long_box_zh.csv"
LONG_BOX_WEIRD = DATA_DIR / "long_box_weird.csv"
SCATTER_ZH = DATA_DIR / "scatter_zh.csv"
SCATTER_WEIRD = DATA_DIR / "scatter_weird.csv"
VOLCANO_ZH = DATA_DIR / "volcano_zh.csv"
VOLCANO_EDGE = DATA_DIR / "volcano_edge.tsv"
FOREST_ZH = DATA_DIR / "forest_zh.csv"

FMT = "png"
NO_SHOW = True


# ---------- 工具 ----------
def _run(argv_list: List[str]) -> None:
    args = [str(a) for a in argv_list if a]
    print(">>> running:", " ".join(args))
    ResearchDrawApp(args).run()


def _expect_saved(name: str, fmt: str = FMT):
    candidates = [
        PROJECT_ROOT / "outputs" / "figures" / f"{name}.{fmt}",
        Path.cwd() / "outputs" / "figures" / f"{name}.{fmt}",
        THIS_FILE.parent / "outputs" / "figures" / f"{name}.{fmt}",
    ]
    for p in candidates:
        if p.exists():
            print(f"[OK] saved -> {p}")
            return
    raise AssertionError("Expected output not found: " + " | ".join(map(str, candidates)))


def _pick_col_exact(df: pd.DataFrame, candidates: Sequence[str]) -> Optional[str]:
    """大小写不敏感的精确匹配；命中则返回列名，否则 None。"""
    cols = list(df.columns)
    lower = {c.lower(): c for c in cols}
    for k in candidates:
        if k in cols:
            return k
        lk = k.lower()
        if lk in lower:
            return lower[lk]
    return None


def _pick_col_contains(df: pd.DataFrame, tokens: Sequence[str]) -> Optional[str]:
    """大小写不敏感的子串匹配；用于别名较多的情形。"""
    cols = list(df.columns)
    lower_cols = [(c, c.lower()) for c in cols]
    lower_tokens = [t.lower() for t in tokens]
    for c, lc in lower_cols:
        for t in lower_tokens:
            if t in lc:
                return c
    return None


def _pick_col(df: pd.DataFrame, candidates: Sequence[str], contains_tokens: Optional[Sequence[str]] = None) -> str:
    """先精确匹配，再子串兜底；仍找不到就报错。"""
    hit = _pick_col_exact(df, candidates)
    if hit is not None:
        return hit
    if contains_tokens:
        hit = _pick_col_contains(df, contains_tokens)
        if hit is not None:
            return hit
    raise KeyError(f"None of {candidates} in columns: {list(df.columns)[:10]}...")


def _pick_p_col(df: pd.DataFrame) -> str:
    """
    兼容中英文 p 值列名：
    - 英文：p, pval, p_value, pvalue, padj, adj.P, qvalue, fdr ...
    - 中文：p值, P值, 显著性, q值 ...
    """
    exact_candidates = [
        "p", "P", "pval", "p_value", "pvalue", "padj", "adj.P",
        "qvalue", "q_value", "qval", "fdr",
        "p值", "P值", "显著性", "q值",
    ]
    contains_tokens = [
        "p值", "P值", "显著",  # 中文
        "pval", "p_value", "pvalue", "padj", "adjp", "adj.p",
        "qvalue", "q_value", "qval", "fdr",
    ]
    return _pick_col(df, exact_candidates, contains_tokens=contains_tokens)


def _pick_gene_label_col(df: pd.DataFrame) -> str:
    """火山图标签列（中文/英文）。"""
    exact = ["label", "gene", "symbol", "name", "Gene", "基因", "名称"]
    contains = ["gene", "symbol", "name", "基因", "名称"]
    return _pick_col(df, exact, contains_tokens=contains)


def _pick_ci_low_col(df: pd.DataFrame) -> str:
    """CI 下界列名（中英文常见别名：CI下/下限/下界/低限 等）。"""
    exact = [
        "ci_low", "ci.low", "ci_l", "lcl", "lower", "lo",
        "CI下", "ci下", "下限", "下界", "下边界", "低限", "下误差",
        "CI_low", "CI.L", "CI_lower",
    ]
    contains = [
        "ci_low", "lcl", "lower",
        "CI下", "ci下", "下限", "下界", "低限",
    ]
    return _pick_col(df, exact, contains_tokens=contains)


def _pick_ci_high_col(df: pd.DataFrame) -> str:
    """CI 上界列名（中英文常见别名：CI上/上限/上界/高限 等）。"""
    exact = [
        "ci_high", "ci.high", "ci_h", "ucl", "upper", "hi",
        "CI上", "ci上", "上限", "上界", "上边界", "高限", "上误差",
        "CI_high", "CI.U", "CI_upper",
    ]
    contains = [
        "ci_high", "ucl", "upper",
        "CI上", "ci上", "上限", "上界", "高限",
    ]
    return _pick_col(df, exact, contains_tokens=contains)


# ---------- 测试用例 ----------
def test_box_long_zh():
    assert LONG_BOX_ZH.exists(), f"Missing {LONG_BOX_ZH}"
    df = pd.read_csv(LONG_BOX_ZH)
    group_col = _pick_col(df, ["group", "grp", "分组", "组"])
    value_col = _pick_col(df, ["value", "val", "数值", "值", "y"])
    save = "t_cn_box_long_zh"
    _run([
        "--plot", "box", "--mode", "file",
        "--file", str(LONG_BOX_ZH),
        "--group-col", group_col, "--value-col", value_col,
        "--title", "箱线图（中文长表）",
        "--save-name", save, "--fmt", FMT, "--tight",
        "--no-show" if NO_SHOW else None,
    ])
    _expect_saved(save)


def test_box_long_weird():
    assert LONG_BOX_WEIRD.exists(), f"Missing {LONG_BOX_WEIRD}"
    df = pd.read_csv(LONG_BOX_WEIRD)
    group_col = _pick_col(df, ["group", "grp", "分组", "组", "类别", "class"])
    value_col = _pick_col(df, ["value", "val", "数值", "值", "y", "resp"])
    save = "t_cn_box_long_weird"
    _run([
        "--plot", "box", "--mode", "file",
        "--file", str(LONG_BOX_WEIRD),
        "--group-col", group_col, "--value-col", value_col,
        "--title", "箱线图（混合列名）",
        "--save-name", save, "--fmt", FMT, "--tight",
        "--no-show" if NO_SHOW else None,
    ])
    _expect_saved(save)


def test_scatter_zh():
    assert SCATTER_ZH.exists(), f"Missing {SCATTER_ZH}"
    df = pd.read_csv(SCATTER_ZH)
    x_col = _pick_col(df, ["x", "X", "横坐标"])
    y_col = _pick_col(df, ["y", "Y", "纵坐标"])
    save = "t_cn_scatter_zh"
    _run([
        "--plot", "scatter", "--mode", "file",
        "--file", str(SCATTER_ZH),
        "--x-col", x_col, "--y-col", y_col,
        "--title", "散点图（中文列）",
        "--save-name", save, "--fmt", FMT, "--tight",
        "--no-show" if NO_SHOW else None,
    ])
    _expect_saved(save)


def test_scatter_weird():
    assert SCATTER_WEIRD.exists(), f"Missing {SCATTER_WEIRD}"
    df = pd.read_csv(SCATTER_WEIRD)
    x_col = _pick_col(df, ["x", "X", "feature_x", "横坐标"])
    y_col = _pick_col(df, ["y", "Y", "feature_y", "纵坐标"])
    save = "t_cn_scatter_weird"
    _run([
        "--plot", "scatter", "--mode", "file",
        "--file", str(SCATTER_WEIRD),
        "--x-col", x_col, "--y-col", y_col,
        "--title", "散点图（混合列名）",
        "--save-name", save, "--fmt", FMT, "--tight",
        "--no-show" if NO_SHOW else None,
    ])
    _expect_saved(save)


def test_volcano_zh():
    assert VOLCANO_ZH.exists(), f"Missing {VOLCANO_ZH}"
    df = pd.read_csv(VOLCANO_ZH, sep="\t")
    log2fc_col = _pick_col(df, ["log2fc", "log2FC", "logFC", "LFC", "foldchange", "倍数变化"])
    p_col = _pick_p_col(df)
    label_col = _pick_gene_label_col(df)
    save = "t_cn_volcano_zh"
    _run([
        "--plot", "volcano", "--mode", "file",
        "--file", str(VOLCANO_ZH),
        "--log2fc-col", log2fc_col, "--p-col", p_col, "--label-col", label_col,
        "--title", "火山图（中文 TSV）",
        "--save-name", save, "--fmt", FMT, "--tight",
        "--no-show" if NO_SHOW else None,
    ])
    _expect_saved(save)


def test_volcano_edge():
    assert VOLCANO_EDGE.exists(), f"Missing {VOLCANO_EDGE}"
    df = pd.read_csv(VOLCANO_EDGE, sep="\t")
    log2fc_col = _pick_col(df, ["log2fc", "log2FC", "logFC", "LFC"])
    p_col = _pick_p_col(df)
    label_col = _pick_gene_label_col(df)
    save = "t_cn_volcano_edge"
    _run([
        "--plot", "volcano", "--mode", "file",
        "--file", str(VOLCANO_EDGE),
        "--log2fc-col", log2fc_col, "--p-col", p_col, "--label-col", label_col,
        "--title", "火山图（边界案例）",
        "--save-name", save, "--fmt", FMT, "--tight",
        "--no-show" if NO_SHOW else None,
    ])
    _expect_saved(save)


def test_forest_zh():
    assert FOREST_ZH.exists(), f"Missing {FOREST_ZH}"
    df = pd.read_csv(FOREST_ZH)
    label = _pick_col(df, ["label", "study", "name", "研究", "名称"],
                      contains_tokens=["label", "study", "name", "研究", "名称"])
    effect = _pick_col(df, ["effect", "estimate", "coef", "theta", "效应"],
                       contains_tokens=["effect", "estimate", "coef", "theta", "效应"])
    ci_low = _pick_ci_low_col(df)  # ← 关键修复：兼容 CI下/下限/下界/低限
    ci_high = _pick_ci_high_col(df)  # ← 关键修复：兼容 CI上/上限/上界/高限
    weight = None
    try:
        weight = _pick_col(df, ["weight", "w", "权重"], contains_tokens=["weight", "权重"])
    except KeyError:
        pass
    save = "t_cn_forest_zh"
    argv = [
        "--plot", "forest", "--mode", "file",
        "--file", str(FOREST_ZH),
        "--forest-label-col", label,
        "--effect-col", effect, "--ci-low-col", ci_low, "--ci-high-col", ci_high,
        "--title", "森林图（中文 CSV）",
        "--save-name", save, "--fmt", FMT, "--tight",
        "--no-show" if NO_SHOW else None,
    ]
    if weight:
        argv += ["--weight-col", weight]
    _run(argv)
    _expect_saved(save)


# ---------- main ----------
if __name__ == "__main__":
    test_box_long_zh()
    test_box_long_weird()
    test_scatter_zh()
    test_scatter_weird()
    test_volcano_zh()
    test_volcano_edge()
    test_forest_zh()
    print("✅ 中文静态图测试完成。")

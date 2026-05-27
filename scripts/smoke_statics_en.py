# -*- coding: utf-8 -*-
# scripts/smoke_statics_en.py
from __future__ import annotations

import os
from pathlib import Path
from typing import List, Dict, Sequence

import pandas as pd

from src.main import ResearchDrawApp

# ---------- 路径 ----------
THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parent.parent.resolve()
DATA_DIR = (PROJECT_ROOT / "data").resolve()
OUT_DIR = (PROJECT_ROOT / "outputs" / "figures").resolve()

# 统一 cwd，保证输出路径稳定
try:
    os.chdir(PROJECT_ROOT)
    print(f"[cwd] {Path.cwd()}")
except Exception as e:
    print(f"[WARN] chdir failed: {e}")

OUT_DIR.mkdir(parents=True, exist_ok=True)

# 固定数据文件（英文版）
WIDE_BOX = DATA_DIR / "wide_box.csv"
LONG_BOX = DATA_DIR / "box_long.csv"
SCATTER = DATA_DIR / "scatter.csv"
VOLCANO = DATA_DIR / "volcano.tsv"
FOREST = DATA_DIR / "forest.csv"

FMT = "png"
NO_SHOW = True


# ---------- 小工具 ----------
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


def _pick_col(df: pd.DataFrame, candidates: Sequence[str]) -> str:
    cols = list(df.columns)
    lower = {c.lower(): c for c in cols}
    for k in candidates:
        if k in cols:
            return k
        if k.lower() in lower:
            return lower[k.lower()]
    raise KeyError(f"None of {candidates} found in columns: {cols[:10]}...")


# ---------- 测试用例 ----------
def test_box_file_wide():
    assert WIDE_BOX.exists(), f"Missing {WIDE_BOX}"
    save = "t_static_box_wide"
    _run([
        "--plot", "box", "--mode", "file",
        "--file", str(WIDE_BOX),
        "--title", "Box (Wide CSV)",
        "--save-name", save, "--fmt", FMT,
        "--tight",
        "--no-show" if NO_SHOW else None,
    ])
    _expect_saved(save)


def test_box_file_long():
    assert LONG_BOX.exists(), f"Missing {LONG_BOX}"
    df = pd.read_csv(LONG_BOX)
    group_col = _pick_col(df, ["group", "grp", "Group"])
    value_col = _pick_col(df, ["value", "val", "Value", "y"])
    save = "t_static_box_long"
    _run([
        "--plot", "box", "--mode", "file",
        "--file", str(LONG_BOX),
        "--group-col", group_col, "--value-col", value_col,
        "--title", "Box (Long CSV)",
        "--save-name", save, "--fmt", FMT,
        "--tight",
        "--no-show" if NO_SHOW else None,
    ])
    _expect_saved(save)


def test_scatter_file():
    assert SCATTER.exists(), f"Missing {SCATTER}"
    df = pd.read_csv(SCATTER)
    x_col = _pick_col(df, ["x", "X"])
    y_col = _pick_col(df, ["y", "Y"])
    save = "t_static_scatter_file"
    _run([
        "--plot", "scatter", "--mode", "file",
        "--file", str(SCATTER),
        "--x-col", x_col, "--y-col", y_col,
        "--title", "Scatter from CSV",
        "--save-name", save, "--fmt", FMT,
        "--tight",
        "--no-show" if NO_SHOW else None,
    ])
    _expect_saved(save)


def test_volcano_file():
    assert VOLCANO.exists(), f"Missing {VOLCANO}"
    sep = "\t" if VOLCANO.suffix.lower() == ".tsv" else ","
    df = pd.read_csv(VOLCANO, sep=sep)
    log2fc_col = _pick_col(df, ["log2fc", "log2FC", "logFC", "LFC"])
    p_col = _pick_col(df, ["p", "pval", "p_value", "pvalue", "P", "padj", "adj.P"])
    label_col = _pick_col(df, ["label", "gene", "symbol", "name", "Gene"])
    save = "t_static_volcano_file"
    _run([
        "--plot", "volcano", "--mode", "file",
        "--file", str(VOLCANO),
        "--log2fc-col", log2fc_col, "--p-col", p_col, "--label-col", label_col,
        "--title", "Volcano (TSV)",
        "--save-name", save, "--fmt", FMT,
        "--tight",
        "--no-show" if NO_SHOW else None,
    ])
    _expect_saved(save)


def test_forest_file():
    assert FOREST.exists(), f"Missing {FOREST}"
    df = pd.read_csv(FOREST)
    label = _pick_col(df, ["label", "study", "name", "Study"])
    effect = _pick_col(df, ["effect", "estimate", "coef", "theta"])
    ci_low = _pick_col(df, ["ci_low", "lcl", "lower", "lo", "ci.l", "ci_lower"])
    ci_high = _pick_col(df, ["ci_high", "ucl", "upper", "hi", "ci.u", "ci_upper"])
    weight = None
    try:
        weight = _pick_col(df, ["weight", "w", "Weight"])
    except KeyError:
        pass
    save = "t_static_forest_file"
    argv = [
        "--plot", "forest", "--mode", "file",
        "--file", str(FOREST),
        "--forest-label-col", label,
        "--effect-col", effect, "--ci-low-col", ci_low, "--ci-high-col", ci_high,
        "--title", "Forest (CSV)",
        "--save-name", save, "--fmt", FMT,
        "--tight",
        "--no-show" if NO_SHOW else None,
    ]
    if weight:
        argv += ["--weight-col", weight]
    _run(argv)
    _expect_saved(save)


# ---------- main ----------
if __name__ == "__main__":
    test_box_file_wide()
    test_box_file_long()
    test_scatter_file()
    test_volcano_file()
    test_forest_file()
    print("✅ English static tests finished.")

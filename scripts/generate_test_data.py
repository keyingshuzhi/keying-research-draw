# -*- coding = utf-8 -*-
# @Time: 2025/10/23 上午11:58
# @Author: 柯影数智
# @File: generate_test_data.py
# @Email: 1090461393@qq.com
# @SoftWare: PyCharm

# -*- coding: utf-8 -*-
# scripts/generate_test_data.py
"""
生成科研绘图的全套测试数据（中英文、CSV/TSV、包含正常/极端/缺失情况）。
输出目录：<project_root>/data

数据清单：
1) 箱线图（长表/宽表/中文/含缺失与极端值）
   - data/box_long.csv           (group,value)
   - data/long_box_zh.csv        (组,数值)
   - data/wide_box.csv           (Ctrl,TreatA,TreatB) 宽表
   - data/long_box_weird.csv     (含 NaN / 离群）

2) 散点（英文/中文/含缺失）
   - data/scatter.csv            (x,y)
   - data/scatter_zh.csv         (横坐标,纵坐标)
   - data/scatter_weird.csv      (含 NaN)

3) 火山图（英文/中文/边界值）
   - data/volcano.tsv            (gene,log2FC,pvalue)   [TSV]
   - data/volcano_zh.csv         (基因,log2FC,p值)      [TSV]
   - data/volcano_edge.tsv       (极端 p 值/FC，含 0/1/很小值) [TSV]

4) 森林图（英文/中文/含权重）
   - data/forest.csv             (label,effect,ci_low,ci_high,weight)
   - data/forest_zh.csv          (研究,效应,CI下,CI上,权重)

5) 领域图 demo 数据（biomed/clinical/materials/remote/finance/psych）
   - data/biomed/*.csv
   - data/clinical/*.csv
   - data/materials/*.csv
   - data/remote/*.csv
   - data/finance/*.csv
   - data/psych/*.csv
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]  # <project_root>
DATA = ROOT / "data"
DATA.mkdir(parents=True, exist_ok=True)


def _write(df: pd.DataFrame, name: str, sep=",", encoding="utf-8", subdir: Path | None = None):
    base = subdir or DATA
    base.mkdir(parents=True, exist_ok=True)
    path = base / name
    df.to_csv(path, sep=sep, index=False, encoding=encoding)
    print(f"✅ Saved {path}  shape={df.shape}")
    print(df.head(min(5, len(df))))
    print("-" * 60)


def gen_box():
    rng = np.random.default_rng(42)
    # 长表（英文）
    df_long = pd.DataFrame({
        "group": np.repeat(["Ctrl", "TreatA", "TreatB"], [60, 60, 60]),
        "value": np.r_[rng.normal(0, 1, 60),
        rng.normal(0.4, 1.1, 60),
        rng.normal(-0.2, 0.9, 60)]
    })
    _write(df_long, "box_long.csv")

    # 长表（中文）
    df_long_zh = df_long.rename(columns={"group": "组", "value": "数值"})
    _write(df_long_zh, "long_box_zh.csv", encoding="utf-8-sig")

    # 宽表
    df_wide = pd.DataFrame({
        "Ctrl": rng.normal(0, 1, 80),
        "TreatA": rng.normal(0.4, 1.1, 90)[:80],
        "TreatB": rng.normal(-0.2, 0.9, 85)[:80],
    })
    _write(df_wide, "wide_box.csv")

    # 含 NaN/离群
    weird = df_long.copy()
    weird.loc[0, "value"] = np.nan
    weird.loc[1, "value"] = 12.0
    weird.loc[2, "value"] = -9.5
    _write(weird, "long_box_weird.csv")


def gen_scatter():
    rng = np.random.default_rng(123)
    x = rng.normal(0, 1, 120)
    y = 1.5 * x + 0.6 + rng.normal(0, 0.8, 120)
    df = pd.DataFrame({"x": x, "y": y})
    _write(df, "scatter.csv")

    # 中文列名
    df_zh = df.rename(columns={"x": "横坐标", "y": "纵坐标"})
    _write(df_zh, "scatter_zh.csv", encoding="utf-8-sig")

    # 含 NaN
    df_weird = df.copy()
    df_weird.loc[0, "x"] = np.nan
    df_weird.loc[5, "y"] = np.nan
    _write(df_weird, "scatter_weird.csv")


def gen_volcano():
    rng = np.random.default_rng(7)
    n = 400
    log2fc = rng.normal(0, 1, n)
    pvals = rng.uniform(0, 1, n) ** 3  # 偏向小 p
    genes = [f"G{i}" for i in range(n)]
    df = pd.DataFrame({"gene": genes, "log2FC": log2fc, "pvalue": pvals})
    _write(df, "volcano.tsv", sep="\t")

    # 中文列名
    df_zh = df.rename(columns={"gene": "基因", "pvalue": "p值"})
    _write(df_zh, "volcano_zh.csv", sep="\t", encoding="utf-8-sig")

    # 边界/极端值
    p_edge = pvals.copy()
    p_edge[:3] = [0.0, 1e-300, 1.0]  # 0 / 很小 / 1
    fc_edge = log2fc.copy()
    fc_edge[:3] = [-10.0, 0.0, 10.0]
    df_edge = pd.DataFrame({"gene": genes, "log2FC": fc_edge, "pvalue": p_edge})
    _write(df_edge, "volcano_edge.tsv", sep="\t")


def gen_forest():
    rng = np.random.default_rng(9)
    k = 8
    eff = rng.normal(0.1, 0.25, k)
    ciw = rng.uniform(0.15, 0.45, k)
    lo, hi = eff - ciw, eff + ciw
    w = rng.uniform(0.5, 2.0, k)
    df = pd.DataFrame({
        "label": [f"Study {i + 1}" for i in range(k)],
        "effect": eff, "ci_low": lo, "ci_high": hi, "weight": w
    })
    _write(df, "forest.csv")

    # 中文列名
    df_zh = df.rename(
        columns={"label": "研究", "effect": "效应", "ci_low": "CI下", "ci_high": "CI上", "weight": "权重"})
    _write(df_zh, "forest_zh.csv", encoding="utf-8-sig")


def gen_biomed():
    rng = np.random.default_rng(101)
    biomed = DATA / "biomed"

    # MA plot
    n = 200
    mean = rng.normal(8, 1.2, n)
    log2fc = rng.normal(0, 1, n)
    pval = rng.uniform(0, 1, n) ** 3
    _write(pd.DataFrame({"mean": mean, "log2fc": log2fc, "pvalue": pval}),
           "ma.csv", subdir=biomed)

    # Enrichment dotplot
    terms = [f"Pathway_{i}" for i in range(1, 16)]
    counts = rng.integers(5, 80, size=len(terms))
    ratio = counts / rng.integers(100, 300, size=len(terms))
    pval = np.sort(rng.uniform(0.0001, 0.2, size=len(terms)))[::-1]
    _write(pd.DataFrame({"term": terms, "pvalue": pval, "count": counts, "ratio": ratio}),
           "enrich_dot.csv", subdir=biomed)

    # GSEA
    rank = np.arange(1, 201)
    es = np.cumsum(rng.normal(0, 0.08, size=rank.size))
    hits = rng.choice([0, 1], size=rank.size, p=[0.9, 0.1])
    _write(pd.DataFrame({"rank": rank, "running_es": es, "hit": hits}),
           "gsea.csv", subdir=biomed)

    # Embedding (PCA/UMAP)
    groups = np.repeat(["A", "B", "C"], [60, 60, 60])
    f1 = np.r_[rng.normal(0, 1, 60), rng.normal(3, 1, 60), rng.normal(-2, 1, 60)]
    f2 = np.r_[rng.normal(0, 1, 60), rng.normal(2, 1, 60), rng.normal(-1.5, 1, 60)]
    f3 = rng.normal(0, 1, groups.size)
    f4 = rng.normal(0, 1, groups.size)
    f5 = rng.normal(0, 1, groups.size)
    _write(pd.DataFrame({"f1": f1, "f2": f2, "f3": f3, "f4": f4, "f5": f5, "group": groups}),
           "embedding.csv", subdir=biomed)

    # UpSet
    sets = pd.DataFrame({
        "SetA": rng.integers(0, 2, 120),
        "SetB": rng.integers(0, 2, 120),
        "SetC": rng.integers(0, 2, 120),
        "SetD": rng.integers(0, 2, 120),
    }).astype(bool)
    _write(sets, "upset.csv", subdir=biomed)


def gen_clinical():
    rng = np.random.default_rng(202)
    clinical = DATA / "clinical"

    # Kaplan-Meier
    n = 200
    group = np.repeat(["Treatment", "Control"], n // 2)
    time = rng.exponential(scale=10, size=n)
    event = rng.binomial(1, 0.7, size=n)
    _write(pd.DataFrame({"time": time, "event": event, "group": group}),
           "km.csv", subdir=clinical)

    # ROC/PR
    y = rng.binomial(1, 0.4, size=n)
    score = y * rng.uniform(0.5, 1.0, size=n) + (1 - y) * rng.uniform(0.0, 0.6, size=n)
    _write(pd.DataFrame({"y": y, "score": score}), "roc.csv", subdir=clinical)

    # Calibration
    prob = np.clip(score + rng.normal(0, 0.08, size=n), 0, 1)
    _write(pd.DataFrame({"y": y, "prob": prob}), "calibration.csv", subdir=clinical)

    # Bland-Altman
    x = rng.normal(10, 2, size=120)
    y2 = x + rng.normal(0, 1.0, size=120)
    _write(pd.DataFrame({"x": x, "y": y2}), "bland_altman.csv", subdir=clinical)

    # DCA
    _write(pd.DataFrame({"y": y, "prob": prob}), "dca.csv", subdir=clinical)


def gen_materials():
    rng = np.random.default_rng(303)
    materials = DATA / "materials"

    # Stress-strain
    strain = np.linspace(0, 0.25, 200)
    stress = 200 * strain + 80 * strain ** 2 + rng.normal(0, 2, size=strain.size)
    _write(pd.DataFrame({"strain": strain, "stress": stress}),
           "stress_strain.csv", subdir=materials)

    # XRD
    theta = np.linspace(10, 80, 400)
    def _peak(x, mu, amp, sig):
        return amp * np.exp(-(x - mu) ** 2 / (2 * sig ** 2))
    inten_a = _peak(theta, 28, 200, 1.2) + _peak(theta, 47, 120, 1.5) + rng.normal(0, 2, theta.size)
    inten_b = _peak(theta, 32, 180, 1.3) + _peak(theta, 56, 140, 1.6) + rng.normal(0, 2, theta.size)
    df_xrd = pd.DataFrame({
        "two_theta": np.r_[theta, theta],
        "intensity": np.r_[inten_a, inten_b],
        "sample": ["SampleA"] * theta.size + ["SampleB"] * theta.size,
    })
    _write(df_xrd, "xrd.csv", subdir=materials)

    # Raman/FTIR
    shift = np.linspace(400, 1800, 300)
    r1 = _peak(shift, 520, 90, 20) + _peak(shift, 1350, 60, 25) + rng.normal(0, 1.5, shift.size)
    r2 = _peak(shift, 480, 80, 18) + _peak(shift, 1580, 70, 28) + rng.normal(0, 1.5, shift.size)
    df_raman = pd.DataFrame({
        "shift": np.r_[shift, shift],
        "intensity": np.r_[r1, r2],
        "sample": ["Material1"] * shift.size + ["Material2"] * shift.size,
    })
    _write(df_raman, "raman.csv", subdir=materials)

    # Phase diagram
    comp = np.linspace(0, 1, 20)
    temp = np.linspace(200, 800, 20)
    cc, tt = np.meshgrid(comp, temp)
    val = np.sin(cc * np.pi) + (tt - 200) / 800
    df_phase = pd.DataFrame({"composition": cc.ravel(), "temperature": tt.ravel(), "value": val.ravel()})
    _write(df_phase, "phase.csv", subdir=materials)

    # Hysteresis
    field = np.r_[np.linspace(-1, 1, 150), np.linspace(1, -1, 150)]
    mag = np.tanh(field * 2.5) + rng.normal(0, 0.02, field.size)
    _write(pd.DataFrame({"field": field, "magnetization": mag, "sample": "Loop1"}),
           "hysteresis.csv", subdir=materials)


def gen_remote():
    rng = np.random.default_rng(404)
    remote = DATA / "remote"

    # Spectral signature
    wl = np.linspace(400, 1000, 200)
    forest = 0.1 + 0.4 * (1 - np.exp(-(wl - 550) / 200))
    water = 0.05 + 0.05 * np.exp(-(wl - 500) / 80)
    soil = 0.15 + 0.2 * (wl - 400) / 600
    df_spec = pd.DataFrame({
        "wavelength": np.r_[wl, wl, wl],
        "reflectance": np.r_[forest, water, soil],
        "class": ["Forest"] * wl.size + ["Water"] * wl.size + ["Soil"] * wl.size,
    })
    _write(df_spec, "spectral_signature.csv", subdir=remote)

    # Index time series
    dates = pd.date_range("2024-01-01", periods=36, freq="M")
    ndvi_a = 0.3 + 0.1 * np.sin(np.linspace(0, 3 * np.pi, len(dates))) + rng.normal(0, 0.02, len(dates))
    ndvi_b = 0.25 + 0.12 * np.sin(np.linspace(0.3, 3 * np.pi + 0.3, len(dates))) + rng.normal(0, 0.02, len(dates))
    df_ts = pd.DataFrame({
        "date": np.r_[dates, dates],
        "value": np.r_[ndvi_a, ndvi_b],
        "group": ["RegionA"] * len(dates) + ["RegionB"] * len(dates),
    })
    _write(df_ts, "index_ts.csv", subdir=remote)

    # Confusion matrix (long)
    true = rng.choice(["Forest", "Water", "Soil"], size=200)
    pred = true.copy()
    flip = rng.random(200) < 0.15
    pred[flip] = rng.choice(["Forest", "Water", "Soil"], size=flip.sum())
    _write(pd.DataFrame({"true": true, "pred": pred}), "confusion.csv", subdir=remote)

    # Class distribution
    classes = ["Forest", "Water", "Soil"]
    df_cd = pd.DataFrame({
        "class": classes * 2,
        "count": rng.integers(50, 200, size=6),
        "group": ["RegionA"] * 3 + ["RegionB"] * 3,
    })
    _write(df_cd, "class_dist.csv", subdir=remote)


def gen_finance():
    rng = np.random.default_rng(505)
    finance = DATA / "finance"

    # Candlestick
    dates = pd.date_range("2024-01-01", periods=60, freq="D")
    price = np.cumsum(rng.normal(0, 1, size=len(dates))) + 100
    open_ = price + rng.normal(0, 0.5, len(dates))
    close = price + rng.normal(0, 0.5, len(dates))
    high = np.maximum(open_, close) + rng.uniform(0.2, 1.0, len(dates))
    low = np.minimum(open_, close) - rng.uniform(0.2, 1.0, len(dates))
    volume = rng.integers(1000, 5000, len(dates))
    _write(pd.DataFrame({
        "date": dates, "open": open_, "high": high, "low": low, "close": close, "volume": volume
    }), "candlestick.csv", subdir=finance)

    # Returns
    returns = rng.normal(0.0005, 0.01, size=len(dates))
    _write(pd.DataFrame({"date": dates, "return": returns}), "returns.csv", subdir=finance)

    # Frontier data
    rA = rng.normal(0.0006, 0.01, size=250)
    rB = rng.normal(0.0004, 0.008, size=250)
    rC = rng.normal(0.0008, 0.012, size=250)
    _write(pd.DataFrame({"AssetA": rA, "AssetB": rB, "AssetC": rC}), "frontier.csv", subdir=finance)

    # Series for ACF/PACF
    series = np.zeros(300)
    for i in range(1, len(series)):
        series[i] = 0.7 * series[i - 1] + rng.normal(0, 1)
    _write(pd.DataFrame({"value": series}), "series.csv", subdir=finance)


def gen_psych():
    rng = np.random.default_rng(606)
    psych = DATA / "psych"

    # Likert
    items = [f"Q{i}" for i in range(1, 6)]
    rows = []
    for it in items:
        for resp in range(1, 6):
            rows.append({"item": it, "response": resp, "count": int(rng.integers(20, 80))})
    _write(pd.DataFrame(rows), "likert.csv", subdir=psych)

    # Raincloud
    df_rc = pd.DataFrame({
        "group": np.repeat(["A", "B", "C"], 80),
        "value": np.r_[rng.normal(0, 1, 80), rng.normal(0.5, 1, 80), rng.normal(-0.2, 1, 80)],
    })
    _write(df_rc, "raincloud.csv", subdir=psych)

    # IRT ICC
    df_irt = pd.DataFrame({
        "item": [f"Item{i}" for i in range(1, 6)],
        "a": rng.uniform(0.6, 1.8, 5),
        "b": rng.uniform(-1.0, 1.5, 5),
        "c": rng.uniform(0.0, 0.25, 5),
    })
    _write(df_irt, "irt_icc.csv", subdir=psych)

    # Factor loadings
    df_fl = pd.DataFrame({
        "factor": ["F1"] * 5 + ["F2"] * 5,
        "item": [f"V{i}" for i in range(1, 6)] + [f"V{i}" for i in range(6, 11)],
        "loading": rng.uniform(-0.8, 0.9, 10),
    })
    _write(df_fl, "factor_loadings.csv", subdir=psych)

    # Interaction
    df_int = pd.DataFrame({
        "factor1": np.repeat(["Low", "High"], 60),
        "factor2": np.tile(np.repeat(["G1", "G2"], 30), 2),
        "value": rng.normal(0, 1, 120) + np.tile([0.2, -0.2], 60),
    })
    _write(df_int, "interaction.csv", subdir=psych)


if __name__ == "__main__":
    print(f"Output dir: {DATA}")
    gen_box()
    gen_scatter()
    gen_volcano()
    gen_forest()
    gen_biomed()
    gen_clinical()
    gen_materials()
    gen_remote()
    gen_finance()
    gen_psych()
    print("🎉 All test datasets created.")

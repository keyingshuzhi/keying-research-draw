# -*- coding: utf-8 -*-
"""
Generate demo datasets for domain plots without external deps.
"""
from __future__ import annotations

import csv
import math
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

random.seed(42)


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _write_csv(path: Path, headers, rows):
    _ensure_dir(path.parent)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)
    print("saved", path)


def gen_biomed():
    base = DATA / "biomed"

    # MA plot
    rows = []
    for _ in range(200):
        mean = random.gauss(8, 1.2)
        log2fc = random.gauss(0, 1)
        pval = random.random() ** 3
        rows.append([mean, log2fc, pval])
    _write_csv(base / "ma.csv", ["mean", "log2fc", "pvalue"], rows)

    # Enrichment dotplot
    rows = []
    for i in range(1, 16):
        term = f"Pathway_{i}"
        count = random.randint(5, 80)
        ratio = count / random.randint(100, 300)
        pval = 10 ** (-random.uniform(0.3, 2.5))
        rows.append([term, pval, count, ratio])
    _write_csv(base / "enrich_dot.csv", ["term", "pvalue", "count", "ratio"], rows)

    # GSEA
    rows = []
    running = 0.0
    for i in range(1, 201):
        running += random.gauss(0, 0.08)
        hit = 1 if random.random() < 0.1 else 0
        rows.append([i, running, hit])
    _write_csv(base / "gsea.csv", ["rank", "running_es", "hit"], rows)

    # Embedding
    rows = []
    for grp, mu in [("A", 0), ("B", 3), ("C", -2)]:
        for _ in range(60):
            f1 = random.gauss(mu, 1)
            f2 = random.gauss(mu * 0.7, 1)
            f3 = random.gauss(0, 1)
            f4 = random.gauss(0, 1)
            f5 = random.gauss(0, 1)
            rows.append([f1, f2, f3, f4, f5, grp])
    _write_csv(base / "embedding.csv", ["f1", "f2", "f3", "f4", "f5", "group"], rows)

    # UpSet
    rows = []
    for _ in range(120):
        rows.append([random.randint(0, 1) for _ in range(4)])
    _write_csv(base / "upset.csv", ["SetA", "SetB", "SetC", "SetD"], rows)


def gen_clinical():
    base = DATA / "clinical"

    # KM
    rows = []
    for grp in ["Treatment", "Control"]:
        for _ in range(100):
            time = random.expovariate(1 / 10.0)
            event = 1 if random.random() < 0.7 else 0
            rows.append([time, event, grp])
    _write_csv(base / "km.csv", ["time", "event", "group"], rows)

    # ROC/PR
    rows = []
    for _ in range(200):
        y = 1 if random.random() < 0.4 else 0
        score = random.uniform(0.5, 1.0) if y else random.uniform(0.0, 0.6)
        rows.append([y, score])
    _write_csv(base / "roc.csv", ["y", "score"], rows)

    # Calibration / DCA
    rows2 = []
    for y, score in rows:
        prob = min(max(score + random.gauss(0, 0.08), 0), 1)
        rows2.append([y, prob])
    _write_csv(base / "calibration.csv", ["y", "prob"], rows2)
    _write_csv(base / "dca.csv", ["y", "prob"], rows2)

    # Bland-Altman
    rows = []
    for _ in range(120):
        x = random.gauss(10, 2)
        y = x + random.gauss(0, 1)
        rows.append([x, y])
    _write_csv(base / "bland_altman.csv", ["x", "y"], rows)


def _peak(x, mu, amp, sig):
    return amp * math.exp(-((x - mu) ** 2) / (2 * sig ** 2))


def gen_materials():
    base = DATA / "materials"

    # Stress-strain
    rows = []
    for i in range(200):
        strain = i / 800.0
        stress = 200 * strain + 80 * strain ** 2 + random.gauss(0, 2)
        rows.append([strain, stress])
    _write_csv(base / "stress_strain.csv", ["strain", "stress"], rows)

    # XRD
    rows = []
    for sample in ["SampleA", "SampleB"]:
        for i in range(400):
            theta = 10 + i * 0.175
            if sample == "SampleA":
                inten = _peak(theta, 28, 200, 1.2) + _peak(theta, 47, 120, 1.5) + random.gauss(0, 2)
            else:
                inten = _peak(theta, 32, 180, 1.3) + _peak(theta, 56, 140, 1.6) + random.gauss(0, 2)
            rows.append([theta, inten, sample])
    _write_csv(base / "xrd.csv", ["two_theta", "intensity", "sample"], rows)

    # Raman
    rows = []
    for sample in ["Material1", "Material2"]:
        for i in range(300):
            shift = 400 + i * 4.666
            if sample == "Material1":
                inten = _peak(shift, 520, 90, 20) + _peak(shift, 1350, 60, 25) + random.gauss(0, 1.5)
            else:
                inten = _peak(shift, 480, 80, 18) + _peak(shift, 1580, 70, 28) + random.gauss(0, 1.5)
            rows.append([shift, inten, sample])
    _write_csv(base / "raman.csv", ["shift", "intensity", "sample"], rows)

    # Phase diagram
    rows = []
    for i in range(20):
        comp = i / 19.0
        for j in range(20):
            temp = 200 + j * 30
            val = math.sin(comp * math.pi) + (temp - 200) / 800
            rows.append([comp, temp, val])
    _write_csv(base / "phase.csv", ["composition", "temperature", "value"], rows)

    # Hysteresis
    rows = []
    for x in [i / 75.0 - 1 for i in range(150)] + [1 - i / 75.0 for i in range(150)]:
        mag = math.tanh(x * 2.5) + random.gauss(0, 0.02)
        rows.append([x, mag, "Loop1"])
    _write_csv(base / "hysteresis.csv", ["field", "magnetization", "sample"], rows)


def gen_remote():
    base = DATA / "remote"

    # Spectral signature
    rows = []
    for cls in ["Forest", "Water", "Soil"]:
        for i in range(200):
            wl = 400 + i * 3
            if cls == "Forest":
                refl = 0.1 + 0.4 * (1 - math.exp(-(wl - 550) / 200))
            elif cls == "Water":
                refl = 0.05 + 0.05 * math.exp(-(wl - 500) / 80)
            else:
                refl = 0.15 + 0.2 * (wl - 400) / 600
            rows.append([wl, refl, cls])
    _write_csv(base / "spectral_signature.csv", ["wavelength", "reflectance", "class"], rows)

    # Index time series
    rows = []
    start = datetime(2024, 1, 1)
    for grp in ["RegionA", "RegionB"]:
        for i in range(36):
            date = start + timedelta(days=30 * i)
            val = 0.3 + 0.1 * math.sin(i / 6.0) + random.gauss(0, 0.02)
            if grp == "RegionB":
                val -= 0.03
            rows.append([date.strftime("%Y-%m-%d"), val, grp])
    _write_csv(base / "index_ts.csv", ["date", "value", "group"], rows)

    # Confusion
    classes = ["Forest", "Water", "Soil"]
    rows = []
    for _ in range(200):
        true = random.choice(classes)
        pred = true if random.random() > 0.15 else random.choice(classes)
        rows.append([true, pred])
    _write_csv(base / "confusion.csv", ["true", "pred"], rows)

    # Class distribution
    rows = []
    for grp in ["RegionA", "RegionB"]:
        for cls in classes:
            rows.append([cls, random.randint(50, 200), grp])
    _write_csv(base / "class_dist.csv", ["class", "count", "group"], rows)


def gen_finance():
    base = DATA / "finance"

    # Candlestick
    rows = []
    start = datetime(2024, 1, 1)
    price = 100.0
    for i in range(60):
        date = start + timedelta(days=i)
        price += random.gauss(0, 1)
        open_ = price + random.gauss(0, 0.5)
        close = price + random.gauss(0, 0.5)
        high = max(open_, close) + random.uniform(0.2, 1.0)
        low = min(open_, close) - random.uniform(0.2, 1.0)
        volume = random.randint(1000, 5000)
        rows.append([date.strftime("%Y-%m-%d"), open_, high, low, close, volume])
    _write_csv(base / "candlestick.csv", ["date", "open", "high", "low", "close", "volume"], rows)

    # Returns
    rows = []
    for i in range(60):
        date = start + timedelta(days=i)
        ret = random.gauss(0.0005, 0.01)
        rows.append([date.strftime("%Y-%m-%d"), ret])
    _write_csv(base / "returns.csv", ["date", "return"], rows)

    # Frontier
    rows = []
    for _ in range(250):
        rows.append([random.gauss(0.0006, 0.01), random.gauss(0.0004, 0.008), random.gauss(0.0008, 0.012)])
    _write_csv(base / "frontier.csv", ["AssetA", "AssetB", "AssetC"], rows)

    # Series
    rows = []
    x = 0.0
    for _ in range(300):
        x = 0.7 * x + random.gauss(0, 1)
        rows.append([x])
    _write_csv(base / "series.csv", ["value"], rows)


def gen_psych():
    base = DATA / "psych"

    # Likert
    rows = []
    for q in range(1, 6):
        for resp in range(1, 6):
            rows.append([f"Q{q}", resp, random.randint(20, 80)])
    _write_csv(base / "likert.csv", ["item", "response", "count"], rows)

    # Raincloud
    rows = []
    for grp, mu in [("A", 0), ("B", 0.5), ("C", -0.2)]:
        for _ in range(80):
            rows.append([grp, random.gauss(mu, 1)])
    _write_csv(base / "raincloud.csv", ["group", "value"], rows)

    # IRT ICC
    rows = []
    for i in range(1, 6):
        rows.append([f"Item{i}", random.uniform(0.6, 1.8), random.uniform(-1.0, 1.5), random.uniform(0.0, 0.25)])
    _write_csv(base / "irt_icc.csv", ["item", "a", "b", "c"], rows)

    # Factor loadings
    rows = []
    for i in range(1, 6):
        rows.append(["F1", f"V{i}", random.uniform(-0.8, 0.9)])
    for i in range(6, 11):
        rows.append(["F2", f"V{i}", random.uniform(-0.8, 0.9)])
    _write_csv(base / "factor_loadings.csv", ["factor", "item", "loading"], rows)

    # Interaction
    rows = []
    for f1 in ["Low", "High"]:
        for f2 in ["G1", "G2"]:
            for _ in range(30):
                offset = 0.2 if f1 == "High" else -0.1
                offset += 0.1 if f2 == "G1" else -0.05
                rows.append([f1, f2, random.gauss(offset, 1)])
    _write_csv(base / "interaction.csv", ["factor1", "factor2", "value"], rows)


if __name__ == "__main__":
    gen_biomed()
    gen_clinical()
    gen_materials()
    gen_remote()
    gen_finance()
    gen_psych()
    print("done")

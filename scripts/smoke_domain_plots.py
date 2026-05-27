# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from pathlib import Path
from typing import List

from src.main import ResearchDrawApp

THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parent.parent.resolve()
DATA_DIR = PROJECT_ROOT / "data"
OUT_DIR = PROJECT_ROOT / "outputs" / "figures"

FMT = "png"
NO_SHOW = True

try:
    os.chdir(PROJECT_ROOT)
except Exception:
    pass

OUT_DIR.mkdir(parents=True, exist_ok=True)


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


def test_biomed_ma():
    save = "t_bio_ma"
    _run(["--plot", "ma", "--mode", "file", "--file", DATA_DIR / "biomed" / "ma.csv",
          "--save-name", save, "--fmt", FMT, "--no-show" if NO_SHOW else None])
    _expect_saved(save)


def test_biomed_enrich():
    save = "t_bio_enrich"
    _run(["--plot", "enrich_dot", "--mode", "file", "--file", DATA_DIR / "biomed" / "enrich_dot.csv",
          "--save-name", save, "--fmt", FMT, "--no-show" if NO_SHOW else None])
    _expect_saved(save)


def test_biomed_gsea():
    save = "t_bio_gsea"
    _run(["--plot", "gsea", "--mode", "file", "--file", DATA_DIR / "biomed" / "gsea.csv",
          "--save-name", save, "--fmt", FMT, "--no-show" if NO_SHOW else None])
    _expect_saved(save)


def test_biomed_embedding():
    save = "t_bio_embedding"
    _run(["--plot", "embedding", "--mode", "file", "--file", DATA_DIR / "biomed" / "embedding.csv",
          "--save-name", save, "--fmt", FMT, "--no-show" if NO_SHOW else None])
    _expect_saved(save)


def test_biomed_upset():
    save = "t_bio_upset"
    _run(["--plot", "upset", "--mode", "file", "--file", DATA_DIR / "biomed" / "upset.csv",
          "--save-name", save, "--fmt", FMT, "--no-show" if NO_SHOW else None])
    _expect_saved(save)


def test_clinical_km():
    save = "t_clin_km"
    _run(["--plot", "km", "--mode", "file", "--file", DATA_DIR / "clinical" / "km.csv",
          "--save-name", save, "--fmt", FMT, "--no-show" if NO_SHOW else None])
    _expect_saved(save)


def test_clinical_roc():
    save = "t_clin_roc"
    _run(["--plot", "roc", "--mode", "file", "--file", DATA_DIR / "clinical" / "roc.csv",
          "--save-name", save, "--fmt", FMT, "--no-show" if NO_SHOW else None])
    _expect_saved(save)


def test_clinical_calibration():
    save = "t_clin_calib"
    _run(["--plot", "calibration", "--mode", "file", "--file", DATA_DIR / "clinical" / "calibration.csv",
          "--save-name", save, "--fmt", FMT, "--no-show" if NO_SHOW else None])
    _expect_saved(save)


def test_clinical_bland_altman():
    save = "t_clin_ba"
    _run(["--plot", "bland_altman", "--mode", "file", "--file", DATA_DIR / "clinical" / "bland_altman.csv",
          "--save-name", save, "--fmt", FMT, "--no-show" if NO_SHOW else None])
    _expect_saved(save)


def test_clinical_dca():
    save = "t_clin_dca"
    _run(["--plot", "dca", "--mode", "file", "--file", DATA_DIR / "clinical" / "dca.csv",
          "--save-name", save, "--fmt", FMT, "--no-show" if NO_SHOW else None])
    _expect_saved(save)


def test_materials_stress_strain():
    save = "t_mat_stress"
    _run(["--plot", "stress_strain", "--mode", "file", "--file", DATA_DIR / "materials" / "stress_strain.csv",
          "--save-name", save, "--fmt", FMT, "--no-show" if NO_SHOW else None])
    _expect_saved(save)


def test_materials_xrd():
    save = "t_mat_xrd"
    _run(["--plot", "xrd", "--mode", "file", "--file", DATA_DIR / "materials" / "xrd.csv",
          "--save-name", save, "--fmt", FMT, "--no-show" if NO_SHOW else None])
    _expect_saved(save)


def test_materials_raman():
    save = "t_mat_raman"
    _run(["--plot", "raman", "--mode", "file", "--file", DATA_DIR / "materials" / "raman.csv",
          "--save-name", save, "--fmt", FMT, "--no-show" if NO_SHOW else None])
    _expect_saved(save)


def test_materials_phase():
    save = "t_mat_phase"
    _run(["--plot", "phase", "--mode", "file", "--file", DATA_DIR / "materials" / "phase.csv",
          "--save-name", save, "--fmt", FMT, "--no-show" if NO_SHOW else None])
    _expect_saved(save)


def test_materials_hysteresis():
    save = "t_mat_hyst"
    _run(["--plot", "hysteresis", "--mode", "file", "--file", DATA_DIR / "materials" / "hysteresis.csv",
          "--save-name", save, "--fmt", FMT, "--no-show" if NO_SHOW else None])
    _expect_saved(save)


def test_remote_spectral():
    save = "t_rs_spectral"
    _run(["--plot", "spectral_signature", "--mode", "file", "--file", DATA_DIR / "remote" / "spectral_signature.csv",
          "--save-name", save, "--fmt", FMT, "--no-show" if NO_SHOW else None])
    _expect_saved(save)


def test_remote_index_ts():
    save = "t_rs_index"
    _run(["--plot", "index_ts", "--mode", "file", "--file", DATA_DIR / "remote" / "index_ts.csv",
          "--save-name", save, "--fmt", FMT, "--no-show" if NO_SHOW else None])
    _expect_saved(save)


def test_remote_confusion():
    save = "t_rs_confusion"
    _run(["--plot", "confusion", "--mode", "file", "--file", DATA_DIR / "remote" / "confusion.csv",
          "--save-name", save, "--fmt", FMT, "--no-show" if NO_SHOW else None])
    _expect_saved(save)


def test_remote_class_dist():
    save = "t_rs_class_dist"
    _run(["--plot", "class_dist", "--mode", "file", "--file", DATA_DIR / "remote" / "class_dist.csv",
          "--save-name", save, "--fmt", FMT, "--no-show" if NO_SHOW else None])
    _expect_saved(save)


def test_finance_candlestick():
    save = "t_fin_candle"
    _run(["--plot", "candlestick", "--mode", "file", "--file", DATA_DIR / "finance" / "candlestick.csv",
          "--save-name", save, "--fmt", FMT, "--no-show" if NO_SHOW else None])
    _expect_saved(save)


def test_finance_cum_return():
    save = "t_fin_cumret"
    _run(["--plot", "cum_return", "--mode", "file", "--file", DATA_DIR / "finance" / "returns.csv",
          "--save-name", save, "--fmt", FMT, "--no-show" if NO_SHOW else None])
    _expect_saved(save)


def test_finance_rolling():
    save = "t_fin_roll"
    _run(["--plot", "rolling_stats", "--mode", "file", "--file", DATA_DIR / "finance" / "returns.csv",
          "--save-name", save, "--fmt", FMT, "--no-show" if NO_SHOW else None])
    _expect_saved(save)


def test_finance_frontier():
    save = "t_fin_frontier"
    _run(["--plot", "frontier", "--mode", "file", "--file", DATA_DIR / "finance" / "frontier.csv",
          "--save-name", save, "--fmt", FMT, "--no-show" if NO_SHOW else None])
    _expect_saved(save)


def test_finance_acf_pacf():
    save = "t_fin_acf_pacf"
    _run(["--plot", "acf_pacf", "--mode", "file", "--file", DATA_DIR / "finance" / "series.csv",
          "--save-name", save, "--fmt", FMT, "--no-show" if NO_SHOW else None])
    _expect_saved(save)


def test_psych_likert():
    save = "t_psy_likert"
    _run(["--plot", "likert", "--mode", "file", "--file", DATA_DIR / "psych" / "likert.csv",
          "--save-name", save, "--fmt", FMT, "--no-show" if NO_SHOW else None])
    _expect_saved(save)


def test_psych_raincloud():
    save = "t_psy_raincloud"
    _run(["--plot", "raincloud", "--mode", "file", "--file", DATA_DIR / "psych" / "raincloud.csv",
          "--save-name", save, "--fmt", FMT, "--no-show" if NO_SHOW else None])
    _expect_saved(save)


def test_psych_irt_icc():
    save = "t_psy_irt"
    _run(["--plot", "irt_icc", "--mode", "file", "--file", DATA_DIR / "psych" / "irt_icc.csv",
          "--save-name", save, "--fmt", FMT, "--no-show" if NO_SHOW else None])
    _expect_saved(save)


def test_psych_factor_loadings():
    save = "t_psy_loadings"
    _run(["--plot", "factor_loadings", "--mode", "file", "--file", DATA_DIR / "psych" / "factor_loadings.csv",
          "--save-name", save, "--fmt", FMT, "--no-show" if NO_SHOW else None])
    _expect_saved(save)


def test_psych_interaction():
    save = "t_psy_interaction"
    _run(["--plot", "interaction", "--mode", "file", "--file", DATA_DIR / "psych" / "interaction.csv",
          "--save-name", save, "--fmt", FMT, "--no-show" if NO_SHOW else None])
    _expect_saved(save)

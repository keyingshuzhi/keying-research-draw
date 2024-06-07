from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("PLOT_BACKEND", "Agg")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/research-draw-mplconfig")


@pytest.fixture(autouse=True)
def _headless_matplotlib(monkeypatch, tmp_path):
    monkeypatch.setenv("MPLBACKEND", "Agg")
    monkeypatch.setenv("PLOT_BACKEND", "Agg")
    monkeypatch.setenv("MPLCONFIGDIR", str(tmp_path / "mplconfig"))


@pytest.fixture
def project_root() -> Path:
    return Path(__file__).resolve().parents[1]

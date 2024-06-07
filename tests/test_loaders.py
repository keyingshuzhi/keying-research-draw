from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from src.loaders.data_loader import (
    auto_sep,
    parse_group_arg,
    parse_label_list,
    parse_numeric_list,
    parse_size_range,
    read_dataframe,
)


def test_auto_sep():
    assert auto_sep(Path("x.csv"), None) == ","
    assert auto_sep(Path("x.tsv"), None) == "\t"
    assert auto_sep(Path("x.txt"), None) == "\t"
    assert auto_sep(Path("x.any"), None) == ","
    assert auto_sep(Path("x.csv"), ";") == ";"


def test_parse_helpers():
    np.testing.assert_allclose(parse_numeric_list("1, 2, 3"), np.array([1.0, 2.0, 3.0]))
    np.testing.assert_allclose(parse_numeric_list("[1,2,3]"), np.array([1.0, 2.0, 3.0]))
    assert parse_label_list("a,b,c") == ["a", "b", "c"]
    assert parse_label_list('["x","y"]') == ["x", "y"]
    assert parse_size_range("180,24") == (24.0, 180.0)
    assert parse_size_range("bad") == (24.0, 160.0)
    label, arr = parse_group_arg("Ctrl: 1,2,3")
    assert label == "Ctrl"
    np.testing.assert_allclose(arr, np.array([1.0, 2.0, 3.0]))


def test_read_dataframe_csv(tmp_path):
    pd = pytest.importorskip("pandas")
    file = tmp_path / "demo.csv"
    file.write_text("x,y\n1,2\n3,4\n", encoding="utf-8")
    df = read_dataframe(file, ",")
    assert list(df.columns) == ["x", "y"]
    assert df.shape == (2, 2)
    assert pd.api.types.is_numeric_dtype(df["x"])


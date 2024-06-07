from __future__ import annotations

import numpy as np

from src.util.stats_utils import StatsUtils


def test_pearson_uses_pairwise_finite_samples():
    x = np.array([1.0, 2.0, np.nan, 4.0, 5.0])
    y = np.array([1.0, 2.0, 3.0, 4.0, np.nan])
    res = StatsUtils.pearson_r_p(x, y)

    # 有效配对样本应是索引 0/1/3，共 3 对
    assert res.n == 3
    assert np.isclose(res.r, 1.0)
    assert res.method in {"scipy", "approx"}


def test_pearson_invalid_when_input_lengths_mismatch():
    res = StatsUtils.pearson_r_p([1, 2, 3], [1, 2])
    assert res.method == "invalid"
    assert np.isnan(res.r)


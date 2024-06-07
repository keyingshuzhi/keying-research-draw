from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List, Optional, Tuple

import numpy as np

from src.util.dependency_hints import format_missing_dependency


def auto_sep(path: Path, sep_opt: Optional[str]) -> str:
    if sep_opt:
        return sep_opt
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return ","
    if suffix in {".tsv", ".txt"}:
        return "\t"
    return ","


def read_dataframe(path: Path, sep: str):
    try:
        import pandas as pd  # type: ignore
    except Exception as e:
        raise RuntimeError(
            format_missing_dependency(
                package="pandas",
                feature="文件模式读取",
                recommended_extra="data",
            )
        ) from e
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    return pd.read_csv(path, sep=sep)


def parse_numeric_list(raw: str) -> np.ndarray:
    text = raw.strip().strip(",")
    if text.startswith("[") and text.endswith("]"):
        try:
            return np.asarray(json.loads(text), dtype=float)
        except Exception:
            pass
    if "," in text:
        parts = [p.strip() for p in text.split(",") if p.strip()]
    else:
        parts = [p.strip() for p in text.split() if p.strip()]
    return np.asarray([float(x) for x in parts], dtype=float)


def parse_label_list(raw: str) -> List[str]:
    text = raw.strip().strip(",")
    if text.startswith("[") and text.endswith("]"):
        try:
            return [str(x) for x in json.loads(text)]
        except Exception:
            pass
    if "," in text:
        parts = [p.strip() for p in text.split(",") if p.strip()]
    else:
        parts = [p.strip() for p in text.split() if p.strip()]
    return [str(x) for x in parts]


def parse_csv_list(raw: Optional[str]) -> Optional[List[str]]:
    if not raw:
        return None
    return [x.strip() for x in raw.split(",") if x.strip()]


def parse_size_range(raw: Optional[str]) -> Tuple[float, float]:
    if not raw:
        return (24.0, 160.0)
    parts = [t.strip() for t in raw.split(",") if t.strip()]
    if len(parts) != 2:
        return (24.0, 160.0)
    try:
        left, right = float(parts[0]), float(parts[1])
        if left > right:
            left, right = right, left
        return (left, right)
    except Exception:
        return (24.0, 160.0)


def load_custom_json(args) -> Optional[Any]:
    if getattr(args, "custom_json", None):
        text = args.custom_json
    elif getattr(args, "custom_json_file", None):
        path = Path(args.custom_json_file).expanduser().resolve()
        text = path.read_text(encoding="utf-8")
    else:
        return None
    return json.loads(text)


def df_from_custom_data(data: Any):
    try:
        import pandas as pd  # type: ignore
    except Exception as e:
        raise RuntimeError(
            format_missing_dependency(
                package="pandas",
                feature="自定义 JSON 转 DataFrame",
                recommended_extra="data",
            )
        ) from e
    if isinstance(data, list):
        return pd.DataFrame(data)
    if isinstance(data, dict):
        return pd.DataFrame(data)
    raise ValueError("custom JSON 需为 list[dict] 或 dict[list]")


def pick_col(df, candidates: List[str]) -> str:
    for col in candidates:
        if col in df.columns:
            return col
    lower = {str(c).lower(): c for c in df.columns}
    for col in candidates:
        key = str(col).lower()
        if key in lower:
            return lower[key]
    raise KeyError(f"列未找到：{candidates}；实际列：{list(df.columns)[:12]} ...")


def parse_group_arg(arg: str) -> Tuple[str, np.ndarray]:
    if ":" not in arg:
        raise ValueError(f"--group 参数缺少冒号分隔：{arg}")
    label, values = arg.split(":", 1)
    return label.strip(), parse_numeric_list(values)


def read_points_from_table(file: Path, lon_col: str, lat_col: str):
    try:
        import geopandas as gpd  # type: ignore
        import pandas as pd  # type: ignore
    except Exception as e:
        raise RuntimeError(
            format_missing_dependency(
                package="geopandas",
                feature="地图点位表格读取",
                recommended_extra="maps",
                fallback_pip="pip install geopandas shapely pandas",
            )
        ) from e

    if file.suffix.lower() in {".xlsx", ".xls"}:
        df = pd.read_excel(file)
    elif file.suffix.lower() in {".tsv", ".txt"}:
        df = pd.read_csv(file, sep="\t")
    else:
        df = pd.read_csv(file)

    if lon_col not in df.columns or lat_col not in df.columns:
        raise KeyError(f"找不到经纬度列：{lon_col}, {lat_col}；实际列：{list(df.columns)[:12]} ...")

    df = df.dropna(subset=[lon_col, lat_col])
    return gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df[lon_col].astype(float), df[lat_col].astype(float)),
        crs="EPSG:4326",
    )


from __future__ import annotations

from argparse import Namespace

from src.registry import (
    is_3d_dispatch_key,
    is_extended_plot_key,
    is_map_dispatch_key,
    normalize_mode as _normalize_mode,
    normalize_plot_name as _normalize_plot_name,
)


def normalize_plot_name(name: str) -> str:
    return _normalize_plot_name(name)


def normalize_mode(name: str) -> str:
    return _normalize_mode(name)


def is_map_plot(plot_key: str) -> bool:
    return is_map_dispatch_key(plot_key)


def is_3d_plot(plot_key: str) -> bool:
    return is_3d_dispatch_key(plot_key)


def is_extended_plot(plot_key: str) -> bool:
    return is_extended_plot_key(plot_key)


def apply_plot_side_effects(args: Namespace) -> None:
    raw_plot = str(args.plot).lower()
    if raw_plot in {"pca", "umap"} and not getattr(args, "embed_method", None):
        args.embed_method = raw_plot
    if raw_plot == "pr" and not getattr(args, "curve", None):
        args.curve = "pr"
    if raw_plot == "ftir" and not getattr(args, "invert_x", False):
        args.invert_x = True

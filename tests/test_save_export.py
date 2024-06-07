from __future__ import annotations

import argparse

from src.save.export import autosave_name, resolve_match_screen


def test_autosave_name_prefers_title():
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    ax.set_title("My Figure")
    assert autosave_name(fig, None, "box", None) == "My_Figure"
    plt.close(fig)


def test_resolve_match_screen_flags():
    args = argparse.Namespace(match_screen=False, no_match_screen=False)
    assert resolve_match_screen(args) is True
    args.match_screen = True
    assert resolve_match_screen(args) is True
    args.no_match_screen = True
    assert resolve_match_screen(args) is False

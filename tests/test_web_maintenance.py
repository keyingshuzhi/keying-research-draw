from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from web.backend import app as web_app


def _write_file(path: Path, *, size: int, mtime: float) -> None:
    path.write_bytes(b"x" * size)
    os.utime(path, (mtime, mtime))


def test_cleanup_directory_enforces_total_bytes(tmp_path: Path) -> None:
    now = time.time()
    newest = tmp_path / "newest.bin"
    middle = tmp_path / "middle.bin"
    oldest = tmp_path / "oldest.bin"

    _write_file(newest, size=120, mtime=now - 1)
    _write_file(middle, size=100, mtime=now - 2)
    _write_file(oldest, size=90, mtime=now - 3)

    result = web_app._cleanup_directory(
        tmp_path,
        max_files=10,
        retention_seconds=3600,
        max_total_bytes=200,
    )

    assert result["before_files"] == 3
    assert result["before_bytes"] == 310
    assert result["after_files"] == 1
    assert result["after_bytes"] <= 200
    assert newest.exists()
    assert not middle.exists()
    assert not oldest.exists()


def test_upload_list_supports_pagination(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    now = time.time()
    for i in range(7):
        _write_file(tmp_path / f"u{i}.csv", size=i + 1, mtime=now - i)

    monkeypatch.setattr(web_app, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(web_app, "UPLOAD_MAX_TOTAL_BYTES", 9999)

    resp = web_app.list_upload_files(page=2, page_size=3)
    assert resp.page == 2
    assert resp.page_size == 3
    assert resp.total == 7
    assert resp.total_pages == 3
    assert resp.has_next is True
    assert len(resp.items) == 3
    assert resp.usage_bytes == sum(range(1, 8))
    assert resp.quota_bytes == 9999


def test_render_list_supports_pagination(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    now = time.time()
    for i in range(7):
        _write_file(tmp_path / f"r{i}.png", size=10 + i, mtime=now - i)

    monkeypatch.setattr(web_app, "RENDER_DIR", tmp_path)
    monkeypatch.setattr(web_app, "RENDER_MAX_TOTAL_BYTES", 4096)

    resp = web_app.list_render_files(page=3, page_size=3)
    assert resp.page == 3
    assert resp.page_size == 3
    assert resp.total == 7
    assert resp.total_pages == 3
    assert resp.has_next is False
    assert len(resp.items) == 1
    assert resp.usage_bytes == sum(10 + i for i in range(7))
    assert resp.quota_bytes == 4096

"""Tests for configuration management."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from cubemcp.config import get_repo_path


def test_repo_path_from_env(tmp_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CUBESOLVE_REPO_PATH", str(tmp_repo))
    assert get_repo_path() == tmp_repo


def test_repo_path_explicit_override(tmp_repo: Path) -> None:
    assert get_repo_path(str(tmp_repo)) == tmp_repo


def test_repo_path_not_found(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("CUBESOLVE_REPO_PATH", raising=False)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(FileNotFoundError):
        get_repo_path()

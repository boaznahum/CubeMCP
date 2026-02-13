"""Shared test fixtures for CubeMCP."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest


@pytest.fixture
def tmp_repo(tmp_path: Path) -> Path:
    """Create a minimal fake CubeSolve repo for testing."""
    repo = tmp_path / "cubesolve"
    repo.mkdir()
    (repo / "pyproject.toml").write_text(
        '[project]\nname = "cubesolve"\nversion = "0.1.0"\nrequires-python = ">=3.10"\n'
    )
    (repo / "README.md").write_text("# CubeSolve\nA Rubik's Cube solver.\n")
    (repo / "arch.md").write_text("# Architecture\nLayered design.\n")

    src = repo / "src" / "cube"
    src.mkdir(parents=True)
    (src / "__init__.py").write_text("")

    solver_dir = src / "domain" / "solver"
    solver_dir.mkdir(parents=True)
    (solver_dir / "__init__.py").write_text("")
    (solver_dir / "Solvers.py").write_text(
        'class Solvers:\n    """Solver factory."""\n    pass\n'
    )

    tests_dir = repo / "tests"
    tests_dir.mkdir()
    (tests_dir / "TESTING.md").write_text("# Testing\nRun with pytest.\n")

    return repo


@pytest.fixture
def mock_repo_env(tmp_repo: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Set CUBESOLVE_REPO_PATH to the fake repo."""
    monkeypatch.setenv("CUBESOLVE_REPO_PATH", str(tmp_repo))
    return tmp_repo

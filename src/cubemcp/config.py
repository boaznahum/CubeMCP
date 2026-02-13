"""Configuration management for CubeMCP."""

from __future__ import annotations

import json
import os
from pathlib import Path


def get_data_dir() -> Path:
    """Return the CubeMCP data directory (~/.cubemcp), creating it if needed."""
    data_dir = Path.home() / ".cubemcp"
    data_dir.mkdir(exist_ok=True)
    return data_dir


def get_repo_path(override: str | None = None) -> Path:
    """Resolve the CubeSolve repository path.

    Priority order:
    1. Explicit override parameter
    2. CUBESOLVE_REPO_PATH environment variable
    3. Config file (~/.cubemcp/config.json)
    4. Auto-detect in common locations
    """
    # 1. Explicit override
    if override:
        p = Path(override).expanduser().resolve()
        if p.is_dir():
            return p
        raise FileNotFoundError(f"CubeSolve repo not found at: {p}")

    # 2. Environment variable
    env_path = os.environ.get("CUBESOLVE_REPO_PATH")
    if env_path:
        p = Path(env_path).expanduser().resolve()
        if p.is_dir():
            return p

    # 3. Config file
    config_file = get_data_dir() / "config.json"
    if config_file.exists():
        config = json.loads(config_file.read_text())
        if "repo_path" in config:
            p = Path(config["repo_path"]).expanduser().resolve()
            if p.is_dir():
                return p

    # 4. Auto-detect
    candidates = [
        Path.home() / "cubesolve",
        Path.home() / "CubeSolve",
        Path.cwd().parent / "cubesolve",
        Path.cwd().parent / "CubeSolve",
    ]
    for candidate in candidates:
        if candidate.is_dir() and (candidate / "pyproject.toml").exists():
            return candidate.resolve()

    raise FileNotFoundError(
        "CubeSolve repository not found. Set CUBESOLVE_REPO_PATH or pass --repo."
    )

"""Repository scanner — walks CubeSolve and extracts structured knowledge."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _checkout_branch(repo_path: Path, branch: str) -> str:
    """Check out a specific branch in the CubeSolve repo.

    Returns the previous branch/ref so it can be restored if needed.
    """
    # Remember current branch
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=str(repo_path),
        capture_output=True,
        text=True,
    )
    previous = result.stdout.strip() if result.returncode == 0 else "main"

    # Fetch the branch from origin
    subprocess.run(
        ["git", "fetch", "origin", branch],
        cwd=str(repo_path),
        capture_output=True,
        text=True,
        timeout=60,
    )

    # Check out the branch
    result = subprocess.run(
        ["git", "checkout", branch],
        cwd=str(repo_path),
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        # Try as remote tracking branch
        result = subprocess.run(
            ["git", "checkout", "-b", branch, f"origin/{branch}"],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Failed to checkout branch '{branch}': {result.stderr.strip()}"
            )

    return previous


def _get_current_branch(repo_path: Path) -> str:
    """Get the currently checked-out branch name."""
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=str(repo_path),
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def scan_repo(repo_path: Path, branch: str | None = None) -> dict:
    """Scan the CubeSolve repository and return a structured knowledge dict.

    Args:
        repo_path: Path to the CubeSolve repository.
        branch: Optional git branch to checkout before scanning.
                If None, scans whatever is currently checked out.
    """
    previous_branch = None
    if branch:
        previous_branch = _checkout_branch(repo_path, branch)

    current_branch = _get_current_branch(repo_path)

    knowledge: dict = {
        "repo_path": str(repo_path),
        "branch": current_branch,
        "project": {},
        "solvers": [],
        "cli": {},
        "architecture": "",
        "test_info": {},
        "modules": [],
    }

    # --- pyproject.toml ---
    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists():
        text = pyproject.read_text()
        knowledge["project"]["pyproject_summary"] = _extract_pyproject_info(text)

    # --- README ---
    readme = repo_path / "README.md"
    if readme.exists():
        knowledge["project"]["readme"] = _truncate(readme.read_text(), 5000)

    # --- Architecture doc ---
    arch = repo_path / "arch.md"
    if arch.exists():
        knowledge["architecture"] = _truncate(arch.read_text(), 8000)

    # --- Solvers ---
    solver_dir = repo_path / "src" / "cube" / "domain" / "solver"
    if solver_dir.exists():
        knowledge["solvers"] = _scan_solvers(solver_dir)

    # --- CLI / Running info ---
    running_md = repo_path / "src" / "cube" / "RUNNING.md"
    if running_md.exists():
        knowledge["cli"]["running_guide"] = _truncate(running_md.read_text(), 3000)

    # --- Test info ---
    testing_md = repo_path / "tests" / "TESTING.md"
    if testing_md.exists():
        knowledge["test_info"]["testing_guide"] = _truncate(testing_md.read_text(), 3000)

    # --- Module map ---
    src_dir = repo_path / "src" / "cube"
    if src_dir.exists():
        knowledge["modules"] = _scan_modules(src_dir)

    return knowledge


def _extract_pyproject_info(text: str) -> str:
    """Extract key info from pyproject.toml text."""
    lines = []
    for line in text.split("\n"):
        stripped = line.strip()
        if any(stripped.startswith(k) for k in [
            "name", "version", "description", "requires-python",
            "dependencies", "testpaths",
        ]):
            lines.append(stripped)
    return "\n".join(lines[:20])


def _scan_solvers(solver_dir: Path) -> list[dict]:
    """Find solver classes and extract their names/descriptions."""
    solvers = []
    for py_file in sorted(solver_dir.rglob("*.py")):
        if py_file.name.startswith("_") and py_file.name != "__init__.py":
            continue
        text = py_file.read_text(errors="replace")
        if "class " in text and ("Solver" in text or "solver" in py_file.name.lower()):
            solvers.append({
                "file": str(py_file.relative_to(solver_dir.parent.parent.parent)),
                "name": py_file.stem,
                "preview": _truncate(text, 500),
            })
    return solvers[:20]  # Cap at 20


def _scan_modules(src_dir: Path) -> list[dict]:
    """Build a module map of the source tree."""
    modules = []
    for init_file in sorted(src_dir.rglob("__init__.py")):
        pkg_dir = init_file.parent
        py_files = [f.name for f in pkg_dir.glob("*.py") if f.name != "__init__.py"]
        modules.append({
            "package": str(pkg_dir.relative_to(src_dir.parent)),
            "files": py_files[:15],
        })
    return modules[:30]


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len] + "\n... (truncated)"


def run_relearn(repo_path: str | None = None, branch: str | None = None) -> None:
    """CLI entry point for relearn command.

    Args:
        repo_path: Path to the CubeSolve repo (None = auto-detect).
        branch: Git branch to checkout before scanning (None = current branch).
    """
    from cubemcp.config import get_repo_path
    from cubemcp.knowledge.store import KnowledgeStore

    path = get_repo_path(repo_path)
    if branch:
        print(f"Scanning CubeSolve at {path} (branch: {branch})...", file=sys.stderr)
    else:
        print(f"Scanning CubeSolve at {path} (current branch)...", file=sys.stderr)

    knowledge = scan_repo(path, branch=branch)

    store = KnowledgeStore()
    store.save(knowledge)

    print(f"Knowledge base updated: {store.knowledge_file}", file=sys.stderr)
    print(f"Branch: {knowledge.get('branch', 'unknown')}", file=sys.stderr)
    print(store.summary(), file=sys.stderr)

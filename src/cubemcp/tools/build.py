"""Build, test, and run tools for CubeSolve."""

from __future__ import annotations

import subprocess

from mcp.server.fastmcp import Context, FastMCP

from cubemcp.config import get_repo_path


def register_build_tools(mcp: FastMCP) -> None:

    @mcp.tool()
    async def cubesolve_build(ctx: Context, clean: bool = False) -> str:
        """Build and install the CubeSolve project using uv sync.

        Args:
            clean: If True, remove .venv first and do a clean install.
        """
        repo = get_repo_path()
        await ctx.info(f"Building CubeSolve at {repo}")

        if clean:
            venv = repo / ".venv"
            if venv.exists():
                subprocess.run(["rm", "-rf", str(venv)], check=True)

        result = subprocess.run(
            ["uv", "sync"],
            cwd=str(repo),
            capture_output=True,
            text=True,
            timeout=120,
        )

        output = result.stdout + result.stderr
        if result.returncode != 0:
            return f"Build FAILED (exit {result.returncode}):\n{output}"
        return f"Build OK:\n{output}"

    @mcp.tool()
    async def cubesolve_test(
        ctx: Context,
        filter: str = "",
        verbose: bool = False,
        marker: str = "",
    ) -> str:
        """Run the CubeSolve test suite.

        Args:
            filter: pytest -k filter expression (e.g. 'scramble' or 'test_lbl').
            verbose: If True, run with -v flag.
            marker: pytest -m marker expression (e.g. 'not slow').
        """
        repo = get_repo_path()
        await ctx.info(f"Running tests in {repo}")

        cmd = ["uv", "run", "pytest"]
        if verbose:
            cmd.append("-v")
        if filter:
            cmd.extend(["-k", filter])
        if marker:
            cmd.extend(["-m", marker])

        result = subprocess.run(
            cmd,
            cwd=str(repo),
            capture_output=True,
            text=True,
            timeout=300,
        )

        output = result.stdout + result.stderr
        status = "PASSED" if result.returncode == 0 else f"FAILED (exit {result.returncode})"
        return f"Tests {status}:\n{output[-3000:]}"  # Truncate to last 3000 chars

    @mcp.tool()
    async def cubesolve_run(
        ctx: Context,
        backend: str = "headless",
        cube_size: int = 3,
        commands: str = "",
    ) -> str:
        """Launch CubeSolve with specified options.

        Args:
            backend: Rendering backend (headless, pyglet2, tkinter, console, web).
            cube_size: Cube dimension (3 for 3x3, 4 for 4x4, etc.).
            commands: Comma-separated command sequence (e.g. 'SCRAMBLE_1,SOLVE_ALL,QUIT').
        """
        repo = get_repo_path()
        await ctx.info(f"Running CubeSolve (backend={backend}, size={cube_size})")

        cmd = [
            "uv", "run", "python", "-m", "cube.main_any_backend",
            f"--backend={backend}",
            f"--cube-size={cube_size}",
        ]
        if commands:
            cmd.append(f"--commands={commands}")

        result = subprocess.run(
            cmd,
            cwd=str(repo),
            capture_output=True,
            text=True,
            timeout=60,
            env={**__import__("os").environ, "PYTHONPATH": str(repo / "src")},
        )

        output = result.stdout + result.stderr
        if result.returncode != 0:
            return f"Run FAILED (exit {result.returncode}):\n{output[-3000:]}"
        return f"Run OK:\n{output[-3000:]}"

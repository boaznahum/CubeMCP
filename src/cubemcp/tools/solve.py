"""Cube-solving tools — scramble, solve, list solvers."""

from __future__ import annotations

import subprocess
import sys

from mcp.server.fastmcp import Context, FastMCP

from cubemcp.config import get_repo_path


def _cubesolve_python_cmd() -> list[str]:
    """Return the command prefix to run Python with CubeSolve on sys.path."""
    repo = get_repo_path()
    return ["uv", "run", "--directory", str(repo), "python"]


def register_solve_tools(mcp: FastMCP) -> None:

    @mcp.tool()
    async def cube_list_solvers(ctx: Context) -> str:
        """List all available solving algorithms in CubeSolve with descriptions."""
        repo = get_repo_path()
        await ctx.info("Listing available solvers")

        script = """\
import sys
sys.path.insert(0, 'src')
from cube.domain.solver.Solvers import Solvers
for name, info in Solvers.all_solvers_info().items():
    print(f"- {name}: {info}")
"""
        result = subprocess.run(
            ["uv", "run", "python", "-c", script],
            cwd=str(repo),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            # Fallback: return known solvers from knowledge base
            return (
                "Available solvers (from knowledge base):\n"
                "- LBL (Beginner Layer-By-Layer): Simple, visual approach\n"
                "- CFOP (Fridrich method): Advanced, faster\n"
                "- Kociemba: Near-optimal (18-22 moves for 3x3)\n"
                "- Cage: For big cubes (4x4+)\n"
                f"\n(Dynamic query failed: {result.stderr[:500]})"
            )
        return f"Available solvers:\n{result.stdout}"

    @mcp.tool()
    async def cube_scramble(
        ctx: Context,
        size: int = 3,
        seed: int = 1,
    ) -> str:
        """Scramble a virtual cube and return its state.

        Args:
            size: Cube dimension (3 for 3x3).
            seed: Random seed for reproducible scrambles.
        """
        repo = get_repo_path()
        await ctx.info(f"Scrambling {size}x{size} cube (seed={seed})")

        script = f"""\
import sys
sys.path.insert(0, 'src')
from cube.application.AbstractApp import AbstractApp
app = AbstractApp.create_non_default(cube_size={size}, animation=False)
app.scramble(seed={seed}, n_moves=None, animation=False, verbose=False)
print(app.cube)
"""
        result = subprocess.run(
            ["uv", "run", "python", "-c", script],
            cwd=str(repo),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return f"Scramble failed:\n{result.stderr[:1000]}"
        return f"Scrambled {size}x{size} cube (seed={seed}):\n{result.stdout}"

    @mcp.tool()
    async def cube_solve(
        ctx: Context,
        size: int = 3,
        solver: str = "LBL",
        seed: int = 1,
    ) -> str:
        """Scramble and solve a cube, returning the move sequence.

        Args:
            size: Cube dimension (3 for 3x3).
            solver: Solver algorithm name (LBL, CFOP, Kociemba).
            seed: Random seed for the scramble (for reproducibility).
        """
        repo = get_repo_path()
        await ctx.info(f"Solving {size}x{size} cube with {solver} (seed={seed})")
        await ctx.report_progress(0, 3)

        script = f"""\
import sys
sys.path.insert(0, 'src')
from cube.application.AbstractApp import AbstractApp
from cube.domain.solver import Solvers

app = AbstractApp.create_non_default(cube_size={size}, animation=False)
app.scramble(seed={seed}, n_moves=None, animation=False, verbose=False)

solver = Solvers.by_name("{solver}", app.op)
print(f"Scrambled: {{not solver.is_solved}}")
solver.solve(debug=False, animation=False)
print(f"Solved: {{solver.is_solved}}")
"""
        await ctx.report_progress(1, 3)

        result = subprocess.run(
            ["uv", "run", "python", "-c", script],
            cwd=str(repo),
            capture_output=True,
            text=True,
            timeout=60,
        )
        await ctx.report_progress(3, 3)

        if result.returncode != 0:
            return f"Solve failed:\n{result.stderr[:1500]}"
        return f"Solve result ({solver} on {size}x{size}, seed={seed}):\n{result.stdout}"

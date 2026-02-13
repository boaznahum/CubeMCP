"""Codebase search tool for CubeSolve."""

from __future__ import annotations

import subprocess

from mcp.server.fastmcp import Context, FastMCP

from cubemcp.config import get_repo_path


def register_search_tools(mcp: FastMCP) -> None:

    @mcp.tool()
    async def cubesolve_search(
        ctx: Context,
        query: str,
        file_pattern: str = "*.py",
        max_results: int = 20,
    ) -> str:
        """Search the CubeSolve codebase for a pattern.

        Args:
            query: Search term or regex pattern.
            file_pattern: Glob pattern to filter files (default: *.py).
            max_results: Maximum number of matching files to return.
        """
        repo = get_repo_path()
        await ctx.info(f"Searching CubeSolve for '{query}' in {file_pattern}")

        cmd = [
            "grep", "-r", "--include", file_pattern,
            "-l", "-n", query, str(repo / "src"),
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 1:  # No matches
            return f"No matches found for '{query}' in {file_pattern}"
        if result.returncode != 0:
            return f"Search error:\n{result.stderr[:500]}"

        lines = result.stdout.strip().split("\n")
        truncated = lines[:max_results]
        output = "\n".join(truncated)
        suffix = f"\n... and {len(lines) - max_results} more" if len(lines) > max_results else ""
        return f"Matches for '{query}':\n{output}{suffix}"

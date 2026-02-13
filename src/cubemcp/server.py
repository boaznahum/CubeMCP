"""CubeMCP FastMCP server — registers all tools, resources, and prompts."""

from __future__ import annotations

import os

from mcp.server.fastmcp import FastMCP

from cubemcp.config import get_repo_path

mcp = FastMCP(
    "CubeMCP",
    instructions="MCP server for CubeSolve — build, test, run, and solve Rubik's cubes",
)

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

from cubemcp.tools.build import register_build_tools
from cubemcp.tools.solve import register_solve_tools
from cubemcp.tools.search import register_search_tools
from cubemcp.tools.relearn import register_relearn_tools

register_build_tools(mcp)
register_solve_tools(mcp)
register_search_tools(mcp)
register_relearn_tools(mcp)

# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

from cubemcp.resources.knowledge import register_resources

register_resources(mcp)

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

from cubemcp.prompts.templates import register_prompts

register_prompts(mcp)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run_server(repo_path: str | None = None) -> None:
    """Start the MCP server with stdio transport."""
    if repo_path:
        os.environ["CUBESOLVE_REPO_PATH"] = repo_path
    # Validate repo path is reachable at startup
    try:
        path = get_repo_path(repo_path)
        import sys
        print(f"CubeMCP: CubeSolve repo at {path}", file=sys.stderr)
    except FileNotFoundError as e:
        import sys
        print(f"CubeMCP warning: {e}", file=sys.stderr)

    mcp.run(transport="stdio")

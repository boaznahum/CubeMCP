"""Tests for the MCP server — tool listing and resource access."""

from __future__ import annotations

import pytest

from cubemcp.server import mcp


@pytest.mark.asyncio
async def test_server_has_tools() -> None:
    """Verify all expected tools are registered."""
    result = await mcp.list_tools()
    tool_names = [t.name for t in result]

    expected = [
        "cubesolve_build",
        "cubesolve_test",
        "cubesolve_run",
        "cube_list_solvers",
        "cube_scramble",
        "cube_solve",
        "cubesolve_search",
    ]
    for name in expected:
        assert name in tool_names, f"Missing tool: {name}"


@pytest.mark.asyncio
async def test_server_has_resources() -> None:
    """Verify all expected resources are registered."""
    result = await mcp.list_resources()
    uris = [str(r.uri) for r in result]

    expected_uris = [
        "cubesolve://architecture",
        "cubesolve://solvers",
        "cubesolve://commands",
        "cubesolve://knowledge",
    ]
    for uri in expected_uris:
        assert uri in uris, f"Missing resource: {uri}"


@pytest.mark.asyncio
async def test_server_has_prompts() -> None:
    """Verify all expected prompts are registered."""
    result = await mcp.list_prompts()
    prompt_names = [p.name for p in result]

    expected = ["solve_cube", "debug_solver", "explain_algorithm"]
    for name in expected:
        assert name in prompt_names, f"Missing prompt: {name}"

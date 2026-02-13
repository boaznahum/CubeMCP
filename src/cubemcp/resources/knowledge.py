"""MCP resource providers — expose CubeSolve knowledge as readable resources."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from cubemcp.knowledge.store import KnowledgeStore

_store = KnowledgeStore()


def register_resources(mcp: FastMCP) -> None:

    @mcp.resource("cubesolve://architecture")
    def architecture() -> str:
        """High-level architecture overview of the CubeSolve project."""
        return _store.get("architecture", "No architecture info. Run cubesolve_relearn first.")

    @mcp.resource("cubesolve://solvers")
    def solvers() -> str:
        """Available cube-solving algorithms and their characteristics."""
        return _store.get("solvers", "No solver info. Run cubesolve_relearn first.")

    @mcp.resource("cubesolve://commands")
    def commands() -> str:
        """CLI commands, keyboard shortcuts, and GUI reference for CubeSolve."""
        return _store.get("cli", "No CLI info. Run cubesolve_relearn first.")

    @mcp.resource("cubesolve://knowledge")
    def full_knowledge() -> str:
        """Full auto-generated knowledge base for CubeSolve."""
        return _store.get("project", "No knowledge. Run cubesolve_relearn first.")

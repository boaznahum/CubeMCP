"""Relearn tool — triggers knowledge base regeneration."""

from __future__ import annotations

from mcp.server.fastmcp import Context, FastMCP

from cubemcp.config import get_repo_path


def register_relearn_tools(mcp: FastMCP) -> None:

    @mcp.tool()
    async def cubesolve_relearn(
        ctx: Context,
        repo_path: str = "",
        branch: str = "",
    ) -> str:
        """Re-scan the CubeSolve repository and regenerate the knowledge base.

        Run this after making changes to CubeSolve so the MCP server's knowledge
        stays up to date. You can point it at a specific branch to learn from.

        Args:
            repo_path: Optional explicit path to CubeSolve repo.
            branch: Git branch to checkout and learn from (e.g. 'main', 'big-lbl-5').
                    If empty, scans whatever branch is currently checked out.
        """
        from cubemcp.knowledge.scanner import scan_repo
        from cubemcp.knowledge.store import KnowledgeStore

        path = get_repo_path(repo_path or None)
        branch_info = f" (branch: {branch})" if branch else " (current branch)"
        await ctx.info(f"Relearning from {path}{branch_info}")
        await ctx.report_progress(0, 3)

        # Scan (with optional branch checkout)
        await ctx.info("Phase 1/3: Scanning repository...")
        knowledge = scan_repo(path, branch=branch or None)
        await ctx.report_progress(1, 3)

        # Store
        await ctx.info("Phase 2/3: Saving knowledge base...")
        store = KnowledgeStore()
        store.save(knowledge)
        await ctx.report_progress(2, 3)

        # Verify
        await ctx.info("Phase 3/3: Verifying...")
        store.load()
        summary = store.summary()
        await ctx.report_progress(3, 3)

        learned_branch = knowledge.get("branch", "unknown")
        return f"Relearn complete from branch '{learned_branch}'.\n\n{summary}"

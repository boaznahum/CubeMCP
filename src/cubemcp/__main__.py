"""CLI entry point for CubeMCP."""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="cubemcp",
        description="MCP server for CubeSolve — Rubik's Cube solver and visualizer",
    )
    sub = parser.add_subparsers(dest="command")

    # serve
    serve_parser = sub.add_parser("serve", help="Start the MCP server (stdio transport)")
    serve_parser.add_argument(
        "--repo",
        default=None,
        help="Path to the CubeSolve repository (overrides CUBESOLVE_REPO_PATH env var)",
    )

    # relearn
    relearn_parser = sub.add_parser("relearn", help="Re-scan CubeSolve and update knowledge base")
    relearn_parser.add_argument(
        "--repo",
        default=None,
        help="Path to the CubeSolve repository",
    )
    relearn_parser.add_argument(
        "--branch",
        default=None,
        help="Git branch to checkout and learn from (e.g. 'main', 'big-lbl-5')",
    )

    # info
    sub.add_parser("info", help="Print current configuration and knowledge summary")

    args = parser.parse_args(argv)

    if args.command == "serve":
        from cubemcp.server import run_server

        run_server(repo_path=args.repo)

    elif args.command == "relearn":
        from cubemcp.knowledge.scanner import run_relearn

        run_relearn(repo_path=args.repo, branch=args.branch)

    elif args.command == "info":
        from cubemcp.knowledge.store import KnowledgeStore

        store = KnowledgeStore()
        store.load()
        print(store.summary(), file=sys.stderr)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

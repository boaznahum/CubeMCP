# CubeMCP — Project Specification

## Vision

Build an MCP (Model Context Protocol) server that gives Claude Code deep, actionable
knowledge of the [CubeSolve](https://github.com/boaznahum/cubesolve) repository.
Through this server, Claude Code can **build, test, run, and solve Rubik's cubes**
using the CubeSolve engine — and the server's knowledge can be updated without
redeploying it.

## Goals

| # | Goal | MVP? |
|---|------|------|
| 1 | Expose CubeSolve build, test, and run commands as MCP tools | Yes |
| 2 | Expose cube-solving capabilities (scramble, solve 3×3, list solvers) as MCP tools | Yes |
| 3 | Expose CubeSolve architecture and codebase knowledge as MCP resources/prompts | Yes |
| 4 | Provide a **relearn** mechanism — a single command that re-scans the CubeSolve repo and regenerates the knowledge base so the MCP server stays current | Yes |
| 5 | Installable via `uv` with a one-liner; binary/entry-point created by the installer | Yes |
| 6 | Support for additional cube sizes (4×4, 5×5, NxN) | Post-MVP |
| 7 | Streaming solve visualization via MCP progress reporting | Post-MVP |

## Technology Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Language | Python 3.13+ | Latest stable; matches CubeSolve |
| Package manager | `uv` | Fast, modern, single-tool workflow |
| MCP SDK | `mcp[cli] >=1.25, <2` | Official Anthropic MCP Python SDK (FastMCP) |
| Build backend | `hatchling` | Simple, standards-compliant |
| Testing | `pytest` + `pytest-asyncio` | Async MCP tests |
| Linting | `ruff` | Fast, comprehensive |
| Type checking | `pyright` | Strict mode |

## MCP Server Capabilities (MVP)

### Tools (actions Claude Code can invoke)

| Tool | Description | Parameters |
|------|-------------|------------|
| `cubesolve_build` | Build/install the CubeSolve project | `clean: bool` |
| `cubesolve_test` | Run CubeSolve test suite | `filter: str`, `verbose: bool` |
| `cubesolve_run` | Launch CubeSolve with given options | `backend: str`, `cube_size: int`, `commands: str` |
| `cube_scramble` | Scramble a virtual cube and return its state | `size: int`, `seed: int` |
| `cube_solve` | Solve a scrambled cube, return move sequence | `size: int`, `solver: str`, `seed: int` |
| `cube_list_solvers` | List available solving algorithms | — |
| `cubesolve_search` | Search the CubeSolve codebase | `query: str`, `file_pattern: str` |

### Resources (read-only data Claude Code can access)

| Resource URI | Description |
|--------------|-------------|
| `cubesolve://architecture` | High-level architecture overview |
| `cubesolve://solvers` | Available solvers and their characteristics |
| `cubesolve://commands` | CLI commands and keyboard shortcuts reference |
| `cubesolve://knowledge` | Auto-generated codebase knowledge (from relearn) |

### Prompts (reusable interaction templates)

| Prompt | Description |
|--------|-------------|
| `solve_cube` | Guide Claude through solving a cube step-by-step |
| `debug_solver` | Help debug a solver issue in CubeSolve |
| `explain_algorithm` | Explain a specific solving algorithm |

## Relearn Mechanism (CLI only)

The **relearn** system allows the MCP server to update its understanding of CubeSolve
without redeploying. Relearn is invoked **only via the CLI** — it is intentionally
not exposed as an MCP tool because it has side effects (git checkout, file scanning,
writing to disk) that should not be triggered by the client.

The client accesses the knowledge through read-only **MCP resources** instead.

**CLI usage**: `cubemcp relearn --repo /path/to/cubesolve [--branch <name>]`

**Phases**:

1. **Branch checkout**: If a branch is specified, fetches it from origin and checks it out.
2. **Scan phase**: Walks the CubeSolve repo, reading key files:
   - `README.md`, `arch.md`, `RUNNING.md`, `TESTING.md`
   - `pyproject.toml` (dependencies, entry points, test config)
   - Solver source files and their docstrings
   - Test structure and available test markers
3. **Extract phase**: Structured knowledge is extracted — solver names, CLI flags,
   architecture layers, module purposes, key classes, keyboard shortcuts.
4. **Store phase**: Knowledge is serialized to `~/.cubemcp/knowledge.json`.
5. **Serve phase**: The MCP server serves the knowledge through read-only resources
   (`cubesolve://architecture`, `cubesolve://solvers`, `cubesolve://commands`,
   `cubesolve://knowledge`). New knowledge is picked up immediately.

This means: when CubeSolve changes (new solvers, new CLI flags, refactored modules),
you run `cubemcp relearn` from the CLI, and the MCP server catches up.

## Installation & Usage

### Install from source (development)

```bash
# Clone
git clone https://github.com/boaznahum/CubeMCP.git
cd CubeMCP

# Install with uv (creates the `cubemcp` CLI entry point)
uv sync

# Run the MCP server directly (for testing)
uv run cubemcp serve
```

### Register with Claude Code

```bash
# Option 1: Point Claude Code at the local project
claude mcp add cubemcp -- uv run --directory /path/to/CubeMCP cubemcp serve

# Option 2: After publishing to PyPI
claude mcp add cubemcp -- uvx cubemcp serve

# Option 3: Project-scoped (.mcp.json in CubeSolve repo)
# Add to cubesolve/.mcp.json so it's always available when working on CubeSolve
```

### Verify

```bash
# List registered servers
claude mcp list

# Inside Claude Code, check connection
/mcp
```

### Relearn (CLI only)

```bash
# Current branch
uv run cubemcp relearn --repo /path/to/cubesolve

# Specific branch
uv run cubemcp relearn --repo /path/to/cubesolve --branch big-lbl-5
```

### Run tests

```bash
uv run pytest                    # All tests
uv run pytest -x                 # Stop on first failure
uv run pytest tests/test_tools.py  # Tool tests only
```

## Project Structure

```
.
├── PROJECT_SPEC.md              # This file — refined project specification
├── ARCHITECTURE.md              # MCP architecture + CubeMCP-specific design
├── README.md                    # Quick start, install, usage instructions
├── pyproject.toml               # uv/hatch project config
├── src/
│   └── cubemcp/
│       ├── __init__.py
│       ├── __main__.py          # CLI entry point (cubemcp serve / cubemcp relearn)
│       ├── server.py            # FastMCP server definition, tool/resource registration
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── build.py         # cubesolve_build, cubesolve_test, cubesolve_run
│       │   ├── solve.py         # cube_scramble, cube_solve, cube_list_solvers
│       │   └── search.py        # cubesolve_search
│       ├── resources/
│       │   ├── __init__.py
│       │   └── knowledge.py     # Resource providers (architecture, solvers, etc.)
│       ├── prompts/
│       │   ├── __init__.py
│       │   └── templates.py     # Prompt templates (solve_cube, debug_solver, etc.)
│       └── knowledge/
│           ├── __init__.py
│           ├── scanner.py       # Repo scanner — walks CubeSolve, extracts info
│           ├── store.py         # Knowledge persistence (JSON/YAML read/write)
│           └── default.json     # Bundled default knowledge (shipped with package)
├── tests/
│   ├── conftest.py
│   ├── test_tools.py            # Tool unit tests (in-memory MCP client)
│   ├── test_resources.py        # Resource tests
│   ├── test_relearn.py          # Relearn mechanism tests
│   └── test_integration.py      # End-to-end stdio transport tests
└── .mcp.json                    # Example Claude Code MCP config
```

## Original Prompt (for reference)

> I want to plan a new python project based on uv and latest available python, I want
> to implement an AI mcp agent that can be used by Claude Code, this mvp will know to
> answer and activate things from CubeSolve repository, for example to build and use it
> to solve a 3x3 cube, I want a way that allows me to improve the mcp dynamics so I can
> enter the mcp project and do something that causes it to relearn. I want a Md file that
> describes in general the architecture of mcp server and the architecture of this
> specific server, then commit and push then start to implement. It is important to
> provide the instructions how to test and install the mcp. The binary of the mcp can be
> created by installer. First thing to do is to improve this prompt and put it in the new
> repository CubeMCP.

# CubeMCP

MCP server that gives [Claude Code](https://docs.anthropic.com/en/docs/claude-code)
deep, actionable knowledge of the [CubeSolve](https://github.com/boaznahum/cubesolve)
Rubik's Cube solver.

Through CubeMCP, Claude Code can **build, test, run, and solve Rubik's cubes** using
the CubeSolve engine.

## Features

- **Build & Test** — build CubeSolve, run its test suite, launch with any backend
- **Solve cubes** — scramble and solve 3x3 cubes with LBL, CFOP, or Kociemba
- **Search codebase** — grep through CubeSolve source files
- **Relearn** — re-scan CubeSolve when it changes; no redeployment needed
- **Knowledge base** — architecture, solver details, CLI reference as MCP resources

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- [CubeSolve](https://github.com/boaznahum/cubesolve) cloned locally

## Installation

### From source (development)

```bash
git clone https://github.com/boaznahum/CubeMCP.git
cd CubeMCP
uv sync
```

### Register with Claude Code

```bash
# Point Claude Code at the local project
claude mcp add cubemcp -- uv run --directory /path/to/CubeMCP cubemcp serve

# Tell it where CubeSolve lives (pick one):

# Option A: Environment variable
claude mcp add cubemcp \
  --env CUBESOLVE_REPO_PATH=/path/to/cubesolve \
  -- uv run --directory /path/to/CubeMCP cubemcp serve

# Option B: Pass --repo flag
claude mcp add cubemcp \
  -- uv run --directory /path/to/CubeMCP cubemcp serve --repo /path/to/cubesolve
```

### Verify

```bash
# List registered MCP servers
claude mcp list

# Inside Claude Code, check server status
/mcp
```

### Project-scoped config (optional)

Add a `.mcp.json` file to your CubeSolve repository root so CubeMCP is always
available when working on CubeSolve:

```json
{
  "mcpServers": {
    "cubemcp": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "--directory", "/path/to/CubeMCP", "cubemcp", "serve"],
      "env": {
        "CUBESOLVE_REPO_PATH": "/path/to/cubesolve"
      }
    }
  }
}
```

## Usage

Once registered, just talk to Claude Code naturally:

- *"Build CubeSolve"* — calls `cubesolve_build`
- *"Run the CubeSolve tests"* — calls `cubesolve_test`
- *"Solve a 3x3 cube with the beginner method"* — calls `cube_solve`
- *"List the available solvers"* — calls `cube_list_solvers`
- *"Search for 'scramble' in CubeSolve"* — calls `cubesolve_search`
- *"What solvers are available?"* — reads `cubesolve://solvers` resource

## Quick Start (end-to-end)

```bash
# 1. Clone both repos
git clone https://github.com/boaznahum/CubeMCP.git
git clone https://github.com/boaznahum/cubesolve.git

# 2. Install CubeMCP
cd CubeMCP
uv sync

# 3. Run tests to verify everything works
uv run pytest -v

# 4. Do the initial relearn (teach it about CubeSolve)
uv run cubemcp relearn --repo ../cubesolve

# 5. Register with Claude Code
claude mcp add cubemcp \
  --env CUBESOLVE_REPO_PATH=$(realpath ../cubesolve) \
  -- uv run --directory $(pwd) cubemcp serve

# 6. Verify
claude mcp list

# 7. Start Claude Code and use it!
# Try: "solve a 3x3 cube", "run cubesolve tests", "search for scramble"
```

## Relearn (CLI only)

When CubeSolve changes (new solvers, refactored modules, updated CLI), update
CubeMCP's knowledge by running the CLI command:

```bash
# Learn from current branch
uv run cubemcp relearn --repo /path/to/cubesolve

# Learn from a specific branch
uv run cubemcp relearn --repo /path/to/cubesolve --branch main
uv run cubemcp relearn --repo /path/to/cubesolve --branch big-lbl-5
```

This re-scans the repo, extracts structured knowledge, and updates the knowledge
base at `~/.cubemcp/knowledge.json`. The knowledge base records which branch
was scanned.

> **Design note**: Relearn is intentionally **not** exposed as an MCP tool. It has
> side effects (git checkout, file scanning, writing to disk) that should not be
> triggered by the client. Instead, the client accesses the knowledge through
> read-only **MCP resources** (`cubesolve://architecture`, `cubesolve://solvers`,
> `cubesolve://commands`, `cubesolve://knowledge`).

### How relearn works

1. **Checkout** — if `--branch` is specified, checks out that branch (fetches from
   origin first)
2. **Scan** — walks the repo reading key files: README, arch.md, pyproject.toml,
   solver source files, test structure, CLI docs
3. **Extract** — parses solver names, CLI flags, module structure, test markers
4. **Store** — saves to `~/.cubemcp/knowledge.json`; the MCP server picks up the
   new knowledge immediately via the read-only resources

## Testing

```bash
# Run all tests
uv run pytest

# Verbose
uv run pytest -v

# Specific test file
uv run pytest tests/test_server.py

# Stop on first failure
uv run pytest -x
```

## Project structure

```
.
├── PROJECT_SPEC.md          # Refined project specification
├── ARCHITECTURE.md          # MCP architecture + CubeMCP design
├── README.md                # This file
├── pyproject.toml           # Project config (uv/hatch)
├── src/cubemcp/
│   ├── __main__.py          # CLI: cubemcp serve|relearn|info
│   ├── server.py            # FastMCP server (tool/resource/prompt registration)
│   ├── config.py            # Configuration resolution
│   ├── tools/
│   │   ├── build.py         # cubesolve_build, cubesolve_test, cubesolve_run
│   │   ├── solve.py         # cube_scramble, cube_solve, cube_list_solvers
│   │   └── search.py        # cubesolve_search
│   ├── resources/
│   │   └── knowledge.py     # MCP resources (architecture, solvers, CLI, knowledge)
│   ├── prompts/
│   │   └── templates.py     # MCP prompts (solve_cube, debug_solver, explain_algorithm)
│   └── knowledge/
│       ├── scanner.py       # Repo scanner and knowledge extractor
│       ├── store.py         # Knowledge persistence (JSON)
│       └── default.json     # Bundled default knowledge
└── tests/
    ├── conftest.py          # Shared fixtures (mock CubeSolve repo)
    ├── test_config.py       # Configuration tests
    ├── test_knowledge.py    # Scanner and store tests
    └── test_server.py       # MCP server integration tests
```

## License

MIT

# CubeMCP Architecture

## Part 1: MCP Server Architecture (General)

### What is MCP?

The **Model Context Protocol (MCP)** is an open standard that defines how applications
provide context, tools, and data to Large Language Models. It follows a client-server
architecture where:

- **Host** — The LLM application (e.g., Claude Code, Claude Desktop)
- **Client** — Built into the host; manages connections to one or more MCP servers
- **Server** — Your custom process that exposes capabilities to the LLM

```
┌─────────────────────────────────────────────┐
│                  Host (Claude Code)          │
│                                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐     │
│  │ Client 1│  │ Client 2│  │ Client N│     │
│  └────┬────┘  └────┬────┘  └────┬────┘     │
│       │            │            │           │
└───────┼────────────┼────────────┼───────────┘
        │            │            │
   ┌────▼────┐  ┌────▼────┐  ┌────▼────┐
   │ Server A│  │ Server B│  │ Server C│
   │ (stdio) │  │ (stdio) │  │ (HTTP)  │
   └─────────┘  └─────────┘  └─────────┘
```

### Communication Transport

MCP supports multiple transports:

| Transport | Use Case | How It Works |
|-----------|----------|--------------|
| **stdio** | Local servers (recommended for CLI tools) | Server is spawned as a child process; JSON-RPC messages over stdin/stdout |
| **Streamable HTTP** | Remote/production servers | HTTP POST/GET with optional SSE streaming |
| **SSE** | Legacy remote | Server-Sent Events (deprecated in favor of Streamable HTTP) |

For CubeMCP, we use **stdio** — Claude Code spawns the server as a subprocess and
communicates via JSON-RPC over stdin/stdout.

### Three Primitives

MCP servers expose three types of capabilities:

#### 1. Tools (Actions)

Tools are like API endpoints that perform actions. The LLM decides when and how to call
them based on the tool's name, description, and parameter schema.

```
LLM → "call tool cube_solve with {size: 3, solver: 'LBL'}" → Server
Server → executes solve logic → returns result → LLM
```

- Can have side effects (run commands, write files)
- Parameters defined via JSON Schema (auto-generated from Python type hints)
- LLM sees tool descriptions and decides autonomously when to use them

#### 2. Resources (Data)

Resources expose read-only data through URI patterns. Think of them as GET endpoints.

```
LLM → "read resource cubesolve://architecture" → Server
Server → returns architecture text → LLM
```

- No side effects — purely informational
- Can be static or dynamic (URI templates like `cubesolve://solver/{name}`)
- LLM can read them for context before taking action

#### 3. Prompts (Templates)

Prompts are reusable interaction templates that guide how the LLM approaches a task.

```
LLM → "use prompt solve_cube with {size: 3}" → Server
Server → returns structured prompt text → LLM uses it to guide its response
```

- Define best practices for interacting with your domain
- Can include multi-step instructions, examples, constraints

### Server Lifecycle

```
1. Host spawns server process (stdio) or connects (HTTP)
2. Client sends `initialize` with protocol version and capabilities
3. Server responds with its capabilities (tools, resources, prompts)
4. Client sends `initialized` notification
5. Normal operation: tool calls, resource reads, prompt requests
6. Shutdown: client closes connection, server exits
```

### The Context Object

Inside tool/resource handlers, a `Context` object provides:
- **Logging** — `ctx.info()`, `ctx.warning()`, `ctx.error()` (sent to client, NOT stdout)
- **Progress** — `ctx.report_progress(current, total)` for long operations
- **Resource access** — read other resources from within a tool
- **Sampling** — ask the LLM a question from within the server

> **Critical rule for stdio servers**: Never write to stdout (e.g., `print()`).
> This corrupts JSON-RPC messages. Use `ctx.info()` or `print(..., file=sys.stderr)`.

---

## Part 2: CubeMCP Architecture (Specific)

### Overview

CubeMCP is an MCP server that bridges Claude Code and the CubeSolve Rubik's Cube
solver. It provides tools for building, testing, running, and solving cubes, plus
a knowledge system that stays current with the CubeSolve codebase.

```
┌──────────────────────────────────────────────────────────┐
│                     Claude Code                          │
│                                                          │
│  User: "solve a 3x3 cube using the beginner method"     │
│                                                          │
│  Claude → calls tool: cube_solve(size=3, solver="LBL")  │
│           reads resource: cubesolve://solvers            │
│                                                          │
└──────────────────────┬───────────────────────────────────┘
                       │ stdio (JSON-RPC)
                       │
┌──────────────────────▼───────────────────────────────────┐
│                    CubeMCP Server                        │
│                                                          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │                   FastMCP Core                      │ │
│  │  - Tool registration & dispatch                     │ │
│  │  - Resource serving                                 │ │
│  │  - Prompt templates                                 │ │
│  └──────────┬──────────────┬──────────────┬────────────┘ │
│             │              │              │               │
│  ┌──────────▼────┐ ┌──────▼──────┐ ┌─────▼──────────┐   │
│  │  Tool Layer   │ │  Resource   │ │   Knowledge    │   │
│  │               │ │   Layer     │ │    Engine      │   │
│  │  - build      │ │             │ │                │   │
│  │  - test       │ │  - arch     │ │  - scanner     │   │
│  │  - run        │ │  - solvers  │ │  - extractor   │   │
│  │  - scramble   │ │  - commands │ │  - store       │   │
│  │  - solve      │ │  - knowledge│ │  - relearn()   │   │
│  │  - search     │ │             │ │                │   │
│  └──────┬────────┘ └──────┬──────┘ └───────┬────────┘   │
│         │                 │                │              │
└─────────┼─────────────────┼────────────────┼──────────────┘
          │                 │                │
          ▼                 ▼                ▼
   ┌─────────────┐  ┌─────────────┐  ┌──────────────┐
   │  CubeSolve  │  │  Knowledge  │  │  CubeSolve   │
   │  (subprocess│  │  Base File  │  │  Source Code  │
   │   or import)│  │  (JSON)     │  │  (on disk)   │
   └─────────────┘  └─────────────┘  └──────────────┘
```

### Layer Descriptions

#### 1. FastMCP Core (`server.py`)

The central server definition. Creates the `FastMCP` instance, registers all tools,
resources, and prompts, and handles the server lifecycle.

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "CubeMCP",
    version="0.1.0",
    description="MCP server for CubeSolve — Rubik's Cube solver and visualizer"
)
```

#### 2. Tool Layer (`tools/`)

Each tool module groups related functionality:

- **`build.py`** — Build & development tools
  - `cubesolve_build`: Runs `uv sync` or `pip install -e .` in the CubeSolve directory
  - `cubesolve_test`: Runs `pytest` with optional filters and markers
  - `cubesolve_run`: Launches CubeSolve with specified backend/options

- **`solve.py`** — Cube-solving tools
  - `cube_scramble`: Creates a virtual cube, scrambles it, returns state
  - `cube_solve`: Solves a cube using a specified algorithm, returns moves
  - `cube_list_solvers`: Lists all available solvers with descriptions
  - These tools import CubeSolve's Python API directly (not subprocess)

- **`search.py`** — Codebase exploration
  - `cubesolve_search`: Grep-like search across CubeSolve source files

> **Note**: Relearn is intentionally not exposed as an MCP tool — it is CLI-only
> because it has side effects (git checkout, file scanning, disk writes). The client
> accesses the knowledge through the read-only Resource Layer instead.

#### 3. Resource Layer (`resources/`)

Exposes structured, read-only information to Claude Code:

- `cubesolve://architecture` — Architecture overview (from `arch.md` + extracted info)
- `cubesolve://solvers` — Solver list with descriptions, complexity, supported sizes
- `cubesolve://commands` — CLI flags, keyboard shortcuts, GUI commands
- `cubesolve://knowledge` — Full auto-generated knowledge base

Resources are populated from the knowledge base (see below).

#### 4. Knowledge Engine (`knowledge/`)

The relearn system that keeps CubeMCP current with CubeSolve changes:

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Scanner    │────▶│  Extractor   │────▶│    Store    │
│              │     │              │     │             │
│ Walks repo,  │     │ Parses files,│     │ Serializes  │
│ finds key    │     │ extracts:    │     │ to JSON,    │
│ files based  │     │ - solvers    │     │ persists to │
│ on patterns  │     │ - CLI args   │     │ disk, loads │
│              │     │ - modules    │     │ into memory │
│              │     │ - tests      │     │             │
└─────────────┘     └──────────────┘     └─────────────┘
```

**Scanner** (`scanner.py`):
- Walks the CubeSolve repository
- Identifies key files: `*.md`, `pyproject.toml`, solver source files, test files
- Reads content with size limits to avoid memory issues

**Extractor** (part of scanner):
- Parses `pyproject.toml` for entry points, dependencies, scripts
- Extracts solver names from `SolverName.py` and `Solvers.py`
- Reads docstrings from key classes
- Extracts CLI arguments from argparse definitions
- Maps test structure (directories, markers, fixtures)

**Store** (`store.py`):
- Serializes knowledge to `~/.cubemcp/knowledge.json`
- Provides in-memory access for resources and tool descriptions
- Falls back to bundled `default.json` if no knowledge file exists
- Supports atomic updates (write to temp file, then rename)

### Configuration

CubeMCP needs to know where CubeSolve lives on disk. Configuration sources
(in priority order):

1. **Environment variable**: `CUBESOLVE_REPO_PATH=/path/to/cubesolve`
2. **Config file**: `~/.cubemcp/config.json` → `{"repo_path": "/path/to/cubesolve"}`
3. **Tool parameter**: Pass `repo_path` directly to tools that need it
4. **Auto-detect**: Look for `cubesolve` in common locations (parent dir, `~/cubesolve`)

### Solving Architecture: Import vs Subprocess

CubeMCP supports two modes for interacting with CubeSolve:

| Mode | How | Pros | Cons |
|------|-----|------|------|
| **Import** (preferred) | Add CubeSolve's `src/` to `sys.path`, import directly | Fast, rich data, no serialization overhead | Tight coupling, CubeSolve must be installed |
| **Subprocess** | Run `python -m cube.main_any_backend --headless --commands=...` | Loose coupling, works with any install | Slower, text parsing required |

MVP will support both, defaulting to **import** when CubeSolve is installed in the
same Python environment, falling back to **subprocess**.

### Entry Points

The package provides a CLI entry point `cubemcp` with subcommands:

```bash
cubemcp serve              # Start MCP server (stdio transport)
cubemcp serve --http       # Start MCP server (HTTP transport, post-MVP)
cubemcp relearn            # Re-scan CubeSolve and update knowledge
cubemcp relearn --repo /x  # Specify repo path explicitly
cubemcp info               # Print current configuration and knowledge summary
```

### Testing Strategy

```
tests/
├── conftest.py              # Shared fixtures (mock CubeSolve repo, test server)
├── test_tools.py            # Each tool tested via in-memory MCP client
├── test_resources.py        # Resource content and URI routing
├── test_relearn.py          # Scanner, extractor, store — unit tests
├── test_integration.py      # Full stdio round-trip test
└── test_cli.py              # CLI subcommand tests
```

Tests use the MCP SDK's built-in test client (`server.test_client()`) for fast,
in-memory testing without spawning subprocesses.

### Security Considerations

- **No secrets in tools**: CubeMCP doesn't handle credentials; it operates on local
  files and processes only
- **Path validation**: All file paths are validated to stay within the CubeSolve repo
  (no directory traversal)
- **Subprocess safety**: Commands are constructed with lists (no shell injection);
  `shell=False` always
- **stdout discipline**: Never write to stdout in server mode (corrupts JSON-RPC)

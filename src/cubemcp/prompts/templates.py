"""MCP prompt templates for CubeSolve interactions."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP


def register_prompts(mcp: FastMCP) -> None:

    @mcp.prompt()
    def solve_cube(size: int = 3, solver: str = "LBL") -> str:
        """Guide through solving a Rubik's cube step by step."""
        return (
            f"I want to solve a {size}x{size} Rubik's cube using the {solver} method.\n\n"
            "Please:\n"
            "1. First scramble the cube using the cube_scramble tool\n"
            "2. Then solve it using the cube_solve tool\n"
            "3. Explain each solving phase and what the solver does\n"
            "4. Report the total number of moves\n\n"
            f"Use solver='{solver}' and the same seed for both scramble and solve "
            "so the results are consistent."
        )

    @mcp.prompt()
    def debug_solver(solver_name: str = "", error_description: str = "") -> str:
        """Help debug a solver issue in the CubeSolve project."""
        return (
            f"I'm debugging an issue with the {solver_name or '[solver name]'} solver "
            "in the CubeSolve project.\n\n"
            f"Error/Issue: {error_description or '[describe the error]'}\n\n"
            "Please:\n"
            "1. Use cubesolve_search to find the solver's source code\n"
            "2. Read the relevant files to understand the solver's logic\n"
            "3. Use cubesolve_test to run the solver's tests\n"
            "4. Identify the root cause and suggest a fix"
        )

    @mcp.prompt()
    def explain_algorithm(algorithm: str = "LBL") -> str:
        """Explain how a specific cube-solving algorithm works."""
        return (
            f"Please explain the {algorithm} cube-solving algorithm as implemented "
            "in the CubeSolve project.\n\n"
            "1. Read the cubesolve://architecture resource for context\n"
            "2. Use cubesolve_search to find the algorithm's source files\n"
            "3. Explain the algorithm's phases/steps\n"
            "4. Describe the key classes and methods involved\n"
            "5. Compare it to other available solvers (use cube_list_solvers)"
        )

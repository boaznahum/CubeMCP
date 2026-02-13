"""Knowledge persistence — read/write the knowledge base to disk."""

from __future__ import annotations

import json
from pathlib import Path

from cubemcp.config import get_data_dir

# Bundled default knowledge (shipped with package)
_DEFAULT_KNOWLEDGE_FILE = Path(__file__).parent / "default.json"


class KnowledgeStore:
    """Manages the CubeMCP knowledge base."""

    def __init__(self) -> None:
        self.knowledge_file = get_data_dir() / "knowledge.json"
        self._data: dict = {}

    def load(self) -> dict:
        """Load knowledge from disk. Falls back to bundled default if needed."""
        if self.knowledge_file.exists():
            self._data = json.loads(self.knowledge_file.read_text())
        elif _DEFAULT_KNOWLEDGE_FILE.exists():
            self._data = json.loads(_DEFAULT_KNOWLEDGE_FILE.read_text())
        else:
            self._data = {"_empty": True}
        return self._data

    def save(self, knowledge: dict) -> None:
        """Save knowledge to disk atomically."""
        self._data = knowledge
        tmp = self.knowledge_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(knowledge, indent=2, default=str))
        tmp.rename(self.knowledge_file)

    @property
    def data(self) -> dict:
        if not self._data:
            self.load()
        return self._data

    def get(self, key: str, default: str = "") -> str:
        val = self.data.get(key, default)
        if isinstance(val, (dict, list)):
            return json.dumps(val, indent=2, default=str)
        return str(val)

    def summary(self) -> str:
        """Human-readable summary of the knowledge base."""
        d = self.data
        if d.get("_empty"):
            return "Knowledge base is empty. Run 'cubemcp relearn' to populate it."

        lines = [
            f"Repository: {d.get('repo_path', 'unknown')}",
            f"Branch: {d.get('branch', 'unknown')}",
            f"Project: {d.get('project', {}).get('pyproject_summary', 'N/A')[:200]}",
            f"Solvers: {len(d.get('solvers', []))} found",
            f"Modules: {len(d.get('modules', []))} packages",
            f"Architecture doc: {'yes' if d.get('architecture') else 'no'}",
            f"CLI guide: {'yes' if d.get('cli', {}).get('running_guide') else 'no'}",
            f"Test guide: {'yes' if d.get('test_info', {}).get('testing_guide') else 'no'}",
        ]
        return "\n".join(lines)

"""Tests for the knowledge scanner and store."""

from __future__ import annotations

from pathlib import Path

from cubemcp.knowledge.scanner import scan_repo
from cubemcp.knowledge.store import KnowledgeStore


def test_scan_repo(tmp_repo: Path) -> None:
    knowledge = scan_repo(tmp_repo)
    assert knowledge["repo_path"] == str(tmp_repo)
    assert "pyproject_summary" in knowledge["project"]
    assert knowledge["architecture"]  # Not empty
    assert isinstance(knowledge["solvers"], list)
    assert isinstance(knowledge["modules"], list)


def test_store_save_load(tmp_repo: Path, tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("cubemcp.config.get_data_dir", lambda: tmp_path)

    knowledge = scan_repo(tmp_repo)

    store = KnowledgeStore()
    store.knowledge_file = tmp_path / "knowledge.json"
    store.save(knowledge)

    assert store.knowledge_file.exists()

    store2 = KnowledgeStore()
    store2.knowledge_file = tmp_path / "knowledge.json"
    loaded = store2.load()

    assert loaded["repo_path"] == str(tmp_repo)


def test_store_summary(tmp_repo: Path, tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("cubemcp.config.get_data_dir", lambda: tmp_path)

    knowledge = scan_repo(tmp_repo)
    store = KnowledgeStore()
    store.knowledge_file = tmp_path / "knowledge.json"
    store.save(knowledge)
    store.load()

    summary = store.summary()
    assert "Repository:" in summary


def test_store_empty_summary(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("cubemcp.config.get_data_dir", lambda: tmp_path)

    store = KnowledgeStore()
    store.knowledge_file = tmp_path / "nonexistent.json"
    store._data = {"_empty": True}

    summary = store.summary()
    assert "empty" in summary.lower()

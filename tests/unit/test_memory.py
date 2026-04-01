"""Tests for the memory system."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from claude_code.memory.find_relevant import find_relevant_memories, should_load_memory
from claude_code.memory.memdir import (
    MAX_MEMORY_INDEX_LINES,
    add_memory_to_index,
    read_memory_index,
    remove_memory_from_index,
    write_memory_index,
)
from claude_code.memory.memory_scan import parse_memory_frontmatter, scan_memory_files
from claude_code.memory.memory_types import MemoryEntry, MemoryType
from claude_code.memory.paths import generate_memory_filename, get_memory_dir


def _patch_memory_dir(tmp_path: Path):
    """Context manager to redirect memory dir to tmp_path."""
    return patch(
        "claude_code.memory.paths.get_claude_dir",
        return_value=tmp_path,
    )


class TestMemoryTypes:
    def test_memory_type_values(self) -> None:
        assert MemoryType.USER == "user"
        assert MemoryType.FEEDBACK == "feedback"
        assert MemoryType.PROJECT == "project"
        assert MemoryType.REFERENCE == "reference"

    def test_memory_entry(self) -> None:
        entry = MemoryEntry(name="test", type=MemoryType.FEEDBACK, content="rule")
        assert entry.name == "test"
        assert entry.type == "feedback"


class TestPaths:
    def test_get_memory_dir(self, tmp_path: Path) -> None:
        with _patch_memory_dir(tmp_path):
            mem_dir = get_memory_dir("/fake/project")
            assert "memory" in str(mem_dir)
            assert str(tmp_path) in str(mem_dir)

    def test_generate_filename(self) -> None:
        assert generate_memory_filename("My Rule") == "my_rule.md"
        assert generate_memory_filename("Test!@#") == "test.md"
        assert generate_memory_filename("") == "untitled.md"


class TestFrontmatter:
    def test_parse_valid(self) -> None:
        content = '---\nname: test\ndescription: A test\ntype: feedback\n---\n\nBody text'
        meta = parse_memory_frontmatter(content)
        assert meta["name"] == "test"
        assert meta["description"] == "A test"
        assert meta["type"] == "feedback"

    def test_parse_no_frontmatter(self) -> None:
        assert parse_memory_frontmatter("Just text") == {}

    def test_parse_quoted_values(self) -> None:
        content = '---\nname: "quoted name"\n---\n\nBody'
        meta = parse_memory_frontmatter(content)
        assert meta["name"] == "quoted name"


class TestMemdir:
    def test_read_empty(self, tmp_path: Path) -> None:
        with _patch_memory_dir(tmp_path):
            content = read_memory_index("/fake")
            assert content == ""

    def test_write_and_read(self, tmp_path: Path) -> None:
        with _patch_memory_dir(tmp_path):
            write_memory_index("/fake", "# Memories\n- Entry 1\n")
            content = read_memory_index("/fake")
            assert "Entry 1" in content

    def test_add_to_index(self, tmp_path: Path) -> None:
        with _patch_memory_dir(tmp_path):
            add_memory_to_index("/fake", "Rule 1", "rule_1.md", "First rule")
            content = read_memory_index("/fake")
            assert "[Rule 1](rule_1.md)" in content

    def test_remove_from_index(self, tmp_path: Path) -> None:
        with _patch_memory_dir(tmp_path):
            write_memory_index("/fake", "- [A](a.md) — desc\n- [B](b.md) — desc\n")
            remove_memory_from_index("/fake", "a.md")
            content = read_memory_index("/fake")
            assert "a.md" not in content
            assert "b.md" in content

    def test_truncation(self, tmp_path: Path) -> None:
        with _patch_memory_dir(tmp_path):
            lines = "\n".join(f"Line {i}" for i in range(300))
            write_memory_index("/fake", lines)
            content = read_memory_index("/fake")
            assert content.count("\n") <= MAX_MEMORY_INDEX_LINES


class TestMemoryScan:
    def test_scan_empty_dir(self, tmp_path: Path) -> None:
        with _patch_memory_dir(tmp_path):
            entries = scan_memory_files("/fake")
            assert entries == []

    def test_scan_with_files(self, tmp_path: Path) -> None:
        with _patch_memory_dir(tmp_path):
            mem_dir = get_memory_dir("/fake")
            mem_dir.mkdir(parents=True, exist_ok=True)
            (mem_dir / "rule.md").write_text(
                '---\nname: my rule\ndescription: test\ntype: feedback\n---\n\nContent here'
            )
            entries = scan_memory_files("/fake")
            assert len(entries) == 1
            assert entries[0].name == "my rule"
            assert entries[0].type == MemoryType.FEEDBACK


class TestFindRelevant:
    def test_empty_query_returns_all(self, tmp_path: Path) -> None:
        with _patch_memory_dir(tmp_path):
            mem_dir = get_memory_dir("/fake")
            mem_dir.mkdir(parents=True, exist_ok=True)
            (mem_dir / "a.md").write_text("---\nname: a\n---\n\nAlpha")
            (mem_dir / "b.md").write_text("---\nname: b\n---\n\nBeta")
            results = find_relevant_memories("/fake", "")
            assert len(results) == 2

    def test_keyword_match(self, tmp_path: Path) -> None:
        with _patch_memory_dir(tmp_path):
            mem_dir = get_memory_dir("/fake")
            mem_dir.mkdir(parents=True, exist_ok=True)
            (mem_dir / "py.md").write_text("---\nname: python\n---\n\nUse snake_case")
            (mem_dir / "js.md").write_text("---\nname: javascript\n---\n\nUse camelCase")
            results = find_relevant_memories("/fake", "python")
            assert len(results) == 1
            assert results[0].name == "python"

    def test_should_load(self) -> None:
        entry = MemoryEntry(description="testing patterns")
        assert should_load_memory(entry, "we need testing") is True
        assert should_load_memory(entry, "unrelated") is False

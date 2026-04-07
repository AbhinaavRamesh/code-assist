"""Comprehensive tests for filesystem tools and utilities.

Covers:
- utils/file.py (expand_path, is_binary_file, get_file_size, suggest_similar_files)
- utils/file_read.py (read_file_with_line_numbers, detect_encoding)
- utils/file_state_cache.py (FileStateCache)
- utils/file_history.py (FileHistoryEntry, FileHistoryTracker)
- tools/file_read (FileReadTool)
- tools/file_write (FileWriteTool)
- tools/file_edit (FileEditTool)
- tools/notebook_edit (NotebookEditTool)
"""

from __future__ import annotations

import json
import os
import time

import pytest

from code_assist.tools.base import DescriptionOptions, ToolResult, ToolUseContext
from code_assist.tools.file_edit.file_edit_tool import FileEditInput, FileEditTool
from code_assist.tools.file_read.file_read_tool import FileReadInput, FileReadTool
from code_assist.tools.file_write.file_write_tool import FileWriteInput, FileWriteTool
from code_assist.tools.notebook_edit.notebook_edit_tool import (
    NotebookEditInput,
    NotebookEditTool,
)
from code_assist.types.message import AssistantMessage
from code_assist.utils.file import expand_path, get_file_size, is_binary_file, suggest_similar_files
from code_assist.utils.file_history import FileAction, FileHistoryEntry, FileHistoryTracker
from code_assist.utils.file_read import detect_encoding, read_file_with_line_numbers
from code_assist.utils.file_state_cache import FileStateCache


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _noop_can_use(*a, **kw):
    return None


def _make_context(cwd: str | None = None) -> ToolUseContext:
    """Create a ToolUseContext with an optional cwd in app state."""
    if cwd is None:
        return ToolUseContext()

    class _State:
        def __init__(self, cwd_: str):
            self.cwd = cwd_

    return ToolUseContext(_get_app_state=lambda: _State(cwd))


# ===========================================================================
# utils/file.py
# ===========================================================================


class TestExpandPath:
    def test_absolute_unchanged(self) -> None:
        assert expand_path("/foo/bar", "/tmp") == "/foo/bar"

    def test_relative_resolved(self, tmp_path) -> None:
        result = expand_path("sub/file.txt", str(tmp_path))
        assert result == os.path.join(str(tmp_path), "sub", "file.txt")

    def test_tilde_expanded(self) -> None:
        result = expand_path("~/test.txt", "/tmp")
        assert result.startswith(os.path.expanduser("~"))
        assert result.endswith("test.txt")

    def test_dot_normalised(self, tmp_path) -> None:
        result = expand_path("./a/../b/file.txt", str(tmp_path))
        assert result == os.path.join(str(tmp_path), "b", "file.txt")


class TestIsBinaryFile:
    def test_text_file(self, tmp_path) -> None:
        f = tmp_path / "text.txt"
        f.write_text("Hello, world!\n")
        assert is_binary_file(str(f)) is False

    def test_binary_file(self, tmp_path) -> None:
        f = tmp_path / "bin.dat"
        f.write_bytes(b"\x00\x01\x02\x03")
        assert is_binary_file(str(f)) is True

    def test_empty_file(self, tmp_path) -> None:
        f = tmp_path / "empty"
        f.write_bytes(b"")
        assert is_binary_file(str(f)) is False

    def test_nonexistent(self) -> None:
        assert is_binary_file("/nonexistent/file") is True


class TestGetFileSize:
    def test_size(self, tmp_path) -> None:
        f = tmp_path / "data.bin"
        f.write_bytes(b"x" * 42)
        assert get_file_size(str(f)) == 42

    def test_nonexistent_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            get_file_size("/nonexistent/nope")


class TestSuggestSimilarFiles:
    def test_finds_similar(self, tmp_path) -> None:
        (tmp_path / "config.py").write_text("")
        (tmp_path / "conftest.py").write_text("")
        (tmp_path / "unrelated.txt").write_text("")

        suggestions = suggest_similar_files(
            str(tmp_path / "config.py.bak"),
            str(tmp_path),
        )
        basenames = [os.path.basename(s) for s in suggestions]
        assert "config.py" in basenames

    def test_no_dir(self) -> None:
        result = suggest_similar_files("/nonexistent/dir/file.txt", "/tmp")
        assert result == []


# ===========================================================================
# utils/file_read.py
# ===========================================================================


class TestDetectEncoding:
    def test_utf8_default(self, tmp_path) -> None:
        f = tmp_path / "plain.txt"
        f.write_text("hello")
        assert detect_encoding(str(f)) == "utf-8"

    def test_utf8_bom(self, tmp_path) -> None:
        f = tmp_path / "bom.txt"
        f.write_bytes(b"\xef\xbb\xbfhello")
        assert detect_encoding(str(f)) == "utf-8-sig"

    def test_nonexistent(self) -> None:
        assert detect_encoding("/nonexistent") == "utf-8"


class TestReadFileWithLineNumbers:
    def test_basic(self, tmp_path) -> None:
        f = tmp_path / "test.txt"
        f.write_text("alpha\nbeta\ngamma\n")
        result = read_file_with_line_numbers(str(f))
        lines = result.split("\n")
        assert len(lines) == 3
        assert "1\talpha" in lines[0]
        assert "2\tbeta" in lines[1]
        assert "3\tgamma" in lines[2]

    def test_offset(self, tmp_path) -> None:
        f = tmp_path / "test.txt"
        f.write_text("a\nb\nc\nd\ne\n")
        result = read_file_with_line_numbers(str(f), offset=2, limit=2)
        lines = result.split("\n")
        assert len(lines) == 2
        assert "3\tc" in lines[0]
        assert "4\td" in lines[1]

    def test_limit(self, tmp_path) -> None:
        f = tmp_path / "test.txt"
        f.write_text("\n".join(f"line{i}" for i in range(100)))
        result = read_file_with_line_numbers(str(f), limit=5)
        lines = result.split("\n")
        assert len(lines) == 5


# ===========================================================================
# utils/file_state_cache.py
# ===========================================================================


class TestFileStateCache:
    def test_update_and_get(self, tmp_path) -> None:
        f = tmp_path / "cached.txt"
        f.write_text("content")
        cache = FileStateCache()
        h = cache.update(str(f))
        assert len(h) == 64  # SHA-256 hex length

        entry = cache.get(str(f))
        assert entry is not None
        assert entry.content_hash == h

    def test_is_stale_after_modification(self, tmp_path) -> None:
        f = tmp_path / "stale.txt"
        f.write_text("original")
        cache = FileStateCache()
        cache.update(str(f))

        assert cache.is_stale(str(f)) is False

        # Modify the file
        time.sleep(0.05)
        f.write_text("modified")
        assert cache.is_stale(str(f)) is True

    def test_is_stale_uncached(self) -> None:
        cache = FileStateCache()
        assert cache.is_stale("/any/path") is True

    def test_invalidate(self, tmp_path) -> None:
        f = tmp_path / "inv.txt"
        f.write_text("x")
        cache = FileStateCache()
        cache.update(str(f))
        assert str(f) in cache
        cache.invalidate(str(f))
        assert str(f) not in cache

    def test_lru_eviction(self, tmp_path) -> None:
        cache = FileStateCache(max_size=3)
        files = []
        for i in range(5):
            f = tmp_path / f"file{i}.txt"
            f.write_text(f"content{i}")
            files.append(str(f))
            cache.update(str(f))

        assert len(cache) == 3
        # Oldest two should be evicted
        assert files[0] not in cache
        assert files[1] not in cache
        assert files[4] in cache

    def test_clear(self, tmp_path) -> None:
        f = tmp_path / "c.txt"
        f.write_text("x")
        cache = FileStateCache()
        cache.update(str(f))
        cache.clear()
        assert len(cache) == 0

    def test_update_with_content(self, tmp_path) -> None:
        f = tmp_path / "provided.txt"
        f.write_text("on disk")
        cache = FileStateCache()
        h = cache.update(str(f), content=b"provided content")
        entry = cache.get(str(f))
        assert entry is not None
        assert entry.content_hash == h


# ===========================================================================
# utils/file_history.py
# ===========================================================================


class TestFileHistoryTracker:
    def test_record_and_query(self) -> None:
        tracker = FileHistoryTracker()
        entry = tracker.record("/foo/bar.py", FileAction.CREATE, tool_use_id="t1")
        assert entry.path == "/foo/bar.py"
        assert entry.action == FileAction.CREATE
        assert entry.tool_use_id == "t1"
        assert len(tracker) == 1

    def test_modified_files(self) -> None:
        tracker = FileHistoryTracker()
        tracker.record("/a.py", FileAction.WRITE)
        tracker.record("/b.py", FileAction.EDIT)
        tracker.record("/a.py", FileAction.EDIT)
        assert tracker.modified_files == {"/a.py", "/b.py"}

    def test_get_entries_for(self) -> None:
        tracker = FileHistoryTracker()
        tracker.record("/a.py", FileAction.CREATE)
        tracker.record("/b.py", FileAction.WRITE)
        tracker.record("/a.py", FileAction.EDIT)
        entries = tracker.get_entries_for("/a.py")
        assert len(entries) == 2

    def test_clear(self) -> None:
        tracker = FileHistoryTracker()
        tracker.record("/x.py", FileAction.DELETE)
        tracker.clear()
        assert len(tracker) == 0
        assert tracker.modified_files == set()

    def test_entry_timestamp(self) -> None:
        before = time.time()
        entry = FileHistoryEntry(path="/t.py", action=FileAction.WRITE)
        after = time.time()
        assert before <= entry.timestamp <= after


# ===========================================================================
# FileReadTool
# ===========================================================================


class TestFileReadTool:
    @pytest.mark.asyncio
    async def test_read_file(self, tmp_path) -> None:
        f = tmp_path / "hello.txt"
        f.write_text("line1\nline2\nline3\n")

        tool = FileReadTool()
        result = await tool.call(
            FileReadInput(file_path=str(f)),
            _make_context(str(tmp_path)),
            _noop_can_use,
            AssistantMessage(),
        )
        assert "line1" in result.data
        assert "line2" in result.data
        assert "1\t" in result.data

    @pytest.mark.asyncio
    async def test_read_with_offset_limit(self, tmp_path) -> None:
        f = tmp_path / "nums.txt"
        f.write_text("\n".join(f"line{i}" for i in range(20)) + "\n")

        tool = FileReadTool()
        result = await tool.call(
            FileReadInput(file_path=str(f), offset=5, limit=3),
            _make_context(str(tmp_path)),
            _noop_can_use,
            AssistantMessage(),
        )
        lines = result.data.strip().split("\n")
        assert len(lines) == 3
        assert "line5" in lines[0]

    @pytest.mark.asyncio
    async def test_read_nonexistent(self, tmp_path) -> None:
        tool = FileReadTool()
        result = await tool.call(
            FileReadInput(file_path=str(tmp_path / "nope.txt")),
            _make_context(str(tmp_path)),
            _noop_can_use,
            AssistantMessage(),
        )
        assert "not found" in result.data.lower()

    @pytest.mark.asyncio
    async def test_read_binary(self, tmp_path) -> None:
        f = tmp_path / "bin.dat"
        f.write_bytes(b"\x00\x01\x02\x03\xff")

        tool = FileReadTool()
        result = await tool.call(
            FileReadInput(file_path=str(f)),
            _make_context(str(tmp_path)),
            _noop_can_use,
            AssistantMessage(),
        )
        assert "binary" in result.data.lower()

    @pytest.mark.asyncio
    async def test_read_directory(self, tmp_path) -> None:
        tool = FileReadTool()
        result = await tool.call(
            FileReadInput(file_path=str(tmp_path)),
            _make_context(str(tmp_path)),
            _noop_can_use,
            AssistantMessage(),
        )
        assert "not a regular file" in result.data.lower()

    def test_is_read_only(self) -> None:
        tool = FileReadTool()
        assert tool.is_read_only(FileReadInput(file_path="/x")) is True

    def test_is_concurrency_safe(self) -> None:
        tool = FileReadTool()
        assert tool.is_concurrency_safe(FileReadInput(file_path="/x")) is True

    @pytest.mark.asyncio
    async def test_description(self) -> None:
        tool = FileReadTool()
        desc = await tool.description(
            FileReadInput(file_path="/foo/bar.py"),
            DescriptionOptions(),
        )
        assert "/foo/bar.py" in desc

    def test_input_schema(self) -> None:
        tool = FileReadTool()
        assert tool.input_schema is FileReadInput

    @pytest.mark.asyncio
    async def test_suggest_similar_on_missing(self, tmp_path) -> None:
        (tmp_path / "config.py").write_text("x = 1")
        tool = FileReadTool()
        result = await tool.call(
            FileReadInput(file_path=str(tmp_path / "confg.py")),
            _make_context(str(tmp_path)),
            _noop_can_use,
            AssistantMessage(),
        )
        assert "not found" in result.data.lower()
        # Should suggest the similar file
        assert "config.py" in result.data


# ===========================================================================
# FileWriteTool
# ===========================================================================


class TestFileWriteTool:
    @pytest.mark.asyncio
    async def test_write_new_file(self, tmp_path) -> None:
        target = str(tmp_path / "new.txt")
        tool = FileWriteTool()
        result = await tool.call(
            FileWriteInput(file_path=target, content="hello world"),
            _make_context(str(tmp_path)),
            _noop_can_use,
            AssistantMessage(),
        )
        assert "created" in result.data.lower()
        assert os.path.isfile(target)
        with open(target) as f:
            assert f.read() == "hello world"

    @pytest.mark.asyncio
    async def test_overwrite_file(self, tmp_path) -> None:
        target = tmp_path / "existing.txt"
        target.write_text("old")

        tool = FileWriteTool()
        result = await tool.call(
            FileWriteInput(file_path=str(target), content="new"),
            _make_context(str(tmp_path)),
            _noop_can_use,
            AssistantMessage(),
        )
        assert "updated" in result.data.lower()
        assert target.read_text() == "new"

    @pytest.mark.asyncio
    async def test_creates_parent_dirs(self, tmp_path) -> None:
        target = str(tmp_path / "deep" / "nested" / "file.txt")
        tool = FileWriteTool()
        result = await tool.call(
            FileWriteInput(file_path=target, content="deep"),
            _make_context(str(tmp_path)),
            _noop_can_use,
            AssistantMessage(),
        )
        assert "created" in result.data.lower()
        assert os.path.isfile(target)

    def test_is_not_read_only(self) -> None:
        tool = FileWriteTool()
        assert tool.is_read_only(FileWriteInput(file_path="/x", content="y")) is False

    def test_not_concurrency_safe(self) -> None:
        tool = FileWriteTool()
        assert tool.is_concurrency_safe(FileWriteInput(file_path="/x", content="y")) is False

    @pytest.mark.asyncio
    async def test_description(self) -> None:
        tool = FileWriteTool()
        desc = await tool.description(
            FileWriteInput(file_path="/foo.py", content="x"),
            DescriptionOptions(),
        )
        assert "/foo.py" in desc


# ===========================================================================
# FileEditTool
# ===========================================================================


class TestFileEditTool:
    @pytest.mark.asyncio
    async def test_replace_unique(self, tmp_path) -> None:
        f = tmp_path / "code.py"
        f.write_text("def hello():\n    pass\n")

        tool = FileEditTool()
        result = await tool.call(
            FileEditInput(
                file_path=str(f),
                old_string="    pass",
                new_string='    return "hi"',
            ),
            _make_context(str(tmp_path)),
            _noop_can_use,
            AssistantMessage(),
        )
        assert "replaced" in result.data.lower()
        assert 'return "hi"' in f.read_text()

    @pytest.mark.asyncio
    async def test_not_found(self, tmp_path) -> None:
        f = tmp_path / "code.py"
        f.write_text("def hello():\n    pass\n")

        tool = FileEditTool()
        result = await tool.call(
            FileEditInput(
                file_path=str(f),
                old_string="nonexistent string",
                new_string="replacement",
            ),
            _make_context(str(tmp_path)),
            _noop_can_use,
            AssistantMessage(),
        )
        assert "not found" in result.data.lower()

    @pytest.mark.asyncio
    async def test_not_unique(self, tmp_path) -> None:
        f = tmp_path / "code.py"
        f.write_text("pass\npass\npass\n")

        tool = FileEditTool()
        result = await tool.call(
            FileEditInput(
                file_path=str(f),
                old_string="pass",
                new_string="continue",
            ),
            _make_context(str(tmp_path)),
            _noop_can_use,
            AssistantMessage(),
        )
        assert "3 times" in result.data
        # File should be unchanged
        assert f.read_text() == "pass\npass\npass\n"

    @pytest.mark.asyncio
    async def test_replace_all(self, tmp_path) -> None:
        f = tmp_path / "code.py"
        f.write_text("pass\npass\npass\n")

        tool = FileEditTool()
        result = await tool.call(
            FileEditInput(
                file_path=str(f),
                old_string="pass",
                new_string="continue",
                replace_all=True,
            ),
            _make_context(str(tmp_path)),
            _noop_can_use,
            AssistantMessage(),
        )
        assert "3 occurrence" in result.data
        assert f.read_text() == "continue\ncontinue\ncontinue\n"

    @pytest.mark.asyncio
    async def test_file_not_found(self, tmp_path) -> None:
        tool = FileEditTool()
        result = await tool.call(
            FileEditInput(
                file_path=str(tmp_path / "nope.py"),
                old_string="x",
                new_string="y",
            ),
            _make_context(str(tmp_path)),
            _noop_can_use,
            AssistantMessage(),
        )
        assert "not found" in result.data.lower()

    @pytest.mark.asyncio
    async def test_identical_strings(self, tmp_path) -> None:
        f = tmp_path / "noop.py"
        f.write_text("hello")

        tool = FileEditTool()
        result = await tool.call(
            FileEditInput(
                file_path=str(f),
                old_string="hello",
                new_string="hello",
            ),
            _make_context(str(tmp_path)),
            _noop_can_use,
            AssistantMessage(),
        )
        assert "identical" in result.data.lower()

    def test_is_not_read_only(self) -> None:
        tool = FileEditTool()
        inp = FileEditInput(file_path="/x", old_string="a", new_string="b")
        assert tool.is_read_only(inp) is False

    def test_not_concurrency_safe(self) -> None:
        tool = FileEditTool()
        inp = FileEditInput(file_path="/x", old_string="a", new_string="b")
        assert tool.is_concurrency_safe(inp) is False


# ===========================================================================
# NotebookEditTool
# ===========================================================================


def _make_notebook(cells: list[dict]) -> dict:
    """Create a minimal valid notebook structure."""
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python"}},
        "cells": cells,
    }


class TestNotebookEditTool:
    @pytest.mark.asyncio
    async def test_edit_code_cell(self, tmp_path) -> None:
        nb_path = tmp_path / "test.ipynb"
        notebook = _make_notebook([
            {
                "cell_type": "code",
                "source": ["print('hello')\n"],
                "metadata": {},
                "outputs": [{"output_type": "stream", "text": ["hello\n"]}],
                "execution_count": 1,
            }
        ])
        nb_path.write_text(json.dumps(notebook))

        tool = NotebookEditTool()
        result = await tool.call(
            NotebookEditInput(
                notebook_path=str(nb_path),
                cell_number=0,
                new_source="print('world')\n",
                cell_type="code",
            ),
            _make_context(str(tmp_path)),
            _noop_can_use,
            AssistantMessage(),
        )
        assert "updated" in result.data.lower()

        updated = json.loads(nb_path.read_text())
        assert updated["cells"][0]["source"] == ["print('world')\n"]
        # Outputs should be cleared
        assert updated["cells"][0]["outputs"] == []
        assert updated["cells"][0]["execution_count"] is None

    @pytest.mark.asyncio
    async def test_edit_markdown_cell(self, tmp_path) -> None:
        nb_path = tmp_path / "test.ipynb"
        notebook = _make_notebook([
            {"cell_type": "markdown", "source": ["# Title\n"], "metadata": {}},
        ])
        nb_path.write_text(json.dumps(notebook))

        tool = NotebookEditTool()
        result = await tool.call(
            NotebookEditInput(
                notebook_path=str(nb_path),
                cell_number=0,
                new_source="# New Title\n\nSome text",
                cell_type="markdown",
            ),
            _make_context(str(tmp_path)),
            _noop_can_use,
            AssistantMessage(),
        )
        assert "updated" in result.data.lower()

        updated = json.loads(nb_path.read_text())
        assert updated["cells"][0]["source"] == ["# New Title\n", "\n", "Some text"]

    @pytest.mark.asyncio
    async def test_cell_out_of_range(self, tmp_path) -> None:
        nb_path = tmp_path / "test.ipynb"
        notebook = _make_notebook([
            {"cell_type": "code", "source": [], "metadata": {}, "outputs": []},
        ])
        nb_path.write_text(json.dumps(notebook))

        tool = NotebookEditTool()
        result = await tool.call(
            NotebookEditInput(
                notebook_path=str(nb_path),
                cell_number=5,
                new_source="x = 1",
            ),
            _make_context(str(tmp_path)),
            _noop_can_use,
            AssistantMessage(),
        )
        assert "out of range" in result.data.lower()

    @pytest.mark.asyncio
    async def test_notebook_not_found(self, tmp_path) -> None:
        tool = NotebookEditTool()
        result = await tool.call(
            NotebookEditInput(
                notebook_path=str(tmp_path / "missing.ipynb"),
                cell_number=0,
                new_source="x = 1",
            ),
            _make_context(str(tmp_path)),
            _noop_can_use,
            AssistantMessage(),
        )
        assert "not found" in result.data.lower()

    @pytest.mark.asyncio
    async def test_invalid_json(self, tmp_path) -> None:
        nb_path = tmp_path / "bad.ipynb"
        nb_path.write_text("not json {{{")

        tool = NotebookEditTool()
        result = await tool.call(
            NotebookEditInput(
                notebook_path=str(nb_path),
                cell_number=0,
                new_source="x = 1",
            ),
            _make_context(str(tmp_path)),
            _noop_can_use,
            AssistantMessage(),
        )
        assert "error" in result.data.lower()

    def test_is_not_read_only(self) -> None:
        tool = NotebookEditTool()
        inp = NotebookEditInput(
            notebook_path="/x.ipynb", cell_number=0, new_source="y"
        )
        assert tool.is_read_only(inp) is False

    @pytest.mark.asyncio
    async def test_description(self) -> None:
        tool = NotebookEditTool()
        desc = await tool.description(
            NotebookEditInput(
                notebook_path="/nb.ipynb", cell_number=2, new_source="x"
            ),
            DescriptionOptions(),
        )
        assert "cell 2" in desc
        assert "/nb.ipynb" in desc



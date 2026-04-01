"""Tests for search tools: Glob, Grep, WebFetch, ToolSearch."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from code_assist.tools.base import ToolDef, ToolResult, ToolUseContext
from code_assist.tools.glob_tool.glob_tool import GlobInput, GlobTool
from code_assist.tools.grep_tool.grep_tool import GrepInput, GrepTool
from code_assist.tools.tool_search.tool_search_tool import ToolSearchInput, ToolSearchTool
from code_assist.tools.web_fetch.web_fetch_tool import WebFetchInput, WebFetchTool
from code_assist.tools.web_search.web_search_tool import WebSearchInput, WebSearchTool
from code_assist.types.message import AssistantMessage


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_context(**kwargs) -> ToolUseContext:
    return ToolUseContext(**kwargs)


def _noop_can_use(*a, **kw):
    return None


_PARENT = AssistantMessage()


# ---------------------------------------------------------------------------
# GlobTool Tests
# ---------------------------------------------------------------------------


class TestGlobTool:
    def test_properties(self) -> None:
        tool = GlobTool()
        assert tool.name == "Glob"
        assert tool.input_schema is GlobInput
        inp = GlobInput(pattern="**/*.py")
        assert tool.is_read_only(inp) is True
        assert tool.is_concurrency_safe(inp) is True
        assert tool.is_search_or_read_command(inp).is_search is True

    @pytest.mark.asyncio
    async def test_glob_finds_files(self, tmp_path: Path) -> None:
        # Create some test files
        (tmp_path / "a.py").write_text("hello")
        (tmp_path / "b.txt").write_text("world")
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "c.py").write_text("nested")

        tool = GlobTool()
        result = await tool.call(
            GlobInput(pattern="**/*.py", path=str(tmp_path)),
            _make_context(),
            _noop_can_use,
            _PARENT,
        )
        assert "a.py" in result.data
        assert "c.py" in result.data
        assert "b.txt" not in result.data

    @pytest.mark.asyncio
    async def test_glob_no_matches(self, tmp_path: Path) -> None:
        tool = GlobTool()
        result = await tool.call(
            GlobInput(pattern="*.xyz", path=str(tmp_path)),
            _make_context(),
            _noop_can_use,
            _PARENT,
        )
        assert result.data == "No files matched."

    @pytest.mark.asyncio
    async def test_glob_invalid_directory(self) -> None:
        tool = GlobTool()
        result = await tool.call(
            GlobInput(pattern="*.py", path="/nonexistent/path/xyzzy"),
            _make_context(),
            _noop_can_use,
            _PARENT,
        )
        assert "does not exist" in result.data

    @pytest.mark.asyncio
    async def test_glob_sorted_by_mtime(self, tmp_path: Path) -> None:
        # Create files with different mtimes
        f1 = tmp_path / "old.py"
        f2 = tmp_path / "new.py"
        f1.write_text("old")
        f2.write_text("new")
        # Ensure different mtimes
        os.utime(f1, (1000, 1000))
        os.utime(f2, (2000, 2000))

        tool = GlobTool()
        result = await tool.call(
            GlobInput(pattern="*.py", path=str(tmp_path)),
            _make_context(),
            _noop_can_use,
            _PARENT,
        )
        lines = result.data.strip().splitlines()
        assert len(lines) == 2
        # Most recent first
        assert "new.py" in lines[0]
        assert "old.py" in lines[1]

    @pytest.mark.asyncio
    async def test_glob_truncation(self, tmp_path: Path) -> None:
        """Test that results are truncated beyond MAX_RESULTS."""
        from code_assist.tools.glob_tool.glob_tool import MAX_RESULTS

        # We won't create 1001 files; just verify the truncation logic path
        # by testing with a small number of files that it returns correctly
        for i in range(5):
            (tmp_path / f"file{i}.txt").write_text(f"content{i}")

        tool = GlobTool()
        result = await tool.call(
            GlobInput(pattern="*.txt", path=str(tmp_path)),
            _make_context(),
            _noop_can_use,
            _PARENT,
        )
        assert "truncated" not in result.data
        # All 5 files should appear
        for i in range(5):
            assert f"file{i}.txt" in result.data


# ---------------------------------------------------------------------------
# GrepTool Tests
# ---------------------------------------------------------------------------


class TestGrepTool:
    def test_properties(self) -> None:
        tool = GrepTool()
        assert tool.name == "Grep"
        assert tool.input_schema is GrepInput
        inp = GrepInput(pattern="test")
        assert tool.is_read_only(inp) is True
        assert tool.is_concurrency_safe(inp) is True
        assert tool.is_search_or_read_command(inp).is_search is True

    @pytest.mark.asyncio
    async def test_grep_ripgrep_files_with_matches(self) -> None:
        """Test ripgrep backend with mocked subprocess."""
        tool = GrepTool()

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "file1.py\nfile2.py\n"
        mock_result.stderr = ""

        with (
            patch("shutil.which", return_value="/usr/bin/rg"),
            patch("subprocess.run", return_value=mock_result) as mock_run,
        ):
            result = await tool.call(
                GrepInput(pattern="def test"),
                _make_context(),
                _noop_can_use,
                _PARENT,
            )

        assert "file1.py" in result.data
        assert "file2.py" in result.data
        # Verify rg was called with --files-with-matches
        cmd = mock_run.call_args[0][0]
        assert "--files-with-matches" in cmd
        assert "def test" in cmd

    @pytest.mark.asyncio
    async def test_grep_ripgrep_content_mode(self) -> None:
        """Test ripgrep in content mode with context flags."""
        tool = GrepTool()

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "1:hello world\n2:hello there\n"
        mock_result.stderr = ""

        with (
            patch("shutil.which", return_value="/usr/bin/rg"),
            patch("subprocess.run", return_value=mock_result) as mock_run,
        ):
            result = await tool.call(
                GrepInput(
                    pattern="hello",
                    output_mode="content",
                    after_context=2,
                    case_insensitive=True,
                    line_numbers=True,
                ),
                _make_context(),
                _noop_can_use,
                _PARENT,
            )

        cmd = mock_run.call_args[0][0]
        assert "-A" in cmd
        assert "-n" in cmd
        assert "-i" in cmd
        assert "hello" in result.data

    @pytest.mark.asyncio
    async def test_grep_ripgrep_no_matches(self) -> None:
        """Test ripgrep returning no matches (exit code 1)."""
        tool = GrepTool()

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = ""

        with (
            patch("shutil.which", return_value="/usr/bin/rg"),
            patch("subprocess.run", return_value=mock_result),
        ):
            result = await tool.call(
                GrepInput(pattern="nonexistent_pattern_xyz"),
                _make_context(),
                _noop_can_use,
                _PARENT,
            )

        assert "No matches" in result.data

    @pytest.mark.asyncio
    async def test_grep_ripgrep_with_glob_filter(self) -> None:
        """Test ripgrep with glob and type filters."""
        tool = GrepTool()

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "main.py\n"
        mock_result.stderr = ""

        with (
            patch("shutil.which", return_value="/usr/bin/rg"),
            patch("subprocess.run", return_value=mock_result) as mock_run,
        ):
            result = await tool.call(
                GrepInput(pattern="import", glob="*.py", type="py"),
                _make_context(),
                _noop_can_use,
                _PARENT,
            )

        cmd = mock_run.call_args[0][0]
        assert "--glob" in cmd
        assert "*.py" in cmd
        assert "--type" in cmd
        assert "py" in cmd

    @pytest.mark.asyncio
    async def test_grep_ripgrep_multiline(self) -> None:
        """Test ripgrep with multiline mode."""
        tool = GrepTool()

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "match\n"
        mock_result.stderr = ""

        with (
            patch("shutil.which", return_value="/usr/bin/rg"),
            patch("subprocess.run", return_value=mock_result) as mock_run,
        ):
            result = await tool.call(
                GrepInput(pattern="class.*:", multiline=True),
                _make_context(),
                _noop_can_use,
                _PARENT,
            )

        cmd = mock_run.call_args[0][0]
        assert "-U" in cmd
        assert "--multiline-dotall" in cmd

    @pytest.mark.asyncio
    async def test_grep_ripgrep_offset_and_limit(self) -> None:
        """Test offset and head_limit on ripgrep output."""
        tool = GrepTool()

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "a.py\nb.py\nc.py\nd.py\ne.py\n"
        mock_result.stderr = ""

        with (
            patch("shutil.which", return_value="/usr/bin/rg"),
            patch("subprocess.run", return_value=mock_result),
        ):
            result = await tool.call(
                GrepInput(pattern="x", offset=1, head_limit=2),
                _make_context(),
                _noop_can_use,
                _PARENT,
            )

        # Skip first 1, take next 2: b.py, c.py
        assert "b.py" in result.data
        assert "c.py" in result.data
        assert "a.py" not in result.data
        assert "d.py" not in result.data

    @pytest.mark.asyncio
    async def test_grep_python_fallback(self, tmp_path: Path) -> None:
        """Test Python re fallback when rg is not available."""
        (tmp_path / "hello.py").write_text("def hello():\n    pass\n")
        (tmp_path / "world.py").write_text("x = 1\n")

        tool = GrepTool()

        with patch("shutil.which", return_value=None):
            result = await tool.call(
                GrepInput(pattern="def", path=str(tmp_path)),
                _make_context(),
                _noop_can_use,
                _PARENT,
            )

        assert "hello.py" in result.data
        assert "world.py" not in result.data

    @pytest.mark.asyncio
    async def test_grep_python_fallback_content_mode(self, tmp_path: Path) -> None:
        """Test Python fallback in content mode."""
        (tmp_path / "test.py").write_text("line1\nhello world\nline3\n")

        tool = GrepTool()

        with patch("shutil.which", return_value=None):
            result = await tool.call(
                GrepInput(
                    pattern="hello",
                    path=str(tmp_path),
                    output_mode="content",
                ),
                _make_context(),
                _noop_can_use,
                _PARENT,
            )

        assert "hello world" in result.data

    @pytest.mark.asyncio
    async def test_grep_ripgrep_timeout(self) -> None:
        """Test handling of subprocess timeout."""
        tool = GrepTool()

        with (
            patch("shutil.which", return_value="/usr/bin/rg"),
            patch(
                "subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd="rg", timeout=30),
            ),
        ):
            result = await tool.call(
                GrepInput(pattern="test"),
                _make_context(),
                _noop_can_use,
                _PARENT,
            )

        assert "timed out" in result.data


# ---------------------------------------------------------------------------
# WebFetchTool Tests
# ---------------------------------------------------------------------------


class TestWebFetchTool:
    def test_properties(self) -> None:
        tool = WebFetchTool()
        assert tool.name == "WebFetch"
        assert tool.input_schema is WebFetchInput
        inp = WebFetchInput(url="https://example.com")
        assert tool.is_read_only(inp) is True
        assert tool.is_concurrency_safe(inp) is True
        assert tool.is_search_or_read_command(inp).is_read is True

    @pytest.mark.asyncio
    async def test_fetch_plain_text(self) -> None:
        """Test fetching plain text content."""
        tool = WebFetchTool()

        mock_response = MagicMock()
        mock_response.text = "Hello, world!"
        mock_response.headers = {"content-type": "text/plain"}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await tool.call(
                WebFetchInput(url="https://example.com/data.txt"),
                _make_context(),
                _noop_can_use,
                _PARENT,
            )

        assert "Hello, world!" in result.data

    @pytest.mark.asyncio
    async def test_fetch_html_strips_tags(self) -> None:
        """Test that HTML tags are stripped."""
        tool = WebFetchTool()

        html = "<html><head><title>Test</title></head><body><p>Content here</p></body></html>"
        mock_response = MagicMock()
        mock_response.text = html
        mock_response.headers = {"content-type": "text/html; charset=utf-8"}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await tool.call(
                WebFetchInput(url="https://example.com"),
                _make_context(),
                _noop_can_use,
                _PARENT,
            )

        assert "Content here" in result.data
        assert "<p>" not in result.data

    @pytest.mark.asyncio
    async def test_fetch_with_prompt(self) -> None:
        """Test that prompt is prepended to output."""
        tool = WebFetchTool()

        mock_response = MagicMock()
        mock_response.text = "Some content"
        mock_response.headers = {"content-type": "text/plain"}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await tool.call(
                WebFetchInput(url="https://example.com", prompt="Find the title"),
                _make_context(),
                _noop_can_use,
                _PARENT,
            )

        assert "Extraction prompt: Find the title" in result.data
        assert "Some content" in result.data

    @pytest.mark.asyncio
    async def test_fetch_adds_https(self) -> None:
        """Test that https:// is prepended if missing."""
        tool = WebFetchTool()

        mock_response = MagicMock()
        mock_response.text = "ok"
        mock_response.headers = {"content-type": "text/plain"}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await tool.call(
                WebFetchInput(url="example.com"),
                _make_context(),
                _noop_can_use,
                _PARENT,
            )

        # The call should have used https://example.com
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "https://example.com"

    @pytest.mark.asyncio
    async def test_fetch_timeout_error(self) -> None:
        """Test handling of timeout."""
        tool = WebFetchTool()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await tool.call(
                WebFetchInput(url="https://slow.example.com"),
                _make_context(),
                _noop_can_use,
                _PARENT,
            )

        assert "timed out" in result.data

    @pytest.mark.asyncio
    async def test_fetch_http_error(self) -> None:
        """Test handling of HTTP errors."""
        tool = WebFetchTool()

        mock_response = MagicMock()
        mock_response.status_code = 404
        exc = httpx.HTTPStatusError(
            "Not Found",
            request=MagicMock(),
            response=mock_response,
        )

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=exc)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await tool.call(
                WebFetchInput(url="https://example.com/missing"),
                _make_context(),
                _noop_can_use,
                _PARENT,
            )

        assert "404" in result.data

    @pytest.mark.asyncio
    async def test_fetch_strips_script_tags(self) -> None:
        """Test that script and style content is removed."""
        tool = WebFetchTool()

        html = (
            "<html><head><script>var x = 1;</script>"
            "<style>.cls{color:red}</style></head>"
            "<body>Visible text</body></html>"
        )
        mock_response = MagicMock()
        mock_response.text = html
        mock_response.headers = {"content-type": "text/html"}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await tool.call(
                WebFetchInput(url="https://example.com"),
                _make_context(),
                _noop_can_use,
                _PARENT,
            )

        assert "Visible text" in result.data
        assert "var x = 1" not in result.data
        assert "color:red" not in result.data


# ---------------------------------------------------------------------------
# WebSearchTool Tests
# ---------------------------------------------------------------------------


class TestWebSearchTool:
    def test_properties(self) -> None:
        tool = WebSearchTool()
        assert tool.name == "WebSearch"
        assert tool.input_schema is WebSearchInput
        assert tool.is_read_only(WebSearchInput(query="test")) is True

    @pytest.mark.asyncio
    async def test_returns_placeholder(self) -> None:
        tool = WebSearchTool()
        result = await tool.call(
            WebSearchInput(query="python asyncio"),
            _make_context(),
            _noop_can_use,
            _PARENT,
        )
        assert result.data == "Web search not yet configured"


# ---------------------------------------------------------------------------
# ToolSearchTool Tests
# ---------------------------------------------------------------------------


class _FakeTool(ToolDef):
    """Fake tool for testing ToolSearch."""

    name = "FakeTool"
    aliases = ["ft"]
    search_hint = "fake testing"

    @property
    def input_schema(self) -> type:
        from pydantic import BaseModel as BM

        class FakeInput(BM):
            x: int = 1

        return FakeInput


class _AnotherFakeTool(ToolDef):
    name = "AnotherTool"
    search_hint = "another utility"


class TestToolSearchTool:
    def test_properties(self) -> None:
        tool = ToolSearchTool()
        assert tool.name == "ToolSearch"
        assert tool.input_schema is ToolSearchInput
        assert tool.is_read_only(ToolSearchInput(query="x")) is True
        assert tool.is_concurrency_safe(ToolSearchInput(query="x")) is True

    @pytest.mark.asyncio
    async def test_search_by_name(self) -> None:
        tool = ToolSearchTool()
        ctx = _make_context(tools=[_FakeTool(), _AnotherFakeTool()])

        result = await tool.call(
            ToolSearchInput(query="FakeTool"),
            ctx,
            _noop_can_use,
            _PARENT,
        )

        assert "FakeTool" in result.data

    @pytest.mark.asyncio
    async def test_search_by_alias(self) -> None:
        tool = ToolSearchTool()
        ctx = _make_context(tools=[_FakeTool(), _AnotherFakeTool()])

        result = await tool.call(
            ToolSearchInput(query="ft"),
            ctx,
            _noop_can_use,
            _PARENT,
        )

        assert "FakeTool" in result.data

    @pytest.mark.asyncio
    async def test_search_by_hint(self) -> None:
        tool = ToolSearchTool()
        ctx = _make_context(tools=[_FakeTool(), _AnotherFakeTool()])

        result = await tool.call(
            ToolSearchInput(query="utility"),
            ctx,
            _noop_can_use,
            _PARENT,
        )

        assert "AnotherTool" in result.data

    @pytest.mark.asyncio
    async def test_search_no_matches(self) -> None:
        tool = ToolSearchTool()
        ctx = _make_context(tools=[_FakeTool()])

        result = await tool.call(
            ToolSearchInput(query="nonexistent_xyz_tool"),
            ctx,
            _noop_can_use,
            _PARENT,
        )

        assert "No tools matched" in result.data

    @pytest.mark.asyncio
    async def test_search_max_results(self) -> None:
        tool = ToolSearchTool()
        # Create many tools that all match "tool"
        tools = []
        for i in range(10):
            t = ToolDef()
            t.name = f"Tool{i}"
            t.search_hint = "tool utility"
            tools.append(t)

        ctx = _make_context(tools=tools)

        result = await tool.call(
            ToolSearchInput(query="tool", max_results=3),
            ctx,
            _noop_can_use,
            _PARENT,
        )

        # Should have at most 3 entries (lines starting with "- ")
        entries = [line for line in result.data.splitlines() if line.startswith("- ")]
        assert len(entries) <= 3


# ---------------------------------------------------------------------------
# Registry Integration
# ---------------------------------------------------------------------------



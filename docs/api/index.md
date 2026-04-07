# API Reference

code-assist exposes a Python API for programmatic use. The primary entry point is `QueryEngine`, which orchestrates the full agent loop — system prompt assembly, tool filtering, API streaming, and tool execution.

## Quick Start

```python
import asyncio
from code_assist.core.query_engine import QueryEngine, QueryEngineConfig
from code_assist.core.query import TextEvent, ToolUseEvent, ToolResultEvent, DoneEvent
from code_assist.tools.registry import get_all_tools


async def main():
    # Configure the engine
    config = QueryEngineConfig(
        cwd="/path/to/project",
        project_root="/path/to/project",
        tools=get_all_tools(),
        model="claude-sonnet-4-6",
        max_turns=50,
        max_tokens=16384,
        api_key="sk-ant-...",  # or set ANTHROPIC_API_KEY env var
    )

    engine = QueryEngine(config)

    # Submit a message and stream events
    async for event in engine.submit_message("Explain the architecture of this project"):
        if isinstance(event, TextEvent):
            print(event.text, end="", flush=True)
        elif isinstance(event, ToolUseEvent):
            print(f"\n[Tool: {event.tool_name}]")
        elif isinstance(event, ToolResultEvent):
            if event.is_error:
                print(f"\n[Error: {event.result}]")
        elif isinstance(event, DoneEvent):
            print(f"\n\n--- Done ({event.total_turns} turns) ---")


asyncio.run(main())
```

## Core Modules

| Module | Import Path | Description |
|---|---|---|
| **QueryEngine** | `code_assist.core.query_engine` | High-level orchestrator — the primary API |
| **query()** | `code_assist.core.query` | Low-level agent loop (async generator) |
| **Tool Protocol** | `code_assist.tools.base` | `Tool` protocol and `ToolDef` base class |
| **Tool Registry** | `code_assist.tools.registry` | `get_all_tools()` to assemble tools |
| **Settings** | `code_assist.config.settings` | `load_merged_settings()` for configuration |
| **CLAUDE.md** | `code_assist.config.claude_md` | Memory file discovery and context building |
| **Memory** | `code_assist.memory.memory_scan` | Structured memory entry scanning |
| **Types** | `code_assist.types.*` | Message, permission, hook, command, plugin types |

## Event Types

The `QueryEngine.submit_message()` method yields these event types:

| Event | Fields | Description |
|---|---|---|
| `TextEvent` | `text: str` | Streamed text from the assistant |
| `ToolUseEvent` | `tool_use_id, tool_name, tool_input` | Tool call initiated by the model |
| `ToolResultEvent` | `tool_use_id, result, is_error` | Result of a tool execution |
| `AssistantMessageEvent` | `message: AssistantMessage` | Complete assistant message (after streaming) |
| `ErrorEvent` | `error: str, is_retryable: bool` | API or execution error |
| `DoneEvent` | `stop_reason, total_turns, total_cost_usd` | Query loop completed |

## Multi-Turn Conversations

The `QueryEngine` maintains conversation history across calls:

```python
engine = QueryEngine(config)

# First turn
async for event in engine.submit_message("Read the README"):
    ...

# Second turn — conversation history is preserved
async for event in engine.submit_message("Now summarize it in bullet points"):
    ...

# Check state
print(f"Total turns: {engine.total_turns}")
print(f"Message count: {len(engine.messages)}")

# Reset
engine.clear_messages()
```

## Headless / CI Usage

For non-interactive use, configure the engine with explicit API key and restricted tools:

```python
from code_assist.tools.base import ToolDef
from code_assist.tools.file_read.file_read_tool import FileReadTool
from code_assist.tools.glob_tool.glob_tool import GlobTool
from code_assist.tools.grep_tool.grep_tool import GrepTool

config = QueryEngineConfig(
    cwd="/path/to/project",
    project_root="/path/to/project",
    tools=[FileReadTool(), GlobTool(), GrepTool()],  # Read-only tools only
    model="claude-sonnet-4-6",
    max_turns=10,
    api_key=os.environ["ANTHROPIC_API_KEY"],
    custom_system_prompt="You are a code reviewer. Only analyze, never modify.",
)
```

## Further Reading

- [QueryEngine](/api/query-engine) — full class reference and configuration options.
- [Tools API](/api/tools) — building custom tools with the `Tool` protocol and `ToolDef` base class.

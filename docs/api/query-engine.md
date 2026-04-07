# QueryEngine

`QueryEngine` is the primary API for interacting with code-assist programmatically. It wraps the core agent loop, handles system prompt assembly, manages conversation history, and streams typed events to the caller.

**Module:** `code_assist.core.query_engine`

## Class: QueryEngine

```python
class QueryEngine:
    def __init__(self, config: QueryEngineConfig) -> None: ...
```

### Constructor

| Parameter | Type | Description |
|---|---|---|
| `config` | `QueryEngineConfig` | Engine configuration (see below) |

### Properties

| Property | Type | Description |
|---|---|---|
| `messages` | `list[Message]` | The full conversation message history |
| `total_turns` | `int` | Cumulative turn count across all `submit_message` calls |

### Methods

#### `submit_message(prompt: str) -> AsyncGenerator[QueryEvent, None]`

Submit a user message and stream the response as an async generator of `QueryEvent` objects.

**Behavior:**

1. Processes the input via `process_user_input()` to detect slash commands.
2. If the input is a slash command, yields a `TextEvent` with the command result (command wiring is in progress).
3. Otherwise, appends a `UserMessage` to the history.
4. Builds the system prompt from CLAUDE.md files and configuration.
5. Builds a `ToolUseContext` with filtered tools.
6. Delegates to `query()` — the core agent loop.
7. Yields each event from the loop: `TextEvent`, `ToolUseEvent`, `ToolResultEvent`, `AssistantMessageEvent`, `ErrorEvent`, `DoneEvent`.
8. Tracks cumulative turns.

```python
async for event in engine.submit_message("Fix the bug in parser.py"):
    match event:
        case TextEvent(text=t):
            print(t, end="")
        case ToolUseEvent(tool_name=name):
            print(f"\n--- Using tool: {name} ---")
        case DoneEvent(stop_reason=reason, total_turns=turns):
            print(f"\nDone: {reason} after {turns} turns")
```

#### `clear_messages() -> None`

Clear the conversation history. Does not reset `total_turns`.

```python
engine.clear_messages()
assert len(engine.messages) == 0
```

## Class: QueryEngineConfig

```python
@dataclass
class QueryEngineConfig:
    cwd: str = ""
    project_root: str = ""
    tools: Tools = field(default_factory=list)
    commands: list[Any] = field(default_factory=list)
    mcp_clients: list[Any] = field(default_factory=list)
    agent_definitions: Any = None
    model: str = "claude-sonnet-4-6"
    max_turns: int = 100
    max_tokens: int = 16384
    api_key: str | None = None
    base_url: str | None = None
    custom_system_prompt: str | None = None
    append_system_prompt: str | None = None
    json_schema: dict[str, Any] | None = None
```

### Configuration Fields

| Field | Type | Default | Description |
|---|---|---|---|
| `cwd` | `str` | `""` | Current working directory |
| `project_root` | `str` | `""` | Project root for CLAUDE.md discovery and settings resolution |
| `tools` | `Tools` | `[]` | List of tool instances (use `get_all_tools()` for defaults) |
| `commands` | `list` | `[]` | Slash commands available in this session |
| `mcp_clients` | `list` | `[]` | Connected MCP client instances |
| `agent_definitions` | `Any` | `None` | Pre-configured agent templates |
| `model` | `str` | `"claude-sonnet-4-6"` | Anthropic model identifier |
| `max_turns` | `int` | `100` | Maximum agent loop iterations per `submit_message` call |
| `max_tokens` | `int` | `16384` | Maximum tokens in each API response |
| `api_key` | `str \| None` | `None` | Anthropic API key (falls back to `get_api_key()`) |
| `base_url` | `str \| None` | `None` | Custom API base URL (for proxies or testing) |
| `custom_system_prompt` | `str \| None` | `None` | Replaces the entire system prompt (skips CLAUDE.md) |
| `append_system_prompt` | `str \| None` | `None` | Appended after the default system prompt |
| `json_schema` | `dict \| None` | `None` | JSON schema for structured output mode |

## Event Types

All events inherit from `QueryEvent`:

### TextEvent

```python
@dataclass
class TextEvent(QueryEvent):
    type: str = "text"
    text: str = ""
```

Emitted as the model streams text. You will receive many `TextEvent` instances for a single response — concatenate them for the full text.

### ToolUseEvent

```python
@dataclass
class ToolUseEvent(QueryEvent):
    type: str = "tool_use"
    tool_use_id: str = ""
    tool_name: str = ""
    tool_input: dict[str, Any] = field(default_factory=dict)
```

Emitted when the model initiates a tool call. The `tool_input` dict contains the raw input before pydantic validation.

### ToolResultEvent

```python
@dataclass
class ToolResultEvent(QueryEvent):
    type: str = "tool_result"
    tool_use_id: str = ""
    result: str = ""
    is_error: bool = False
```

Emitted after a tool finishes execution. If `is_error` is `True`, the `result` contains the error message.

### AssistantMessageEvent

```python
@dataclass
class AssistantMessageEvent(QueryEvent):
    type: str = "assistant_message"
    message: AssistantMessage = field(default_factory=AssistantMessage)
```

Emitted once per API response with the complete `AssistantMessage` (including all content blocks, usage, and stop reason).

### ErrorEvent

```python
@dataclass
class ErrorEvent(QueryEvent):
    type: str = "error"
    error: str = ""
    is_retryable: bool = False
```

Emitted when an API or execution error occurs. If `is_retryable` is `True`, the loop will retry automatically.

### DoneEvent

```python
@dataclass
class DoneEvent(QueryEvent):
    type: str = "done"
    stop_reason: str = ""       # "end_turn", "max_turns", "tool_use"
    total_turns: int = 0
    total_cost_usd: float = 0.0
```

Emitted when the agent loop completes. `stop_reason` is `"end_turn"` for normal completion and `"max_turns"` if the turn limit was hit.

## System Prompt Assembly

The system prompt is built by `_build_system_prompt()`:

1. If `custom_system_prompt` is set, it replaces everything else.
2. Otherwise:
   - A core instruction block is added.
   - CLAUDE.md files are discovered via `get_memory_files(project_root)` and concatenated via `build_claude_md_context()`.
   - If `append_system_prompt` is set, it is appended as a final block.
3. Each block can have `cache_control: {"type": "ephemeral"}` for Anthropic prompt caching.

## Usage Examples

### Basic interactive use

```python
config = QueryEngineConfig(
    cwd="/home/user/project",
    project_root="/home/user/project",
    tools=get_all_tools(),
)
engine = QueryEngine(config)

async for event in engine.submit_message("What does this project do?"):
    if isinstance(event, TextEvent):
        print(event.text, end="")
```

### Custom system prompt

```python
config = QueryEngineConfig(
    tools=get_all_tools(),
    custom_system_prompt="You are a security auditor. Analyze code for vulnerabilities.",
)
engine = QueryEngine(config)
```

### Restricted tools with append prompt

```python
from code_assist.tools.file_read.file_read_tool import FileReadTool
from code_assist.tools.grep_tool.grep_tool import GrepTool

config = QueryEngineConfig(
    tools=[FileReadTool(), GrepTool()],
    append_system_prompt="Only search for potential SQL injection vulnerabilities.",
    max_turns=20,
)
engine = QueryEngine(config)
```

### Collecting all events

```python
events = []
async for event in engine.submit_message("List all Python files"):
    events.append(event)

text_events = [e for e in events if isinstance(e, TextEvent)]
full_response = "".join(e.text for e in text_events)
```

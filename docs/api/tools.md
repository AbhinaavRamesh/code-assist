# Tools API

This page covers the `Tool` protocol, the `ToolDef` base class, and how to build custom tools.

**Module:** `code_assist.tools.base`

## Tool Protocol

The `Tool` protocol defines the interface every tool must satisfy. It is a `runtime_checkable` protocol, so you can use `isinstance(obj, Tool)` at runtime.

```python
@runtime_checkable
class Tool(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def max_result_size_chars(self) -> int: ...

    @property
    def input_schema(self) -> type[BaseModel]: ...

    async def call(
        self,
        args: BaseModel,
        context: ToolUseContext,
        can_use_tool: CanUseToolFn,
        parent_message: AssistantMessage,
        on_progress: ToolCallProgress | None = None,
    ) -> ToolResult: ...

    async def description(
        self, input: BaseModel, options: DescriptionOptions,
    ) -> str: ...

    def is_enabled(self) -> bool: ...
    def is_read_only(self, input: BaseModel) -> bool: ...
    def is_concurrency_safe(self, input: BaseModel) -> bool: ...
```

### Protocol Methods

| Method | Signature | Description |
|---|---|---|
| `name` | `-> str` | Unique tool identifier (e.g., `"Bash"`, `"FileRead"`) |
| `max_result_size_chars` | `-> int` | Max result length before persisting to disk |
| `input_schema` | `-> type[BaseModel]` | Pydantic model class for input validation |
| `call()` | `async (args, context, ...) -> ToolResult` | Execute the tool |
| `description()` | `async (input, options) -> str` | Generate a human-readable description |
| `is_enabled()` | `-> bool` | Whether the tool is currently available |
| `is_read_only()` | `(input) -> bool` | Whether this invocation is read-only |
| `is_concurrency_safe()` | `(input) -> bool` | Whether the tool can run in parallel |

## ToolDef Base Class

`ToolDef` is a concrete base class that provides sensible defaults for all optional methods. Most tool implementations subclass `ToolDef` and override only what they need.

```python
class ToolDef:
    name: str = ""
    aliases: list[str] = []
    search_hint: str | None = None
    max_result_size_chars: int = 100_000
    should_defer: bool = False
    always_load: bool = False
    is_mcp: bool = False
    is_lsp: bool = False
    strict: bool = False
```

### Class Attributes

| Attribute | Type | Default | Description |
|---|---|---|---|
| `name` | `str` | `""` | Primary tool name |
| `aliases` | `list[str]` | `[]` | Alternative names for tool lookup |
| `search_hint` | `str \| None` | `None` | Keywords for `ToolSearchTool` discovery |
| `max_result_size_chars` | `int` | `100,000` | Max result before disk persistence |
| `should_defer` | `bool` | `False` | Load lazily via `ToolSearchTool` |
| `always_load` | `bool` | `False` | Always include in tool list (even if deferred) |
| `is_mcp` | `bool` | `False` | Whether this wraps an MCP tool |
| `is_lsp` | `bool` | `False` | Whether this wraps an LSP tool |
| `strict` | `bool` | `False` | Enable strict input validation |

### Overridable Methods

| Method | Default | Override When |
|---|---|---|
| `call()` | `NotImplementedError` | Always (this is the main logic) |
| `input_schema` | `BaseModel` | Always (define your input fields) |
| `description()` | `f"Using {self.name}"` | You want a richer description |
| `prompt()` | `""` | You want to inject system prompt text |
| `is_enabled()` | `True` | The tool is conditionally available |
| `is_read_only()` | `False` | The tool only reads data |
| `is_concurrency_safe()` | `True` | The tool has write conflicts |
| `is_destructive()` | `False` | The tool performs irreversible operations |
| `interrupt_behavior()` | `"block"` | The tool should be cancelled on user input |
| `validate_input()` | `ValidationResult(True)` | You need custom validation beyond pydantic |
| `check_permissions()` | `None` | You need tool-specific permission logic |
| `backfill_observable_input()` | no-op | You want to sanitize input before observers see it |

## ToolResult

The return type of `tool.call()`:

```python
@dataclass
class ToolResult:
    data: Any = None
    new_messages: list[Message] | None = None
    context_modifier: Callable[[ToolUseContext], ToolUseContext] | None = None
    mcp_meta: dict[str, Any] | None = None
```

| Field | Type | Description |
|---|---|---|
| `data` | `Any` | The tool output (usually a string). Sent back to the model. |
| `new_messages` | `list[Message] \| None` | Additional messages to inject into the conversation |
| `context_modifier` | `Callable \| None` | A function that modifies the `ToolUseContext` for subsequent tools |
| `mcp_meta` | `dict \| None` | MCP-specific metadata |

## ToolUseContext

The execution context passed to every `tool.call()`:

```python
@dataclass
class ToolUseContext:
    commands: list[Any] = []
    debug: bool = False
    main_loop_model: str = ""
    tools: list[Tool] = []
    verbose: bool = False
    mcp_clients: list[Any] = []
    mcp_resources: dict[str, list[Any]] = {}
    is_non_interactive_session: bool = False
    agent_definitions: Any = None
    max_budget_usd: float | None = None
    custom_system_prompt: str | None = None
    append_system_prompt: str | None = None
    query_source: str | None = None
    refresh_tools: Callable[[], list[Tool]] | None = None
    abort_controller: asyncio.Event = ...
    messages: list[Message] = []
    read_file_state: dict[str, Any] = {}
    agent_id: str | None = None
    agent_type: str | None = None
    tool_use_id: str | None = None
    file_reading_limits: dict[str, int] | None = None
    glob_limits: dict[str, int] | None = None
```

### Key Context Fields

| Field | Description |
|---|---|
| `tools` | The full list of available tools (for meta-tools like AgentTool) |
| `messages` | The current conversation history |
| `mcp_clients` | Connected MCP clients for MCP-bridged operations |
| `abort_controller` | An `asyncio.Event` that signals when the user aborts |
| `agent_id` | Unique identifier for the current agent |
| `read_file_state` | Tracks which files have been read (for permission enforcement) |

## Creating a Custom Tool

### Step 1: Define the input schema

```python
from pydantic import BaseModel, Field


class CountLinesInput(BaseModel):
    """Count lines in a file matching a pattern."""
    file_path: str = Field(..., description="Absolute path to the file")
    pattern: str = Field("", description="Regex pattern to filter lines")
```

### Step 2: Implement the tool

```python
import re
from pathlib import Path

from code_assist.tools.base import (
    ToolDef, ToolResult, ToolUseContext,
    CanUseToolFn, ToolCallProgress, DescriptionOptions,
)
from code_assist.types.message import AssistantMessage


class CountLinesTool(ToolDef):
    name = "CountLines"
    aliases = ["count", "wc"]
    search_hint = "count lines in file"
    max_result_size_chars = 10_000

    @property
    def input_schema(self) -> type[BaseModel]:
        return CountLinesInput

    async def call(
        self,
        args: BaseModel,
        context: ToolUseContext,
        can_use_tool: CanUseToolFn,
        parent_message: AssistantMessage,
        on_progress: ToolCallProgress | None = None,
    ) -> ToolResult:
        inp: CountLinesInput = args  # type: ignore[assignment]
        path = Path(inp.file_path)

        if not path.is_file():
            return ToolResult(data=f"Error: {inp.file_path} is not a file")

        content = path.read_text(encoding="utf-8")
        lines = content.splitlines()

        if inp.pattern:
            regex = re.compile(inp.pattern)
            matching = [l for l in lines if regex.search(l)]
            return ToolResult(
                data=f"{len(matching)} lines match '{inp.pattern}' (out of {len(lines)} total)"
            )

        return ToolResult(data=f"{len(lines)} lines")

    async def description(self, input: BaseModel, options: DescriptionOptions) -> str:
        inp: CountLinesInput = input  # type: ignore[assignment]
        if inp.pattern:
            return f"Counting lines matching '{inp.pattern}' in {inp.file_path}"
        return f"Counting lines in {inp.file_path}"

    def is_read_only(self, input: BaseModel) -> bool:
        return True

    def is_concurrency_safe(self, input: BaseModel) -> bool:
        return True
```

### Step 3: Register the tool

Add it to the registry:

```python
# In tools/registry.py
from code_assist.tools.count_lines import CountLinesTool

def get_all_tools() -> Tools:
    tools: Tools = [
        # ... existing tools ...
        CountLinesTool(),
    ]
    return tools
```

Or pass it directly to the `QueryEngineConfig`:

```python
config = QueryEngineConfig(
    tools=[*get_all_tools(), CountLinesTool()],
    ...
)
```

## Validation and Permissions

### Custom validation

Override `validate_input()` for validation beyond what pydantic provides:

```python
async def validate_input(
    self, input: BaseModel, context: ToolUseContext
) -> ValidationResult:
    inp: CountLinesInput = input  # type: ignore[assignment]
    if not Path(inp.file_path).is_absolute():
        return ValidationResult(
            result=False,
            message="file_path must be an absolute path",
            error_code=1,
        )
    return ValidationResult(result=True)
```

### Custom permission check

Override `check_permissions()` for tool-specific permission logic:

```python
from code_assist.types.permissions import PermissionResult, PermissionDenyDecision

async def check_permissions(
    self, input: BaseModel, context: ToolUseContext
) -> PermissionResult | None:
    inp: CountLinesInput = input  # type: ignore[assignment]
    if "/etc/" in inp.file_path:
        return PermissionDenyDecision(
            behavior="deny",
            message="Cannot access system files in /etc/",
        )
    return None  # Fall through to normal permission logic
```

## Utility Functions

```python
from code_assist.tools.base import tool_matches_name, find_tool_by_name

# Check if a tool matches a name or alias
matches = tool_matches_name(my_tool, "CountLines")  # True
matches = tool_matches_name(my_tool, "count")        # True (alias)
matches = tool_matches_name(my_tool, "wc")            # True (alias)

# Find a tool by name in a list
tool = find_tool_by_name(all_tools, "CountLines")
```

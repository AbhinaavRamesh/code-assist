# Commands

Claude Code supports **slash commands** — typed as `/command` in the prompt. Commands are either **local** (executed immediately on the client) or **prompt** (expanded into an API query).

## Command Types

| Type | Enum Value | Behavior |
|---|---|---|
| **Local** | `local` | Runs client-side logic, returns `TextCommandResult`, `CompactCommandResult`, or `SkipCommandResult` |
| **Prompt** | `prompt` | Expands to API messages via `get_prompt_for_command()`, then submitted to the model |
| **Local JSX** | `local-jsx` | Like local, but returns rich UI components (TUI widgets) |

## Command Sources

Commands can be loaded from multiple sources, identified by `CommandLoadedFrom`:

| Source | Description |
|---|---|
| `bundled` | Ships with claude-code core |
| `managed` | Organization-managed commands |
| `skills` | User-defined skills (see [Skills](/guide/skills)) |
| `plugin` | Loaded from installed plugins |
| `mcp` | Provided by MCP servers |
| `commands_DEPRECATED` | Legacy command format |

## Built-in Commands

### Session Management

| Command | Type | Description |
|---|---|---|
| `/clear` | local | Clear the conversation history and start fresh |
| `/compact` | local | Compact the conversation to reduce token usage. Returns `CompactCommandResult` with the summarized context |
| `/resume` | local | Resume a previous session. Supports entrypoints: `cli_flag`, `slash_command_picker`, `slash_command_session_id`, `slash_command_title`, `fork` |
| `/status` | local | Show current session status — model, turns, token usage, cost |

### Permission & Mode Control

| Command | Type | Description |
|---|---|---|
| `/permissions` | local | View and manage permission rules (allow/deny lists) |
| `/allowed-tools` | local | List tools currently allowed without confirmation |
| `/plan` | local | Toggle plan mode — the model can only read and analyze, not write |
| `/model` | local | Switch the active model (e.g., `claude-sonnet-4-6`, `claude-opus-4`) |

### Configuration

| Command | Type | Description |
|---|---|---|
| `/config` | local | View or modify runtime configuration |
| `/settings` | local | Open the settings file in your editor |
| `/memory` | local | View loaded CLAUDE.md files and memory entries |
| `/env` | local | Show environment variable overrides |

### Development Workflow

| Command | Type | Description |
|---|---|---|
| `/review` | prompt | Review the current diff or staged changes |
| `/commit` | prompt | Generate a commit message and create a commit |
| `/pr` | prompt | Create a pull request with generated title and body |
| `/test` | prompt | Run the project's test suite and analyze results |
| `/lint` | prompt | Run linters and fix issues |
| `/simplify` | prompt | Review changed code for reuse, quality, and efficiency |

### Code Understanding

| Command | Type | Description |
|---|---|---|
| `/explain` | prompt | Explain a file, function, or concept in the codebase |
| `/search` | prompt | Search the codebase for a pattern or concept |
| `/diagram` | prompt | Generate a mermaid diagram of architecture or flow |

### Agent & Task Management

| Command | Type | Description |
|---|---|---|
| `/agent` | local | Spawn a sub-agent with a given prompt |
| `/task` | local | Create or manage background tasks |
| `/loop` | local | Run a command on a recurring interval (e.g., `/loop 5m /test`) |
| `/schedule` | local | Create or manage scheduled remote agents (cron triggers) |

### Help & Debugging

| Command | Type | Description |
|---|---|---|
| `/help` | local | Show available commands and usage |
| `/version` | local | Show the claude-code version |
| `/debug` | local | Toggle debug mode (verbose API logging) |
| `/cost` | local | Show cumulative token usage and estimated cost |
| `/doctor` | local | Run diagnostics (API connectivity, tool health, etc.) |

## Command Anatomy

Every command is a `CommandBase` dataclass with these fields:

```python
@dataclass
class CommandBase:
    name: str = ""                  # Slash command name (without /)
    description: str = ""           # Short description
    command_type: CommandType        # local, prompt, or local-jsx
    is_hidden: bool = False         # Hidden from /help listing
    aliases: list[str] = []         # Alternative names
    argument_hint: str | None       # Placeholder for arguments
    when_to_use: str | None         # Hint for the model on when to invoke
    immediate: bool = False         # Execute without waiting for Enter
    is_sensitive: bool = False      # Redact from logs
    user_invocable: bool = True     # Can the user type this directly
    availability: list[str] = []    # "claude-ai" and/or "console"
```

## Using Commands

### Basic usage

```
> /help
```

### With arguments

```
> /commit -m "fix: resolve null pointer in query loop"
```

### Prompt commands with context

```
> /review src/claude_code/core/query.py
```

::: tip
Prompt commands are expanded into API messages before being sent to the model. The model sees the expanded content, not the raw slash command. This means prompt commands can leverage the full tool ecosystem.
:::

## Command Result Types

Local commands return one of three result types:

### TextCommandResult

```python
TextCommandResult(type="text", value="Current model: claude-sonnet-4-6")
```

Displayed directly to the user.

### CompactCommandResult

```python
CompactCommandResult(
    type="compact",
    compaction_result={"summary": "...", "token_reduction": 4200},
    display_text="Compacted conversation: saved 4,200 tokens",
)
```

Replaces the conversation history with a compacted version.

### SkipCommandResult

```python
SkipCommandResult(type="skip")
```

Command handled silently — no output shown and no message sent to the model.

## Command Availability

Some commands are restricted by user type:

- **`claude-ai`** — available to OAuth subscribers using the Claude AI service.
- **`console`** — available to users with a Console API key.
- Commands with an empty `availability` list are available to everyone.

::: warning
Commands marked `disable_non_interactive = True` cannot be used in headless/CI mode. Commands marked `supports_non_interactive = True` explicitly work in that context.
:::

# Getting Started

This guide walks you through installing `code-assist`, configuring your API key, and running your first interactive session.

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | >= 3.13 | Required — uses modern `StrEnum`, union syntax, etc. |
| uv | latest | Recommended package manager (`pip` also works) |
| Anthropic API key | — | Obtain from [console.anthropic.com](https://console.anthropic.com/) |
| Git | >= 2.30 | Optional but needed for worktree agent mode |

## Installation

### With uv (recommended)

```bash
# Clone the repository
git clone https://github.com/abhinaavramesh/code-assist.git
cd code-assist

# Install with uv
uv sync
```

### With pip

```bash
pip install code-assist
```

### Development install

```bash
uv sync --extra dev
```

This pulls in `ruff`, `mypy`, `pytest`, `pytest-asyncio`, `pytest-mock`, `respx`, and `pre-commit`.

## API Key Setup

Claude Code needs an Anthropic API key. You can provide it in three ways (checked in order):

### 1. Environment variable

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 2. Keyring (system credential store)

```bash
# Store once — code-assist reads it automatically via the `keyring` library
python -m keyring set anthropic api_key
# Paste your key at the prompt
```

### 3. Interactive prompt

If no key is found, the CLI will prompt you on first launch.

::: tip
For CI or non-interactive use, always set the environment variable. The keyring fallback requires a desktop session.
:::

## First Run

```bash
# Launch the interactive TUI
code-assist
```

You will see a prompt powered by `prompt-toolkit` and `rich`. Type a natural-language request:

```
> Explain the structure of this project and list the main modules.
```

Claude Code will:

1. Build the **system prompt** from CLAUDE.md files and core instructions.
2. Send your message to the Anthropic API (default model: `claude-sonnet-4-6`).
3. Stream the response, executing any **tool calls** (file reads, bash commands, etc.) along the way.
4. Return the final answer in your terminal.

## Basic Usage Examples

### Ask a question about your code

```
> What does the QueryEngine class do?
```

### Edit a file

```
> Add type hints to the `load_settings_file` function in src/code_assist/config/settings.py
```

### Run a command

```
> Run the test suite and tell me if anything fails
```

### Search the codebase

```
> Find all files that import pydantic and list them
```

## CLI Entry Point

The package registers a single CLI command via `pyproject.toml`:

```toml
[project.scripts]
code-assist = "code_assist.cli.main:cli"
```

This means after installation you can simply run `code-assist` anywhere on your system.

## Project Layout

```
src/code_assist/
  cli/          # Click-based CLI entry point
  config/       # Settings, constants, CLAUDE.md discovery
  core/         # QueryEngine, query loop, streaming
  memory/       # Memory file scanning and types
  services/     # Anthropic API client, tool execution
  tasks/        # Background task management
  tools/        # All built-in tools (bash, file_read, etc.)
  tui/          # Terminal UI (Textual-based)
  types/        # Shared type definitions
  utils/        # Auth, logging, cost tracking, tokens
```

## What's Next

- [Architecture](/guide/architecture) — understand the system design and data flow.
- [Tools Reference](/guide/tools) — see every built-in tool with input schemas.
- [Configuration](/guide/configuration) — customize settings, CLAUDE.md, and environment.

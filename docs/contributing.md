# Contributing

Thank you for your interest in contributing to Claude Code. This guide covers development setup, testing, code style, and the pull request process.

## Development Environment Setup

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Git 2.30+

### Clone and install

```bash
git clone https://github.com/abhinaavramesh/code-assist.git
cd code-assist

# Install with dev dependencies
uv sync --extra dev
```

This installs:

| Package | Purpose |
|---|---|
| `ruff` | Linting and formatting |
| `mypy` | Static type checking |
| `pytest` | Test runner |
| `pytest-asyncio` | Async test support |
| `pytest-cov` | Code coverage |
| `pytest-mock` | Mocking utilities |
| `respx` | HTTP mocking for `httpx` |
| `pre-commit` | Git hook management |

### Pre-commit hooks

```bash
pre-commit install
```

This sets up automatic linting and formatting on every commit.

## Project Structure

```
src/code_assist/
  cli/            # Click-based CLI entry point
  config/         # Settings, constants, CLAUDE.md discovery
  core/           # QueryEngine, query loop, streaming
  memory/         # Memory file scanning and types
  services/       # Anthropic API client, tool execution
  tasks/          # Background task management
  tools/          # All built-in tools
  tui/            # Terminal UI (Textual-based)
  types/          # Shared type definitions
  utils/          # Auth, logging, cost tracking

tests/
  test_*.py       # Test files mirror src/ structure
```

## Running Tests

### Full suite

```bash
pytest
```

### With coverage

```bash
pytest --cov=code_assist --cov-report=html
open htmlcov/index.html
```

### Specific file or test

```bash
pytest tests/test_settings.py
pytest tests/test_query_engine.py::test_submit_message
```

### Async tests

All tests use `asyncio_mode = "auto"` (configured in `pyproject.toml`), so async test functions are detected automatically:

```python
async def test_query_engine_submit():
    engine = QueryEngine(config)
    events = []
    async for event in engine.submit_message("hello"):
        events.append(event)
    assert any(isinstance(e, DoneEvent) for e in events)
```

## Code Style

### Ruff configuration

From `pyproject.toml`:

```toml
[tool.ruff]
target-version = "py313"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]
```

Selected rule sets:

| Code | Rules |
|---|---|
| `E` | pycodestyle errors |
| `F` | pyflakes |
| `I` | isort (import sorting) |
| `UP` | pyupgrade (modern Python syntax) |
| `B` | flake8-bugbear |
| `SIM` | flake8-simplicity |

### Run linting

```bash
ruff check src/ tests/
ruff format src/ tests/
```

### Mypy

```bash
mypy
```

Configuration:

```toml
[tool.mypy]
python_version = "3.13"
strict = true
warn_return_any = true
disallow_untyped_defs = true
```

All code must pass `mypy --strict`. This means:
- Every function must have type annotations.
- No `Any` types without explicit `# type: ignore` comments.
- No untyped definitions.

## Coding Conventions

### General

- Use `dataclass` for data structures, `BaseModel` for tool input schemas.
- Use `StrEnum` for string enumerations.
- Use `from __future__ import annotations` in every module (PEP 604 union syntax).
- Prefer `pathlib.Path` over `os.path`.

### Tools

- Every tool subclasses `ToolDef`.
- Input schemas are pydantic `BaseModel` subclasses.
- Tool modules live in `tools/<tool_name>/` with `__init__.py` and `<tool_name>_tool.py`.
- Always implement `is_read_only()` and `is_concurrency_safe()` accurately.

### Tests

- Mirror the `src/` directory structure in `tests/`.
- Use `pytest-mock` for mocking and `respx` for HTTP mocking.
- Prefer `async def test_*` for testing async code.
- Include both happy-path and error-case tests.

## Pull Request Guidelines

### Before submitting

1. Ensure all tests pass: `pytest`
2. Ensure linting passes: `ruff check src/ tests/`
3. Ensure formatting is correct: `ruff format --check src/ tests/`
4. Ensure types check: `mypy`

### PR structure

- **Title:** Short, descriptive (under 70 characters).
- **Description:** Explain what and why, not just what changed.
- **Tests:** Include tests for new functionality and bug fixes.
- **Breaking changes:** Call out any breaking changes explicitly.

### Commit messages

- Use present tense ("add feature" not "added feature").
- Keep the first line under 72 characters.
- Reference issues with `#123` syntax.

### Review process

1. Open a PR against `main`.
2. Automated checks (lint, type check, tests) must pass.
3. At least one approving review is required.
4. Squash and merge is the default merge strategy.

## Adding a New Tool

1. Create `src/code_assist/tools/<name>/` with `__init__.py` and `<name>_tool.py`.
2. Define a pydantic input schema.
3. Subclass `ToolDef` and implement `call()` and `input_schema`.
4. Add the tool to `tools/registry.py` in `get_all_tools()`.
5. Write tests in `tests/test_<name>_tool.py`.
6. Document the tool in `docs/guide/tools.md`.

## Adding a New Command

1. Create the command module following the `CommandBase` pattern.
2. Implement the `call()` method (for local) or `get_prompt_for_command()` (for prompt).
3. Register the command in the command registry.
4. Document the command in `docs/guide/commands.md`.

## Reporting Issues

- Use GitHub Issues for bug reports and feature requests.
- Include reproduction steps, expected behavior, and actual behavior.
- For bugs, include the Python version, OS, and relevant error output.

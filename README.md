# claude-code

AI-powered coding assistant - Python 3.13 package.

> Inspired by Claude Code. Pure research and experimentation purpose only. No enterprise use.

## Quick Start

```bash
# Install dependencies
uv sync

# Run
uv run claude-code --version

# Or via module
uv run python -m claude_code --version
```

## Development

```bash
# Install with dev dependencies
uv sync --extra dev

# Run tests
uv run pytest

# Lint
uv run ruff check src/ tests/

# Type check
uv run mypy src/claude_code/
```

## Architecture

See `docs/architecture.md` for full system design with mermaid diagrams.

## License

MIT

# claude-code

A Python 3.13 AI-powered coding assistant package.

[![Tests](https://img.shields.io/badge/tests-714%20passing-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.13+-blue)]()
[![License](https://img.shields.io/badge/license-research%20only-red)]()

> **Research and educational purposes only. No commercial use permitted.**

---

## Overview

`claude-code` is a fully-featured AI coding assistant built in Python, featuring:

- **33 tools** - File operations, shell execution, search, MCP, agents, tasks, and more
- **Interactive TUI** - Textual-based terminal UI with markdown rendering, vi mode, themes
- **Query engine** - Streaming agent loop with tool execution and context management
- **Permission system** - Configurable modes, rules, auto-approval, denial tracking
- **MCP integration** - Model Context Protocol client with stdio/SSE transports
- **Multi-agent** - Sub-agent spawning with isolated contexts and worktree support
- **Memory system** - CLAUDE.md discovery, MEMORY.md index, frontmatter parsing
- **Hooks** - PreToolUse, PostToolUse, SessionStart and 13 more event types
- **80+ slash commands** - /commit, /review, /plan, /compact, /config, and more
- **Skills & plugins** - Custom skill loading from ~/.claude/skills/

## Quick Start

```bash
# Install with uv
uv pip install -e .

# Set your API key
export ANTHROPIC_API_KEY="sk-ant-..."

# Run
claude-code --version
claude-code -p "explain this codebase"
claude-code  # interactive mode
```

## Documentation

Full documentation at **[abhinaavramesh.github.io/claude-code](https://abhinaavramesh.github.io/claude-code/)**

## Development

```bash
# Clone and install
git clone https://github.com/AbhinaavRamesh/claude-code.git
cd claude-code
uv sync --extra dev

# Run tests (714 passing)
uv run pytest

# Lint & type check
uv run ruff check src/ tests/
uv run mypy src/claude_code/

# Build docs locally
cd docs && npm install && npm run docs:dev
```

## Project Stats

| Metric | Value |
|--------|-------|
| Python files | 232 |
| Lines of code | 16,090 |
| Tools | 33 |
| Tests | 714 |
| Slash commands | 24+ |
| Doc pages | 19 |

## Architecture

```mermaid
graph TB
    CLI["CLI (click)"] --> QE["Query Engine"]
    TUI["TUI (textual)"] --> QE
    QE --> API["Anthropic API"]
    QE --> TOOLS["33 Tools"]
    QE --> COMPACT["Compaction"]
    TOOLS --> BASH["Bash"]
    TOOLS --> FILES["File R/W/Edit"]
    TOOLS --> SEARCH["Glob/Grep/Web"]
    TOOLS --> MCP["MCP Tools"]
    TOOLS --> AGENT["Agent/Tasks"]
    TOOLS --> OTHER["Plan/Config/LSP/..."]
```

---

## Credits & Attribution

> **This project is inspired by [Claude Code](https://docs.anthropic.com/en/docs/claude-code) by [Anthropic](https://www.anthropic.com/).**
>
> Claude Code is a product of Anthropic. All original concepts, design patterns, and intellectual property belong to **Anthropic and Claude**. This Python implementation is an independent educational project and is **not affiliated with, endorsed by, or connected to Anthropic in any way**.

## Disclaimer

> **This project is provided strictly for technical research, study, and educational exchange among enthusiasts.**
>
> - **Commercial use is strictly prohibited.** No individual, organization, or entity may use this content for commercial purposes, profit-making activities, or any unauthorized scenarios
> - **No enterprise deployment** is authorized
> - **All rights to the original Claude Code product are reserved by Anthropic**
> - No warranty is provided; use at your own risk
> - If any content infringes upon your legal rights, intellectual property, or other interests, please open an issue and we will verify and remove it immediately
>
> By using this software, you agree to these terms.

## License

Research and educational use only. Not for commercial use. See [Credits](#credits--attribution) and [Disclaimer](#disclaimer).

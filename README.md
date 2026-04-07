# code-assist

A Python 3.13 AI-powered coding assistant package.

**Inspired by [Claude Code](https://docs.anthropic.com/en/docs/code-assist) by [Anthropic](https://www.anthropic.com/). All original concepts and intellectual property belong to Anthropic.**

**Research and educational purposes only. No commercial use permitted.**

---

## Overview

`code-assist` is a fully-featured AI coding assistant built in Python, featuring:

- **33 tools** - File operations, shell execution, search, MCP, agents, tasks, and more
- **Interactive TUI** - Textual-based terminal UI with markdown rendering, vi mode, themes
- **Query engine** - Streaming agent loop with tool execution and context management
- **Permission system** - Configurable modes, rules, auto-approval, denial tracking
- **MCP integration** - Model Context Protocol client with stdio/SSE transports
- **Multi-agent** - Sub-agent spawning with isolated contexts and worktree support
- **Memory system** - CLAUDE.md discovery, MEMORY.md index, frontmatter parsing
- **Hooks** - PreToolUse, PostToolUse, SessionStart and 13 more event types
- **24+ slash commands** - /commit, /review, /plan, /compact, /config, and more
- **Skills & plugins** - Custom skill loading from ~/.claude/skills/

## Quick Start

```bash
pip install code-assist
```

```bash
export ANTHROPIC_API_KEY="sk-ant-..."

code-assist --version
code-assist -p "explain this codebase"
code-assist  # interactive mode
```

## Documentation

Full docs with architecture diagrams, tool reference, and API: **https://abhinaavramesh.github.io/code-assist/**

## Development

```bash
git clone https://github.com/AbhinaavRamesh/code-assist.git
cd code-assist
uv sync --extra dev
uv run pytest
```

## Credits & Attribution

This project is inspired by [Claude Code](https://docs.anthropic.com/en/docs/code-assist) by [Anthropic](https://www.anthropic.com/). Claude Code is a product of Anthropic. All original concepts, design patterns, and intellectual property belong to **Anthropic and Claude**. This Python implementation is an independent educational project and is **not affiliated with, endorsed by, or connected to Anthropic in any way**.

## Disclaimer

**This project is provided strictly for technical research, study, and educational exchange among enthusiasts.**

- **Commercial use is strictly prohibited.** No individual, organization, or entity may use this content for commercial purposes, profit-making activities, or any unauthorized scenarios
- **No enterprise deployment** is authorized
- **All rights to the original Claude Code product are reserved by Anthropic**
- No warranty is provided; use at your own risk
- If any content infringes upon your legal rights, intellectual property, or other interests, please open an issue and we will verify and remove it immediately

By using this software, you agree to these terms.

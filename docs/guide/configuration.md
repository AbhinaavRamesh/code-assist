# Configuration

Claude Code uses a layered configuration system. Settings are loaded from multiple files and merged with deep-merge semantics (higher priority wins).

## Settings File Locations

| Priority | File | Scope | Git-tracked |
|:---:|---|---|:---:|
| 4 (highest) | `.claude/settings.local.json` | Project (private) | No |
| 3 | `.claude/settings.json` | Project (shared) | Yes |
| 2 | `~/.claude/settings.json` | User (global) | No |
| 1 (lowest) | Built-in defaults | System | N/A |

The merge algorithm is recursive: nested objects are merged key-by-key, while arrays and scalars are replaced entirely by the higher-priority value.

```python
# Simplified merge logic from config/settings.py
def _deep_merge(base: dict, override: dict) -> dict:
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
```

## Full Settings Schema

```json
{
  "permissions": {
    "allow": [],
    "deny": []
  },
  "hooks": {},
  "env": {},
  "mcpServers": {},
  "advancedSettings": {
    "SKIP_GIT_INSTRUCTIONS": false,
    "CLAUDE_CODE_DISABLE_CLAUDE_MDS": false,
    "DISABLE_BACKGROUND_TASKS": false,
    "DISABLE_COMPACT": false
  },
  "plugins": [],
  "skills": {}
}
```

### Schema Reference

| Key | Type | Default | Description |
|---|---|---|---|
| `permissions.allow` | `list[str]` | `[]` | Rules for auto-approved tool uses (see [Permissions](/guide/permissions)) |
| `permissions.deny` | `list[str]` | `[]` | Rules for auto-denied tool uses |
| `hooks` | `dict[str, list]` | `{}` | Hook event handlers (see [Hooks](/guide/hooks)) |
| `env` | `dict[str, str]` | `{}` | Environment variable overrides injected at startup |
| `mcpServers` | `dict[str, object]` | `{}` | MCP server configurations (see [MCP](/guide/mcp)) |
| `advancedSettings.SKIP_GIT_INSTRUCTIONS` | `bool` | `false` | Omit git-related instructions from the system prompt |
| `advancedSettings.CLAUDE_CODE_DISABLE_CLAUDE_MDS` | `bool` | `false` | Skip loading all CLAUDE.md files |
| `advancedSettings.DISABLE_BACKGROUND_TASKS` | `bool` | `false` | Prevent background task creation |
| `advancedSettings.DISABLE_COMPACT` | `bool` | `false` | Disable automatic conversation compaction |
| `plugins` | `list[str]` | `[]` | List of plugin package names to load |
| `skills` | `dict[str, object]` | `{}` | Skill definitions (see [Skills](/guide/skills)) |

## CLAUDE.md System

CLAUDE.md files are the primary way to give Claude Code persistent instructions. They are discovered automatically and injected into the system prompt.

### File Discovery Order

1. **Managed** — `/etc/claude-code/CLAUDE.md` (organization-wide, admin-controlled)
2. **User** — `~/.claude/CLAUDE.md` (personal, applies to all projects)
3. **Project** — `CLAUDE.md` or `.claude/CLAUDE.md` in the project root
4. **Rules** — `.claude/rules/*.md` (modular project rules)
5. **Local** — `CLAUDE.local.md` in the project root (gitignored, personal overrides)

::: tip
The `MEMORY_INSTRUCTION_PROMPT` prefix tells the model that CLAUDE.md instructions override default behavior. Use this for project-specific coding conventions, forbidden patterns, or required workflows.
:::

### CLAUDE.md Format

CLAUDE.md files are plain Markdown. They are concatenated and injected into the system prompt with headers indicating their source:

```markdown
Contents of /Users/you/.claude/CLAUDE.md (user's private global instructions for all projects):

# My Preferences
- Use type hints everywhere
- Prefer dataclasses over dicts
- Run ruff before committing

Contents of /path/to/project/CLAUDE.md:

# Project Rules
- This is a Python 3.13 project using pydantic v2
- All tests use pytest-asyncio
- Never modify files in vendor/
```

### Rules Directory

For larger projects, split instructions into `.claude/rules/*.md`:

```
.claude/rules/
  code-style.md
  testing.md
  security.md
  api-conventions.md
```

Each file is loaded and appended to the system prompt.

### Size Limit

Memory files exceeding `MAX_MEMORY_CHARACTER_COUNT` (40,000 characters) are flagged. You can detect oversized files with:

```python
from claude_code.config.claude_md import get_memory_files, get_large_memory_files

files = get_memory_files("/path/to/project")
large = get_large_memory_files(files)
for f in large:
    print(f"Warning: {f.path} is {f.size} chars (limit: 40,000)")
```

## Environment Variables

### Set via settings.json

```json
{
  "env": {
    "ANTHROPIC_API_KEY": "sk-ant-...",
    "PYTHONPATH": "/extra/lib",
    "MY_CUSTOM_VAR": "value"
  }
}
```

These are injected into the process environment at startup.

### Built-in Environment Variables

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | API key for the Anthropic service |
| `USER_TYPE` | User type: `external` (default) or `internal` |
| `CODE_ASSIST_<NAME>` | Feature flags (set to `1` or `true` to enable) |

### Feature Flags

Feature flags are checked via `is_feature_enabled(name)`:

```python
from claude_code.config.constants import is_feature_enabled

if is_feature_enabled("EXPERIMENTAL_TOOLS"):
    # Enable experimental tool set
    ...
```

The function reads `CODE_ASSIST_<NAME>` from the environment.

## Example Configurations

### Minimal (defaults only)

No settings files needed. Claude Code uses built-in defaults with the `default` permission mode.

### Python Development

**`~/.claude/settings.json`** (global):
```json
{
  "permissions": {
    "allow": [
      "FileRead",
      "GlobTool",
      "GrepTool"
    ]
  }
}
```

**`.claude/settings.json`** (project):
```json
{
  "permissions": {
    "allow": [
      "Bash(pytest *)",
      "Bash(ruff check *)",
      "Bash(ruff format *)",
      "Bash(mypy *)",
      "Bash(python -m *)",
      "FileWrite",
      "FileEdit"
    ],
    "deny": [
      "Bash(pip install *)"
    ]
  },
  "env": {
    "PYTHONPATH": "src"
  },
  "advancedSettings": {
    "SKIP_GIT_INSTRUCTIONS": false
  }
}
```

### CI / Non-Interactive

**`.claude/settings.local.json`**:
```json
{
  "permissions": {
    "allow": [
      "FileRead",
      "GlobTool",
      "GrepTool",
      "Bash(pytest *)"
    ],
    "deny": [
      "Bash(*)",
      "FileWrite",
      "FileEdit",
      "WebFetchTool",
      "WebSearchTool"
    ]
  },
  "advancedSettings": {
    "DISABLE_BACKGROUND_TASKS": true,
    "DISABLE_COMPACT": true
  }
}
```

### With MCP Servers

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/allowed/path"],
      "env": {}
    },
    "database": {
      "command": "python",
      "args": ["-m", "my_db_mcp_server"],
      "env": {
        "DB_URL": "postgresql://localhost/mydb"
      }
    }
  }
}
```

## Programmatic Access

```python
from claude_code.config.settings import (
    load_merged_settings,
    get_permission_rules,
    get_hooks_settings,
    get_mcp_servers,
    get_env_vars,
    get_advanced_setting,
)

settings = load_merged_settings("/path/to/project")

allow_rules = get_permission_rules(settings, "allow")
deny_rules = get_permission_rules(settings, "deny")
hooks = get_hooks_settings(settings)
mcp = get_mcp_servers(settings)
env = get_env_vars(settings)
skip_git = get_advanced_setting(settings, "SKIP_GIT_INSTRUCTIONS", False)
```

# Skills & Plugins

Claude Code is extensible through two mechanisms: **skills** (reusable prompt-based workflows) and **plugins** (code packages that contribute tools, commands, and hooks).

## Skills Overview

Skills are named workflows that can be invoked as slash commands. They bundle a prompt, allowed tools, model preferences, and execution context into a reusable unit.

### What a Skill Is

A skill is essentially a specialized prompt command with:

- A **name** (used as `/name` in the CLI)
- A **prompt** (the instructions sent to the model)
- Optional **tool restrictions** (which tools the model can use)
- Optional **model override** (use a different model for this skill)
- Optional **execution context** (`inline` or `fork`)

### Skill Configuration

Skills are defined in `settings.json` under the `skills` key:

```json
{
  "skills": {
    "review-pr": {
      "description": "Review a pull request for bugs and style issues",
      "prompt": "Review the current pull request. Check for bugs, security issues, and style violations. Provide actionable feedback.",
      "allowedTools": ["FileRead", "GlobTool", "GrepTool", "Bash(git diff *)"],
      "model": "claude-sonnet-4-6",
      "context": "inline"
    },
    "write-tests": {
      "description": "Generate tests for a module",
      "prompt": "Write comprehensive tests for the specified module. Use pytest with async support. Cover edge cases.",
      "allowedTools": null,
      "context": "fork"
    }
  }
}
```

### Skill Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `description` | `str` | Yes | Short description shown in `/help` |
| `prompt` | `str` | Yes | The prompt sent to the model |
| `allowedTools` | `list[str] \| null` | No | Tools the model can use (`null` = all) |
| `model` | `str \| null` | No | Model override for this skill |
| `context` | `"inline" \| "fork"` | No | Run inline or in a forked agent |
| `agent` | `str \| null` | No | Agent template to use |
| `effort` | `str \| null` | No | Effort level hint |
| `paths` | `list[str] \| null` | No | File paths relevant to the skill |
| `argNames` | `list[str] \| null` | No | Named arguments the skill accepts |

### Using Skills

```
> /review-pr
> /write-tests src/code_assist/core/query.py
```

Skills appear alongside built-in commands in the `/help` listing and in autocomplete.

## Custom Skill Creation

### 1. Add to settings.json

```json
{
  "skills": {
    "explain-error": {
      "description": "Explain a Python traceback",
      "prompt": "The user will provide a Python traceback. Explain the root cause, suggest a fix, and show the corrected code.",
      "allowedTools": ["FileRead", "GlobTool", "GrepTool"]
    }
  }
}
```

### 2. Skill with arguments

```json
{
  "skills": {
    "migrate-function": {
      "description": "Migrate a function to async",
      "prompt": "Convert the function at the specified path from synchronous to asynchronous. Update all callers.",
      "argNames": ["path"],
      "allowedTools": ["FileRead", "FileEdit", "GlobTool", "GrepTool"]
    }
  }
}
```

Usage: `/migrate-function src/code_assist/config/settings.py`

### 3. Skill with forked context

```json
{
  "skills": {
    "experiment": {
      "description": "Try an experimental approach",
      "prompt": "Explore the approach described by the user. This runs in a fork so it won't affect the main conversation.",
      "context": "fork"
    }
  }
}
```

## Skill Storage

User-created skills can also be stored as files in `~/.claude/skills/`:

```
~/.claude/skills/
  review-pr.json
  write-tests.json
  explain-error.json
```

Each file is a JSON object with the same schema as a skill entry in `settings.json`.

## Bundled Skills

Claude Code ships with several built-in skills:

| Skill | Description |
|---|---|
| `simplify` | Review changed code for reuse, quality, and efficiency |
| `commit` | Generate a commit message and create a git commit |
| `review-pr` | Review a pull request |
| `loop` | Run a command on a recurring interval |
| `schedule` | Create scheduled remote agents (cron triggers) |
| `claude-api` | Help build apps with the Anthropic SDK |
| `frontend-design` | Create production-grade frontend interfaces |

Bundled skills are loaded from `CommandLoadedFrom.BUNDLED` and cannot be overridden by user skills with the same name (user skills take priority through the merge order).

## Plugin System

Plugins are Python packages that extend Claude Code with custom tools, commands, and hooks.

### Plugin Manifest

Every plugin declares a `PluginManifest`:

```python
@dataclass
class PluginManifest:
    name: str = ""              # Plugin name
    version: str = ""           # Semantic version
    description: str = ""       # What this plugin does
    repository: str = ""        # Source repository URL
    author: str = ""            # Author name
    hooks: dict = {}            # Hook event -> handler mappings
    tools: list[str] = []       # Tool class names to register
    commands: list[str] = []    # Command names to register
    settings: dict = {}         # Default settings contributed by the plugin
```

### Loading Plugins

Plugins are listed in `settings.json`:

```json
{
  "plugins": [
    "my-code-assist-plugin",
    "another-plugin"
  ]
}
```

Each plugin is loaded and produces a `LoadedPlugin`:

```python
@dataclass
class LoadedPlugin:
    manifest: PluginManifest    # The plugin's declared capabilities
    path: str = ""              # Filesystem path where the plugin was found
    source: str = ""            # How it was discovered
    is_active: bool = True      # Whether it is currently active
    error: str | None = None    # Load error, if any
```

### Creating a Plugin

1. **Create a Python package** with a `code_assist_plugin` entry point:

```toml
# pyproject.toml
[project.entry-points."code_assist.plugins"]
my_plugin = "my_plugin:manifest"
```

2. **Define the manifest**:

```python
# my_plugin/__init__.py
from code_assist.types.plugin import PluginManifest

manifest = PluginManifest(
    name="my-plugin",
    version="1.0.0",
    description="Adds custom tools for my workflow",
    author="Your Name",
    tools=["MyCustomTool"],
    commands=["my-command"],
)
```

3. **Implement tools and commands** following the standard `ToolDef` and `CommandBase` patterns.

4. **Install the package** in the same environment as code-assist:

```bash
uv pip install -e ./my-plugin
```

### Plugin Settings

Plugins can contribute default settings that are merged into the settings hierarchy:

```python
manifest = PluginManifest(
    name="my-plugin",
    settings={
        "myPlugin": {
            "apiUrl": "https://api.example.com",
            "timeout": 30,
        }
    },
)
```

These appear under their key in the merged settings and can be overridden by user/project/local settings.

## Command Loading Sources

Commands (including skill-generated ones) are tracked by their source:

| Source | Enum Value | Description |
|---|---|---|
| Bundled | `bundled` | Ships with code-assist core |
| Managed | `managed` | Organization-managed commands |
| Skills | `skills` | User-defined skills from settings.json |
| Plugin | `plugin` | Loaded from installed plugins |
| MCP | `mcp` | Provided by MCP servers |

::: tip
Skills are the easiest way to extend Claude Code for your workflow. Start with a skill before building a full plugin — most use cases can be covered by a well-crafted prompt with tool restrictions.
:::

::: warning
Plugins run with the same privileges as Claude Code itself. Only install plugins from trusted sources. Review the plugin manifest to understand which tools, hooks, and commands it registers.
:::

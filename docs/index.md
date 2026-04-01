---
layout: home

hero:
  name: Claude Code
  text: AI-Powered Coding Assistant
  tagline: A Python 3.13 implementation of an agentic coding assistant with tool use, memory, and multi-agent orchestration.
  actions:
    - theme: brand
      text: Get Started
      link: /guide/getting-started
    - theme: alt
      text: View on GitHub
      link: https://github.com/abhinaavramesh/claude-code

features:
  - icon: "\U0001F527"
    title: Rich Tool Ecosystem
    details: 10+ built-in tools covering file I/O, bash execution, search, web access, and notebook editing — all with pydantic-validated inputs and permission controls.
  - icon: "\U0001F9E0"
    title: Memory & Context
    details: Hierarchical CLAUDE.md system with managed, user, project, and local layers. Memory files are auto-discovered and injected into the system prompt.
  - icon: "\U0001F916"
    title: Multi-Agent Architecture
    details: Spawn sub-agents in isolated contexts — default, fork, or worktree modes — with full tool access and coordinated task management.
  - icon: "\U0001F50C"
    title: MCP Integration
    details: First-class Model Context Protocol support. Connect external MCP servers to extend tool and resource capabilities without modifying core code.
  - icon: "\U0001F6E1\uFE0F"
    title: Granular Permissions
    details: Six permission modes from plan-only to full bypass, with rule-based allow/deny lists, hook-driven overrides, and safety classifiers.
  - icon: "\U0001F3AF"
    title: Extensible Hooks & Skills
    details: Hook into 16 lifecycle events to run shell commands, modify tool inputs/outputs, or gate permissions. Bundle reusable workflows as skills.
  - icon: "\U0001F4CA"
    title: Streaming Event API
    details: Async generator-based QueryEngine yields typed events (text, tool_use, tool_result, done) for real-time UI integration.
  - icon: "\u2699\uFE0F"
    title: Deep Configuration
    details: Three-tier settings merge (global, project, local) with environment variable overrides, advanced feature flags, and per-tool permission rules.
---

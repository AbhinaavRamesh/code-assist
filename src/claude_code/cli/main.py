"""Click CLI entry point."""

from __future__ import annotations

import asyncio
import sys
from typing import Any

import click

from claude_code import __version__


@click.command()
@click.version_option(version=__version__, prog_name="claude-code")
@click.option("--model", "-m", default=None, help="Model to use (e.g., sonnet, opus, haiku)")
@click.option("--print", "-p", "print_mode", is_flag=True, help="Non-interactive print mode")
@click.option("--prompt", default=None, help="Initial prompt (with --print)")
@click.option("--resume", default=None, help="Resume a previous session")
@click.option("--permission-mode", default=None, help="Permission mode (default, acceptEdits, bypassPermissions)")
@click.option("--output-format", default="text", help="Output format (text, json, ndjson)")
@click.option("--max-turns", default=None, type=int, help="Maximum conversation turns")
@click.option("--system-prompt", default=None, help="Custom system prompt")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--debug", is_flag=True, help="Debug mode")
@click.argument("prompt_text", required=False, default=None)
def cli(
    model: str | None,
    print_mode: bool,
    prompt: str | None,
    resume: str | None,
    permission_mode: str | None,
    output_format: str,
    max_turns: int | None,
    system_prompt: str | None,
    verbose: bool,
    debug: bool,
    prompt_text: str | None,
) -> None:
    """Claude Code - AI-powered coding assistant."""
    from claude_code.utils.log import setup_logging

    setup_logging(verbose=verbose, debug=debug)

    # Determine the prompt
    initial_prompt = prompt or prompt_text

    if print_mode and initial_prompt:
        asyncio.run(_run_print_mode(initial_prompt, model=model, system_prompt=system_prompt))
    elif initial_prompt:
        asyncio.run(_run_single_query(initial_prompt, model=model, system_prompt=system_prompt))
    else:
        _run_interactive(model=model, verbose=verbose)


async def _run_print_mode(
    prompt: str,
    *,
    model: str | None = None,
    system_prompt: str | None = None,
) -> None:
    """Non-interactive print mode - single query, output to stdout."""
    from claude_code.core.query import TextEvent
    from claude_code.core.query_engine import QueryEngine, QueryEngineConfig

    config = QueryEngineConfig(
        model=model or "claude-sonnet-4-6",
        custom_system_prompt=system_prompt,
    )
    engine = QueryEngine(config)

    async for event in engine.submit_message(prompt):
        if isinstance(event, TextEvent):
            print(event.text, end="", flush=True)

    print()  # Final newline


async def _run_single_query(
    prompt: str,
    *,
    model: str | None = None,
    system_prompt: str | None = None,
) -> None:
    """Run a single query with rich output."""
    from rich.console import Console

    from claude_code.core.query import TextEvent, ToolUseEvent, DoneEvent
    from claude_code.core.query_engine import QueryEngine, QueryEngineConfig

    console = Console()
    config = QueryEngineConfig(
        model=model or "claude-sonnet-4-6",
        custom_system_prompt=system_prompt,
    )
    engine = QueryEngine(config)

    async for event in engine.submit_message(prompt):
        if isinstance(event, TextEvent):
            console.print(event.text, end="")
        elif isinstance(event, ToolUseEvent):
            console.print(f"\n[dim]Using {event.tool_name}...[/dim]")
        elif isinstance(event, DoneEvent):
            console.print(f"\n[dim]({event.total_turns} turns)[/dim]")


def _run_interactive(
    *,
    model: str | None = None,
    verbose: bool = False,
) -> None:
    """Run interactive REPL mode."""
    from rich.console import Console

    console = Console()
    console.print(f"[bold]Claude Code v{__version__}[/bold]")
    console.print("[dim]Type /help for commands, Ctrl+C to exit[/dim]\n")

    # Simple REPL (full TUI in Branch 18)
    try:
        while True:
            try:
                user_input = input("> ")
            except EOFError:
                break

            if not user_input.strip():
                continue
            if user_input.strip() in ("/exit", "/quit"):
                break

            asyncio.run(_run_single_query(user_input, model=model))
    except KeyboardInterrupt:
        console.print("\n[dim]Goodbye![/dim]")


if __name__ == "__main__":
    cli()

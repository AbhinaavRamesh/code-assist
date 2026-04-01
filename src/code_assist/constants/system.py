"""System prompt constants and query source definitions."""

from __future__ import annotations

from enum import StrEnum


class QuerySource(StrEnum):
    """Source of API queries for tracking and caching."""

    REPL_MAIN_THREAD = "repl_main_thread"
    AGENT_CUSTOM = "agent:custom"
    AGENT_CREATION = "agent_creation"
    AGENT_SUMMARY = "agent_summary"
    AUTO_MODE = "auto_mode"
    AUTO_MODE_CRITIQUE = "auto_mode_critique"
    AWAY_SUMMARY = "away_summary"
    BASH_EXTRACT_PREFIX = "bash_extract_prefix"
    COMPACT = "compact"
    EXTRACT_MEMORIES = "extract_memories"
    FEEDBACK = "feedback"
    GENERATE_SESSION_TITLE = "generate_session_title"
    HOOK_AGENT = "hook_agent"
    HOOK_PROMPT = "hook_prompt"
    INSIGHTS = "insights"
    MEMDIR_RELEVANCE = "memdir_relevance"
    MODEL_VALIDATION = "model_validation"
    PERMISSION_EXPLAINER = "permission_explainer"
    PROMPT_SUGGESTION = "prompt_suggestion"
    SDK = "sdk"
    SESSION_MEMORY = "session_memory"
    SESSION_SEARCH = "session_search"
    SIDE_QUESTION = "side_question"
    SKILL_IMPROVEMENT_APPLY = "skill_improvement_apply"
    SPECULATION = "speculation"
    TOOL_USE_SUMMARY_GENERATION = "tool_use_summary_generation"
    WEB_FETCH_APPLY = "web_fetch_apply"
    WEB_SEARCH_TOOL = "web_search_tool"
    VERIFICATION_AGENT = "verification_agent"
    MEMORY_EXTRACTION = "memory_extraction"


def is_agent_query_source(source: str) -> bool:
    """Check if a query source is from an agent."""
    return source.startswith("agent:")

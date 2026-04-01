"""Tests for API client, error classification, model/cost utilities."""

import anthropic
import pytest

from code_assist.services.api.claude import (
    APIClientConfig,
    SystemPromptBlock,
    build_system_prompt_param,
    extract_usage,
    get_default_betas,
    tool_to_api_schema,
)
from code_assist.services.api.errors import (
    APIErrorType,
    ClassifiedError,
    _extract_token_counts,
    classify_api_error,
)
from code_assist.state.bootstrap import reset_bootstrap_state
from code_assist.types.message import Usage
from code_assist.utils.context import get_available_tokens, should_compact
from code_assist.utils.cost_tracker import format_cost, track_usage
from code_assist.utils.model.cost import (
    calculate_cost_usd,
    get_context_window,
    get_max_output_tokens,
    get_pricing,
)
from code_assist.utils.model.model import (
    get_display_name,
    is_opus_model,
    is_sonnet_model,
    resolve_model,
)
from code_assist.utils.model.providers import APIProvider, detect_provider
from code_assist.utils.tokens import rough_token_estimate


class TestAPIConfig:
    def test_default_betas(self) -> None:
        betas = get_default_betas()
        assert len(betas) >= 2
        assert any("context" in b for b in betas)

    def test_api_client_config_defaults(self) -> None:
        config = APIClientConfig()
        assert config.model == "claude-sonnet-4-20250514"
        assert config.max_tokens == 16384
        assert config.timeout == 600.0

    def test_build_system_prompt(self) -> None:
        prompt = [
            SystemPromptBlock(text="You are helpful."),
            SystemPromptBlock(
                text="Context here.",
                cache_control={"type": "ephemeral"},
            ),
        ]
        result = build_system_prompt_param(prompt)
        assert len(result) == 2
        assert result[0]["text"] == "You are helpful."
        assert "cache_control" not in result[0]
        assert result[1]["cache_control"] == {"type": "ephemeral"}

    def test_tool_to_api_schema(self) -> None:
        schema = tool_to_api_schema(
            "bash",
            "Execute a shell command",
            {"type": "object", "properties": {"command": {"type": "string"}}},
            strict=True,
        )
        assert schema["name"] == "bash"
        assert schema["strict"] is True


def _make_httpx_response(status_code: int) -> "httpx.Response":
    """Create a minimal httpx.Response for testing."""
    import httpx

    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    return httpx.Response(status_code=status_code, request=request)


class TestErrorClassification:
    def test_classify_auth_error(self) -> None:
        error = anthropic.AuthenticationError(
            message="Invalid API key",
            response=_make_httpx_response(401),
            body=None,
        )
        result = classify_api_error(error)
        assert result.error_type == APIErrorType.AUTHENTICATION_FAILED

    def test_classify_rate_limit(self) -> None:
        error = anthropic.RateLimitError(
            message="Rate limited",
            response=_make_httpx_response(429),
            body=None,
        )
        result = classify_api_error(error)
        assert result.error_type == APIErrorType.RATE_LIMIT
        assert result.is_retryable is True

    def test_classify_connection_error(self) -> None:
        import httpx

        request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
        error = anthropic.APIConnectionError(request=request)
        result = classify_api_error(error)
        assert result.error_type == APIErrorType.CONNECTION_ERROR
        assert result.is_retryable is True

    def test_extract_token_counts(self) -> None:
        msg = "prompt is too long: 250,000 tokens > limit of 200,000"
        actual, limit = _extract_token_counts(msg)
        assert actual == 250000
        assert limit == 200000

    def test_extract_token_counts_no_match(self) -> None:
        actual, limit = _extract_token_counts("some other error")
        assert actual is None
        assert limit is None


class TestModelCost:
    def test_get_pricing_known(self) -> None:
        pricing = get_pricing("claude-sonnet-4-20250514")
        assert pricing.input_per_mtok == 3.0
        assert pricing.output_per_mtok == 15.0

    def test_get_pricing_unknown(self) -> None:
        pricing = get_pricing("unknown-model")
        assert pricing.input_per_mtok > 0  # Falls back to default

    def test_calculate_cost(self) -> None:
        cost = calculate_cost_usd(
            "claude-sonnet-4-20250514",
            input_tokens=1_000_000,
            output_tokens=100_000,
        )
        assert cost == pytest.approx(3.0 + 1.5)  # $3 input + $1.5 output

    def test_context_window(self) -> None:
        assert get_context_window("claude-opus-4-6") == 1_000_000
        assert get_context_window("claude-sonnet-4-20250514") == 200_000

    def test_max_output_tokens(self) -> None:
        assert get_max_output_tokens("claude-opus-4-6") == 32768


class TestModelNames:
    def test_resolve_alias(self) -> None:
        assert resolve_model("sonnet") == "claude-sonnet-4-6"
        assert resolve_model("opus") == "claude-opus-4-6"

    def test_resolve_full_name(self) -> None:
        full = "claude-sonnet-4-20250514"
        assert resolve_model(full) == full

    def test_display_name(self) -> None:
        assert get_display_name("claude-opus-4-6") == "Opus 4.6"

    def test_model_family_checks(self) -> None:
        assert is_opus_model("claude-opus-4-6")
        assert is_sonnet_model("claude-sonnet-4-20250514")
        assert not is_opus_model("claude-sonnet-4-20250514")


class TestProviders:
    def test_default_provider(self) -> None:
        provider = detect_provider()
        assert provider == APIProvider.ANTHROPIC


class TestCostTracker:
    def setup_method(self) -> None:
        reset_bootstrap_state()

    def test_track_usage(self) -> None:
        usage = Usage(input_tokens=1000, output_tokens=500)
        cost = track_usage("claude-sonnet-4-20250514", usage)
        assert cost > 0

    def test_format_cost(self) -> None:
        assert format_cost(1.50) == "$1.50"
        assert format_cost(0.005) == "$0.0050"


class TestTokens:
    def test_rough_estimate(self) -> None:
        assert rough_token_estimate("hello world") >= 1
        assert rough_token_estimate("a" * 400) == 100


class TestContext:
    def test_available_tokens(self) -> None:
        available = get_available_tokens("claude-sonnet-4-20250514", used_tokens=50000)
        assert available > 0
        assert available < 200000

    def test_should_compact(self) -> None:
        assert should_compact("claude-sonnet-4-20250514", used_tokens=180000)
        assert not should_compact("claude-sonnet-4-20250514", used_tokens=50000)


class TestUsageExtraction:
    def test_extract_none(self) -> None:
        usage = extract_usage(None)
        assert usage.input_tokens == 0

    def test_extract_from_object(self) -> None:
        obj = type("U", (), {
            "input_tokens": 100,
            "output_tokens": 50,
            "cache_read_input_tokens": 10,
            "cache_creation_input_tokens": 5,
        })()
        usage = extract_usage(obj)
        assert usage.input_tokens == 100
        assert usage.output_tokens == 50

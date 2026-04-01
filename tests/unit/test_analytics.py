"""Tests for analytics: event sink, feature flags, configuration."""

import pytest

from claude_code.services.analytics.config import (
    get_analytics_endpoint,
    is_analytics_enabled,
)
from claude_code.services.analytics.growthbook import FeatureFlags, get_feature_flags
from claude_code.services.analytics.sink import (
    AnalyticsEvent,
    AnalyticsSink,
    log_event,
)


# ---------------------------------------------------------------------------
# Config Tests
# ---------------------------------------------------------------------------


class TestAnalyticsConfig:
    def test_enabled_by_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("CODE_ASSIST_DISABLE_ANALYTICS", raising=False)
        assert is_analytics_enabled() is True

    def test_disabled_with_1(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CODE_ASSIST_DISABLE_ANALYTICS", "1")
        assert is_analytics_enabled() is False

    def test_disabled_with_true(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CODE_ASSIST_DISABLE_ANALYTICS", "true")
        assert is_analytics_enabled() is False

    def test_disabled_case_insensitive(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CODE_ASSIST_DISABLE_ANALYTICS", "TRUE")
        assert is_analytics_enabled() is False

    def test_enabled_with_other_value(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CODE_ASSIST_DISABLE_ANALYTICS", "no")
        assert is_analytics_enabled() is True

    def test_endpoint_default_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("CODE_ASSIST_ANALYTICS_URL", raising=False)
        assert get_analytics_endpoint() == ""

    def test_endpoint_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CODE_ASSIST_ANALYTICS_URL", "https://example.com/events")
        assert get_analytics_endpoint() == "https://example.com/events"


# ---------------------------------------------------------------------------
# Sink Tests
# ---------------------------------------------------------------------------


class TestAnalyticsEvent:
    def test_defaults(self) -> None:
        event = AnalyticsEvent()
        assert event.name == ""
        assert event.properties == {}
        assert event.session_id is None
        assert event.timestamp > 0

    def test_custom_values(self) -> None:
        event = AnalyticsEvent(
            name="test_event",
            properties={"key": "value"},
            session_id="sess-123",
        )
        assert event.name == "test_event"
        assert event.properties == {"key": "value"}
        assert event.session_id == "sess-123"


class TestAnalyticsSink:
    def test_log_event(self) -> None:
        sink = AnalyticsSink()
        sink.log_event("click", {"button": "ok"})
        assert sink.event_count == 1

    def test_log_event_with_session(self) -> None:
        sink = AnalyticsSink()
        sink.log_event("click", session_id="s1")
        events = sink.flush()
        assert len(events) == 1
        assert events[0].session_id == "s1"

    def test_flush_returns_and_clears(self) -> None:
        sink = AnalyticsSink()
        sink.log_event("a")
        sink.log_event("b")
        assert sink.event_count == 2

        events = sink.flush()
        assert len(events) == 2
        assert sink.event_count == 0

    def test_disable_stops_logging(self) -> None:
        sink = AnalyticsSink()
        sink.disable()
        sink.log_event("ignored")
        assert sink.event_count == 0

    def test_properties_default_to_empty_dict(self) -> None:
        sink = AnalyticsSink()
        sink.log_event("test")
        events = sink.flush()
        assert events[0].properties == {}

    def test_flush_returns_copies(self) -> None:
        sink = AnalyticsSink()
        sink.log_event("x")
        events = sink.flush()
        # Flushing again returns empty, original list still intact
        assert sink.flush() == []
        assert len(events) == 1


class TestModuleLevelLogEvent:
    def test_log_event_via_module(self) -> None:
        """Test the module-level log_event convenience function."""
        import claude_code.services.analytics.sink as sink_mod

        sink_mod._sink = None
        log_event("module_event", {"source": "test"})
        sink = sink_mod.get_analytics_sink()
        assert sink.event_count == 1
        events = sink.flush()
        assert events[0].name == "module_event"
        assert events[0].properties == {"source": "test"}
        sink_mod._sink = None


# ---------------------------------------------------------------------------
# Feature Flag Tests
# ---------------------------------------------------------------------------


class TestFeatureFlags:
    def test_empty_flags(self) -> None:
        ff = FeatureFlags()
        assert ff.is_on("anything") is False
        assert ff.get_value("anything") is None

    def test_set_and_check_flags(self) -> None:
        ff = FeatureFlags()
        ff.set_flags({"new_ui": True, "beta_mode": False})
        assert ff.is_on("new_ui") is True
        assert ff.is_on("beta_mode") is False

    def test_default_value(self) -> None:
        ff = FeatureFlags()
        assert ff.is_on("missing", default=True) is True
        assert ff.get_value("missing", default=42) == 42

    def test_get_value(self) -> None:
        ff = FeatureFlags()
        ff.set_flags({"threshold": 0.75})
        assert ff.get_value("threshold") == 0.75

    def test_is_on_truthy_values(self) -> None:
        ff = FeatureFlags()
        ff.set_flags({"a": 1, "b": "yes", "c": [], "d": ""})
        assert ff.is_on("a") is True
        assert ff.is_on("b") is True
        assert ff.is_on("c") is False  # empty list is falsy
        assert ff.is_on("d") is False  # empty string is falsy


class TestGetFeatureFlags:
    def test_singleton(self) -> None:
        """get_feature_flags returns the same instance."""
        import claude_code.services.analytics.growthbook as gb_mod

        gb_mod._flags = None
        ff1 = get_feature_flags()
        ff2 = get_feature_flags()
        assert ff1 is ff2
        gb_mod._flags = None

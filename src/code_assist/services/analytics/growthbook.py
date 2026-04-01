"""Feature flag evaluation (GrowthBook-compatible)."""

from typing import Any


class FeatureFlags:
    """Simple feature flag store."""

    def __init__(self) -> None:
        self._flags: dict[str, Any] = {}

    def set_flags(self, flags: dict[str, Any]) -> None:
        self._flags = flags

    def is_on(self, key: str, default: bool = False) -> bool:
        val = self._flags.get(key)
        if val is None:
            return default
        return bool(val)

    def get_value(self, key: str, default: Any = None) -> Any:
        return self._flags.get(key, default)


_flags: FeatureFlags | None = None


def get_feature_flags() -> FeatureFlags:
    global _flags  # noqa: PLW0603
    if _flags is None:
        _flags = FeatureFlags()
    return _flags

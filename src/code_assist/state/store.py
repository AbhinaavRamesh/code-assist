"""Generic reactive store with pub-sub pattern.

Generic reactive store with pub-sub pattern.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Generic, TypeVar

T = TypeVar("T")

Listener = Callable[[], None]
OnChange = Callable[[T, T], None]  # (new_state, old_state)


class Store(Generic[T]):
    """Generic reactive state store with subscriber notifications.

    Generic reactive store with subscriber notifications.
    Uses identity comparison (is) to detect state changes.
    """

    def __init__(
        self,
        initial_state: T,
        on_change: OnChange[T] | None = None,
    ) -> None:
        self._state = initial_state
        self._listeners: set[Listener] = set()
        self._on_change = on_change

    def get_state(self) -> T:
        """Return the current state."""
        return self._state

    def set_state(self, updater: Callable[[T], T]) -> None:
        """Update state via updater function.

        Only triggers listeners if the new state is different (identity check).
        """
        prev = self._state
        next_state = updater(prev)
        if next_state is prev:
            return
        self._state = next_state
        if self._on_change is not None:
            self._on_change(next_state, prev)
        for listener in list(self._listeners):
            listener()

    def subscribe(self, listener: Listener) -> Callable[[], None]:
        """Register a listener. Returns an unsubscribe function."""
        self._listeners.add(listener)

        def unsubscribe() -> None:
            self._listeners.discard(listener)

        return unsubscribe


def create_store(
    initial_state: T,
    on_change: OnChange[T] | None = None,
) -> Store[T]:
    """Create a new reactive store. Matches TS createStore<T>()."""
    return Store(initial_state, on_change)

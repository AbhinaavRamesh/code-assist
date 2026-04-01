"""Tests for the reactive store."""

from claude_code.state.store import Store, create_store


class TestStore:
    def test_get_initial_state(self) -> None:
        store: Store[int] = create_store(42)
        assert store.get_state() == 42

    def test_set_state(self) -> None:
        store: Store[int] = create_store(0)
        store.set_state(lambda prev: prev + 1)
        assert store.get_state() == 1

    def test_no_notification_when_state_unchanged(self) -> None:
        store: Store[dict[str, int]] = create_store({"a": 1})
        calls: list[int] = []
        store.subscribe(lambda: calls.append(1))
        # Return same object -> no notification
        store.set_state(lambda prev: prev)
        assert len(calls) == 0

    def test_notification_on_state_change(self) -> None:
        store: Store[int] = create_store(0)
        calls: list[int] = []
        store.subscribe(lambda: calls.append(1))
        store.set_state(lambda prev: prev + 1)
        assert len(calls) == 1

    def test_unsubscribe(self) -> None:
        store: Store[int] = create_store(0)
        calls: list[int] = []
        unsub = store.subscribe(lambda: calls.append(1))
        store.set_state(lambda _: 1)
        assert len(calls) == 1
        unsub()
        store.set_state(lambda _: 2)
        assert len(calls) == 1  # No more notifications

    def test_on_change_callback(self) -> None:
        changes: list[tuple[int, int]] = []

        def on_change(new: int, old: int) -> None:
            changes.append((new, old))

        store: Store[int] = create_store(0, on_change)
        store.set_state(lambda _: 5)
        assert changes == [(5, 0)]

    def test_multiple_subscribers(self) -> None:
        store: Store[int] = create_store(0)
        calls_a: list[int] = []
        calls_b: list[int] = []
        store.subscribe(lambda: calls_a.append(1))
        store.subscribe(lambda: calls_b.append(1))
        store.set_state(lambda _: 1)
        assert len(calls_a) == 1
        assert len(calls_b) == 1

    def test_dict_state(self) -> None:
        store: Store[dict[str, int]] = create_store({"count": 0})
        store.set_state(lambda prev: {**prev, "count": prev["count"] + 1})
        assert store.get_state()["count"] == 1

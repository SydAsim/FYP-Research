"""Explicit wait/release controls for each research timing boundary."""

from collections.abc import Callable
from datetime import UTC, datetime
from threading import Condition
from uuid import UUID

from research.run_store import record_barrier, release_barrier
from research.scenario_dsl.models import Barrier


class NamedBarrierController:
    """Block only configured barriers, with a durable reach and release record."""

    def __init__(
        self,
        execution_id: UUID,
        held: set[Barrier],
        *,
        persist_reach: Callable[..., UUID] = record_barrier,
        persist_release: Callable[[UUID], None] = release_barrier,
    ) -> None:
        self.execution_id = execution_id
        self.held = frozenset(held)
        self._persist_reach = persist_reach
        self._persist_release = persist_release
        self._condition = Condition()
        self._reached: dict[Barrier, UUID] = {}
        self._released: set[Barrier] = set()

    def reach(self, barrier: Barrier, source_event_id: str, timeout: float = 40) -> UUID:
        """Persist the exact boundary, then wait for an explicit release if held."""
        with self._condition:
            if barrier in self._reached:
                raise ValueError(f"{barrier.value} has already been reached")
            event_id = self._persist_reach(
                self.execution_id,
                barrier.value,
                source_event_id,
                datetime.now(UTC),
                held=barrier in self.held,
            )
            self._reached[barrier] = event_id
            if barrier not in self.held:
                self._released.add(barrier)
            self._condition.notify_all()
            if barrier in self.held and not self._condition.wait_for(
                lambda: barrier in self._released, timeout=timeout
            ):
                raise TimeoutError(f"{barrier.value} was reached but not released")
            return event_id

    def wait_reached(self, barrier: Barrier, timeout: float = 40) -> UUID:
        with self._condition:
            if not self._condition.wait_for(lambda: barrier in self._reached, timeout=timeout):
                raise TimeoutError(f"{barrier.value} was not reached")
            return self._reached[barrier]

    def release(self, barrier: Barrier) -> None:
        with self._condition:
            event_id = self._reached.get(barrier)
            if event_id is None:
                raise ValueError(f"{barrier.value} has not been reached")
            if barrier not in self.held or barrier in self._released:
                raise ValueError(f"{barrier.value} is not held")
            self._persist_release(event_id)
            self._released.add(barrier)
            self._condition.notify_all()

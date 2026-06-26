from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.models.event import Event


class FakeEventSession:
    def __init__(self) -> None:
        self.events: dict[object, Event] = {}

    def add(self, event: Event) -> None:
        if event.id is None:
            event.id = uuid4()
        self._stamp(event)
        self.events[event.id] = event

    async def commit(self) -> None:
        for event in self.events.values():
            self._stamp(event)

    async def refresh(self, event: Event) -> None:
        self._stamp(event)

    async def get(self, model, event_id):
        if model is Event:
            return self.events.get(event_id)
        return None

    async def delete(self, event: Event) -> None:
        self.events.pop(event.id, None)

    def _stamp(self, event: Event) -> None:
        now = datetime.now(timezone.utc)
        if getattr(event, "created_at", None) is None:
            event.created_at = now
        event.updated_at = now


@pytest.fixture
def session() -> FakeEventSession:
    return FakeEventSession()

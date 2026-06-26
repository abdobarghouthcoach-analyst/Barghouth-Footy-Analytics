from typing import Any


class Service:
    """Base service class for application business logic."""

    def __init__(self, repository: Any) -> None:
        self.repository = repository


__all__ = ["Service"]

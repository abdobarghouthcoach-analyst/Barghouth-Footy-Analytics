from typing import Generic, TypeVar

T = TypeVar("T")


class Repository(Generic[T]):
    """Base repository type for database access."""

    def __init__(self, model: type[T]) -> None:
        self.model = model


__all__ = ["Repository"]

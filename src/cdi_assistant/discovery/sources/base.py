from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from ..models import JobDiscovery
from ..query_generator import SearchQuery


class JobSource(ABC):
    """Interface implemented by every job-discovery provider."""

    name: str

    @abstractmethod
    def search(self, query: SearchQuery) -> Sequence[JobDiscovery]:
        """Return normalized jobs for one generated search query."""
        raise NotImplementedError

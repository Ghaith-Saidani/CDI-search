from __future__ import annotations

from dataclasses import dataclass

from .config import DiscoveryConfig
from .models import JobDiscovery
from .query_generator import SearchQuery, generate_queries
from .sources.base import JobSource
from .storage import JobDiscoveryStore


@dataclass(slots=True)
class DiscoveryRun:
    """Result of one discovery run."""

    queries: list[SearchQuery]
    jobs: list[JobDiscovery]
    persisted: int


class DiscoveryEngine:
    """Generate the search portfolio, query providers, deduplicate and persist."""

    def __init__(
        self,
        sources: list[JobSource],
        store: JobDiscoveryStore | None = None,
        config: DiscoveryConfig | None = None,
    ) -> None:
        self.sources = sources
        self.store = store
        self.config = config or DiscoveryConfig()

    def run(self) -> DiscoveryRun:
        queries = generate_queries(self.config)
        unique: dict[str, JobDiscovery] = {}

        for query in queries:
            for source in self.sources:
                for job in source.search(query):
                    unique.setdefault(job.deduplication_key, job)

        jobs = list(unique.values())
        persisted = self.store.upsert_many(jobs) if self.store else 0
        return DiscoveryRun(queries=queries, jobs=jobs, persisted=persisted)

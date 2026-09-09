from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from cdi_assistant.discovery.config import DiscoveryConfig
from cdi_assistant.discovery.engine import DiscoveryEngine
from cdi_assistant.discovery.models import JobDiscovery
from cdi_assistant.discovery.query_generator import SearchQuery
from cdi_assistant.discovery.sources.base import JobSource
from cdi_assistant.discovery.storage import JobDiscoveryStore


class FakeSource(JobSource):
    name = "fake"

    def search(self, query: SearchQuery) -> list[JobDiscovery]:
        return [
            JobDiscovery(
                source=self.name,
                source_id="job-1",
                url="https://example.test/jobs/1",
                title="Junior Data Engineer",
                company="Example",
                location="France",
                contract="CDI",
                search_query=query.text,
            ),
            JobDiscovery(
                source=self.name,
                source_id="job-1",
                url="https://example.test/jobs/1?tracking=duplicate",
                title="Junior Data Engineer",
                company="Example",
                location="France",
                contract="CDI",
                search_query=query.text,
            ),
        ]


class DiscoveryEngineTests(unittest.TestCase):
    def test_engine_deduplicates_and_persists(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = JobDiscoveryStore(Path(directory) / "jobs.db")
            config = DiscoveryConfig(max_queries=2)
            run = DiscoveryEngine([FakeSource()], store=store, config=config).run()

            self.assertEqual(len(run.queries), 2)
            self.assertEqual(len(run.jobs), 1)
            self.assertEqual(run.persisted, 1)
            self.assertEqual(store.count(), 1)

    def test_job_uses_canonical_url_for_fallback_deduplication(self) -> None:
        job = JobDiscovery(
            source="fake",
            url="https://example.test/jobs/1?utm_source=test",
            canonical_url="https://example.test/jobs/1",
            title="Data Engineer",
        )
        self.assertEqual(job.deduplication_key, "https://example.test/jobs/1")


if __name__ == "__main__":
    unittest.main()

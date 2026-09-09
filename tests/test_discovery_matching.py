from __future__ import annotations

import unittest

from cdi_assistant.discovery.models import JobDiscovery
from cdi_assistant.discovery_cli import _rank_jobs, _to_job_offer
from cdi_assistant.models import CandidateProfile


class DiscoveryMatchingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.candidate = CandidateProfile(
            confirmed_skills=["Python", "SQL", "PostgreSQL", "Docker"],
            years_experience=0.9,
            degree_level="Diplôme d’Ingénieur / Master-equivalent",
            degree_fields=["Data Science", "Computer Science"],
            languages={"French": "C1", "English": "C1"},
        )

    def test_discovery_is_converted_to_job_offer(self) -> None:
        job = JobDiscovery(
            source="fake",
            source_id="1",
            url="https://example.test/1",
            title="Junior Data Engineer",
            company="Example",
            location="Paris, France",
            contract="CDI",
            description="Junior role requiring Python and SQL, Bac+5 in data science.",
            skills=("Python", "SQL"),
        )
        offer = _to_job_offer(job)
        self.assertEqual(offer.position, "Junior Data Engineer")
        self.assertEqual(offer.contract, "CDI")
        self.assertEqual([item.name for item in offer.technical_requirements], ["Python", "SQL"])
        self.assertEqual(offer.education_required, "Master")
        self.assertIn("Data Science", offer.education_fields)

    def test_ranked_results_are_sorted_by_score(self) -> None:
        strong = JobDiscovery(
            source="fake", source_id="1", url="https://example.test/1",
            title="Junior Data Engineer", company="StrongCo", location="Paris, France",
            contract="CDI", description="Junior Data Engineer role.",
            skills=("Python", "SQL", "PostgreSQL", "Docker"),
        )
        weak = JobDiscovery(
            source="fake", source_id="2", url="https://example.test/2",
            title="Junior AI Engineer", company="WeakCo", location="Paris, France",
            contract="CDI", description="Junior AI Engineer role.",
            skills=("Kubernetes",),
        )
        ranked = _rank_jobs(self.candidate, [weak, strong])
        self.assertEqual(ranked[0]["company"], "StrongCo")
        self.assertGreaterEqual(int(ranked[0]["score"]), int(ranked[1]["score"]))


if __name__ == "__main__":
    unittest.main()

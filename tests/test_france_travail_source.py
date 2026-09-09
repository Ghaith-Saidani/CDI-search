from __future__ import annotations

import unittest

from cdi_assistant.discovery.models import JobDiscovery
from cdi_assistant.discovery.query_generator import SearchQuery
from cdi_assistant.discovery.sources.france_travail import (
    FranceTravailConfig,
    FranceTravailSource,
)


class FranceTravailSourceTests(unittest.TestCase):
    def test_normalize_maps_api_fields(self) -> None:
        source = FranceTravailSource(
            FranceTravailConfig(client_id="id", client_secret="secret")
        )
        query = SearchQuery(text="Data Engineer CDI France", role_family="Data Engineer")
        job = source._normalize(
            {
                "id": "123ABC",
                "intitule": "Ingénieur Data Junior",
                "description": "Construire des pipelines data.",
                "dateCreation": "2026-09-01T10:00:00Z",
                "dateActualisation": "2026-09-02T10:00:00Z",
                "typeContratLibelle": "CDI",
                "experienceLibelle": "Débutant accepté",
                "lieuTravail": {"libelle": "Limoges (87)"},
                "entreprise": {"nom": "Example Data"},
                "competences": [
                    {"libelle": "Python"},
                    {"libelle": "SQL"},
                    {},
                ],
            },
            query,
        )

        self.assertIsInstance(job, JobDiscovery)
        self.assertEqual(job.source, "france_travail")
        self.assertEqual(job.source_id, "123ABC")
        self.assertEqual(job.title, "Ingénieur Data Junior")
        self.assertEqual(job.company, "Example Data")
        self.assertEqual(job.location, "Limoges (87)")
        self.assertEqual(job.contract, "CDI")
        self.assertEqual(job.experience, "Débutant accepté")
        self.assertEqual(job.skills, ("Python", "SQL"))
        self.assertEqual(job.search_query, query.text)

    def test_credentials_are_required_from_environment(self) -> None:
        import os

        old_id = os.environ.pop("FRANCE_TRAVAIL_CLIENT_ID", None)
        old_secret = os.environ.pop("FRANCE_TRAVAIL_CLIENT_SECRET", None)
        try:
            with self.assertRaises(RuntimeError):
                FranceTravailConfig.from_environment()
        finally:
            if old_id is not None:
                os.environ["FRANCE_TRAVAIL_CLIENT_ID"] = old_id
            if old_secret is not None:
                os.environ["FRANCE_TRAVAIL_CLIENT_SECRET"] = old_secret


if __name__ == "__main__":
    unittest.main()

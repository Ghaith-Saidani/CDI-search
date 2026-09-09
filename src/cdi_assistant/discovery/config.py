from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class DiscoveryConfig:
    """Configuration for the France-wide Data/AI CDI job search."""

    country: str = "France"
    contract: str = "CDI"
    target_start: str = "2027-01"

    role_families: dict[str, tuple[str, ...]] = field(
        default_factory=lambda: {
            "Data Engineer": (
                "Data Engineer",
                "Ingénieur Data",
                "Ingénieur données",
                "Data Engineering",
            ),
            "AI Engineer": (
                "AI Engineer",
                "Artificial Intelligence Engineer",
                "Ingénieur IA",
                "Ingénieur Intelligence Artificielle",
            ),
            "ML Engineer": (
                "Machine Learning Engineer",
                "ML Engineer",
                "Ingénieur Machine Learning",
                "Ingénieur ML",
            ),
            "MLOps Engineer": (
                "MLOps Engineer",
                "ML Engineer MLOps",
                "Ingénieur MLOps",
                "Machine Learning Operations",
            ),
            "Data Scientist": (
                "Data Scientist",
                "Data Science",
                "Scientist Data",
            ),
            "Data & AI Engineer": (
                "Data & AI Engineer",
                "Data AI Engineer",
                "Ingénieur Data et IA",
                "Ingénieur Data & IA",
            ),
            "Applied AI Engineer": (
                "Applied AI Engineer",
                "Ingénieur IA appliquée",
                "Applied Machine Learning Engineer",
            ),
            "GenAI / LLM Engineer": (
                "GenAI Engineer",
                "Generative AI Engineer",
                "LLM Engineer",
                "Ingénieur IA générative",
                "Ingénieur LLM",
            ),
            "Data/AI Consultant": (
                "Data Consultant",
                "AI Consultant",
                "Data & AI Consultant",
                "Consultant Data",
                "Consultant IA",
            ),
            "Python/Data Developer": (
                "Python Data Developer",
                "Data Developer",
                "Développeur Python Data",
                "Développeur Data",
            ),
            "Data Platform Engineer": (
                "Data Platform Engineer",
                "Ingénieur Data Platform",
                "Data Platform",
            ),
        }
    )

    seniority_terms: tuple[str, ...] = (
        "junior",
        "junior(e)",
        "jeune diplômé",
        "jeune diplômée",
        "jeunes diplômés",
        "graduate",
        "entry level",
        "0-2 years",
        "0 à 2 ans",
        "débutant",
        "débutante",
    )

    positive_context_terms: tuple[str, ...] = (
        "jeune diplômé",
        "jeune diplômée",
        "graduate",
        "first job",
        "première expérience",
        "première expérience professionnelle",
        "0-2 ans",
        "0 à 2 ans",
        "moins de 2 ans",
        "moins de 3 ans",
    )

    hard_exclude_terms: tuple[str, ...] = (
        "stage",
        "internship",
        "alternance",
        "apprentissage",
    )

    seniority_exclude_terms: tuple[str, ...] = (
        "senior",
        "lead",
        "principal",
        "staff engineer",
        "head of",
        "director",
        "manager",
    )

    languages: tuple[str, ...] = (
        "French",
        "English",
    )

    mobility: str = "France entière"

    max_queries: int = 40

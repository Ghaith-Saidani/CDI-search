from __future__ import annotations

from dataclasses import dataclass

from .config import DiscoveryConfig


@dataclass(frozen=True, slots=True)
class SearchQuery:
    """A generated search query and the role family it targets."""

    text: str
    role_family: str


def generate_queries(config: DiscoveryConfig | None = None) -> list[SearchQuery]:
    """Generate a bounded and balanced portfolio of job-search queries."""

    config = config or DiscoveryConfig()

    queries: list[SearchQuery] = []
    seen: set[str] = set()

    def add(role_family: str, text: str) -> None:
        normalized = " ".join(text.split()).strip().lower()

        if not normalized or normalized in seen:
            return

        seen.add(normalized)
        queries.append(
            SearchQuery(
                text=" ".join(text.split()),
                role_family=role_family,
            )
        )

    # Give every role family three searches:
    #   1. CDI-focused
    #   2. junior-focused
    #   3. French graduate-focused
    for role_family, terms in config.role_families.items():
        if not terms:
            continue

        english_or_primary = terms[0]
        french_or_secondary = terms[1] if len(terms) > 1 else terms[0]

        add(
            role_family,
            f'"{english_or_primary}" {config.contract} {config.country}',
        )

        add(
            role_family,
            f'"{english_or_primary}" {config.country} junior',
        )

        add(
            role_family,
            f'"{french_or_secondary}" {config.country} "jeune diplômé"',
        )

    # Broader searches catch relevant jobs whose titles don't exactly
    # match one of the role-family names.
    broad_queries = (
        f'"Data" "IA" {config.contract} {config.country}',
        f'"Data Science" {config.contract} {config.country}',
        f'"Machine Learning" {config.contract} {config.country}',
        f'"Artificial Intelligence" {config.contract} {config.country}',
        f'"Data" "IA" {config.country} junior',
        f'"Machine Learning" {config.country} "jeune diplômé"',
    )

    for query in broad_queries:
        add("Broad Data/AI", query)

    return queries[: config.max_queries]


def query_texts(config: DiscoveryConfig | None = None) -> list[str]:
    """Return only the query strings, preserving generation order."""

    return [query.text for query in generate_queries(config)]
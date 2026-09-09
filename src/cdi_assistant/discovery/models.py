from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class JobDiscovery:
    """Normalized representation of a discovered job offer."""

    source: str
    url: str
    title: str

    company: str | None = None
    location: str | None = None
    canonical_url: str | None = None
    apply_url: str | None = None

    source_id: str | None = None

    published_at: str | None = None
    updated_at: str | None = None
    discovered_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    snippet: str = ""
    description: str = ""
    contract: str | None = None
    remote: str | None = None
    salary: str | None = None
    experience: str | None = None
    skills: tuple[str, ...] = ()

    search_query: str | None = None

    raw_data: dict[str, Any] = field(default_factory=dict)

    @property
    def deduplication_key(self) -> str:
        """Stable key used to detect the same offer across sources."""
        if self.source_id:
            return f"{self.source}:{self.source_id}"

        value = self.canonical_url or self.url
        return value.strip().lower()

    def to_dict(self) -> dict[str, Any]:
        """Serialize the discovery record to a JSON-compatible dictionary."""
        return {
            "source": self.source,
            "source_id": self.source_id,
            "url": self.url,
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "canonical_url": self.canonical_url,
            "apply_url": self.apply_url,
            "published_at": self.published_at,
            "updated_at": self.updated_at,
            "discovered_at": self.discovered_at,
            "snippet": self.snippet,
            "description": self.description,
            "contract": self.contract,
            "remote": self.remote,
            "salary": self.salary,
            "experience": self.experience,
            "skills": list(self.skills),
            "search_query": self.search_query,
            "raw_data": self.raw_data,
        }

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from ..query_generator import SearchQuery
from ..models import JobDiscovery
from .base import JobSource


@dataclass(frozen=True, slots=True)
class FranceTravailConfig:
    """Configuration for the France Travail Offers API."""

    client_id: str
    client_secret: str
    search_url: str = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"
    token_url: str = "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=/partenaire"
    page_size: int = 50

    @classmethod
    def from_environment(cls) -> "FranceTravailConfig":
        client_id = os.getenv("FRANCE_TRAVAIL_CLIENT_ID", "").strip()
        client_secret = os.getenv("FRANCE_TRAVAIL_CLIENT_SECRET", "").strip()
        if not client_id or not client_secret:
            raise RuntimeError(
                "France Travail API credentials are missing. Set "
                "FRANCE_TRAVAIL_CLIENT_ID and FRANCE_TRAVAIL_CLIENT_SECRET."
            )
        return cls(client_id=client_id, client_secret=client_secret)


class FranceTravailSource(JobSource):
    """France Travail Offers API adapter using the OAuth2 client-credentials flow."""

    name = "france_travail"

    def __init__(self, config: FranceTravailConfig) -> None:
        self.config = config
        self._access_token: str | None = None

    def _get_access_token(self) -> str:
        if self._access_token:
            return self._access_token

        body = urlencode(
            {
                "grant_type": "client_credentials",
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
                "scope": "api_offresdemploiv2 o2dsoffre",
            }
        ).encode("utf-8")
        request = Request(
            self.config.token_url,
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        with urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))

        token = str(payload.get("access_token", "")).strip()
        if not token:
            raise RuntimeError("France Travail token response did not contain access_token.")
        self._access_token = token
        return token

    def search(self, query: SearchQuery) -> list[JobDiscovery]:
        """Search active France Travail offers for one generated query."""
        params = {
            "motsCles": query.text,
            "typeContrat": "CDI",
            "range": f"0-{max(1, self.config.page_size) - 1}",
        }
        request = Request(
            f"{self.config.search_url}?{urlencode(params)}",
            headers={
                "Authorization": f"Bearer {self._get_access_token()}",
                "Accept": "application/json",
            },
            method="GET",
        )
        with urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))

        return [self._normalize(item, query) for item in payload.get("resultats", [])]

    def _normalize(self, item: dict, query: SearchQuery) -> JobDiscovery:
        lieu = item.get("lieuTravail") or {}
        entreprise = item.get("entreprise") or {}
        experience = item.get("experienceLibelle") or item.get("experienceExige")
        competences = item.get("competences") or []
        skills = tuple(
            str(skill.get("libelle", "")).strip()
            for skill in competences
            if isinstance(skill, dict) and str(skill.get("libelle", "")).strip()
        )
        description = str(item.get("description", "")).strip()
        url = str(item.get("origineOffre", {}).get("urlOrigine", "")).strip()
        if not url:
            url = f"https://candidat.francetravail.fr/offres/recherche/detail/{item.get('id', '')}"

        return JobDiscovery(
            source=self.name,
            source_id=str(item.get("id", "")).strip() or None,
            url=url,
            canonical_url=url,
            apply_url=url,
            title=str(item.get("intitule", "")).strip(),
            company=str(entreprise.get("nom", "")).strip() or None,
            location=str(lieu.get("libelle", "")).strip() or None,
            published_at=item.get("dateCreation"),
            updated_at=item.get("dateActualisation"),
            description=description,
            snippet=description[:500],
            contract=str(item.get("typeContratLibelle", "")).strip() or None,
            experience=str(experience).strip() if experience else None,
            skills=skills,
            search_query=query.text,
            raw_data=item,
        )

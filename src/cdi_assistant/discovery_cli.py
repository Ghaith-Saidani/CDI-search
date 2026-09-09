from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from .discovery.engine import DiscoveryEngine
from .discovery.models import JobDiscovery
from .discovery.sources.france_travail import FranceTravailConfig, FranceTravailSource
from .discovery.storage import JobDiscoveryStore
from .models import CandidateProfile, JobOffer, TechnicalRequirement
from .service import evaluate

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = PROJECT_ROOT / "data" / "jobs.db"
DEFAULT_PROFILE = PROJECT_ROOT / "data" / "candidate_profile.json"


def _load_candidate(path: Path) -> CandidateProfile:
    return CandidateProfile(**json.loads(path.read_text(encoding="utf-8")))


def _infer_seniority(job: JobDiscovery) -> str | None:
    text = f"{job.title} {job.description} {job.experience}".lower()
    if any(term in text for term in ("senior", "lead", "principal", "staff", "head of", "director")):
        return "senior"
    if any(term in text for term in ("junior", "graduate", "jeune diplôm", "entry level", "0-2", "0 à 2", "débutant")):
        return "junior"
    return None


def _infer_min_years(job: JobDiscovery) -> float | None:
    text = f"{job.experience} {job.description}".lower()
    patterns = (
        r"(?:minimum|au moins|min(?:imum)?|at least)\s+(\d+(?:[.,]\d+)?)\s*(?:ans?|years?)",
        r"(\d+(?:[.,]\d+)?)\s*\+\s*(?:ans?|years?)",
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return float(match.group(1).replace(",", "."))
    return None


def _infer_education(job: JobDiscovery) -> tuple[str | None, list[str]]:
    text = f"{job.title} {job.description}".lower()
    required = None
    if any(term in text for term in ("bac+5", "bac + 5", "master", "diplôme d'ingénieur", "diplôme d’ingénieur")):
        required = "Master"
    fields: list[str] = []
    for label, terms in (
        ("Data Science", ("data science", "data scientist")),
        ("Computer Science", ("computer science", "informatique")),
        ("Artificial Intelligence", ("artificial intelligence", "intelligence artificielle", "machine learning")),
    ):
        if any(term in text for term in terms):
            fields.append(label)
    return required, fields


def _to_job_offer(job: JobDiscovery) -> JobOffer:
    education_required, education_fields = _infer_education(job)
    requirements = [
        TechnicalRequirement(name=skill, importance="preferred")
        for skill in job.skills
        if skill.strip()
    ]
    return JobOffer(
        company=job.company or "Unknown company",
        position=job.title,
        location=job.location or "France",
        contract=job.contract,
        description=job.description,
        seniority=_infer_seniority(job),
        min_years_experience=_infer_min_years(job),
        education_required=education_required,
        education_fields=education_fields,
        technical_requirements=requirements,
    )


def _score_number(evaluation: object) -> int:
    match = re.search(r"(\d+)\s*/\s*100", str(evaluation))
    return int(match.group(1)) if match else 0


def _rank_jobs(candidate: CandidateProfile, jobs: list[JobDiscovery]) -> list[dict[str, object]]:
    ranked: list[dict[str, object]] = []
    for job in jobs:
        evaluation = evaluate(candidate, _to_job_offer(job))
        ranked.append(
            {
                "source": job.source,
                "source_id": job.source_id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "contract": job.contract,
                "url": job.apply_url or job.url,
                "published_at": job.published_at,
                "updated_at": job.updated_at,
                "score": _score_number(evaluation.match_score["total"]),
                "priority": evaluation.match_score["priority"],
                "decision": evaluation.final_decision["decision"],
                "role_family": evaluation.job_information["role_family"],
                "strong_matches": evaluation.strong_matches,
                "gaps": evaluation.gaps,
                "red_flags": evaluation.red_flags,
                "recommended_cv": evaluation.recommended_cv,
            }
        )
    return sorted(ranked, key=lambda item: (-int(item["score"]), item["company"] or "", item["title"]))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Discover France Data/AI CDI offers and optionally rank them against the canonical candidate profile."
    )
    parser.add_argument("--source", choices=["france-travail"], default="france-travail")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--max-queries", type=int, default=None)
    parser.add_argument("--match", action="store_true", help="Evaluate and rank discovered offers against the candidate profile.")
    parser.add_argument("--top", type=int, default=20, help="Maximum ranked offers to print when --match is used.")
    args = parser.parse_args()

    config = None
    if args.max_queries is not None:
        from dataclasses import replace
        from .discovery.config import DiscoveryConfig

        config = replace(DiscoveryConfig(), max_queries=max(1, args.max_queries))

    if args.source == "france-travail":
        source = FranceTravailSource(FranceTravailConfig.from_environment())
    else:  # pragma: no cover
        raise RuntimeError(f"Unsupported source: {args.source}")

    store = JobDiscoveryStore(args.db)
    run = DiscoveryEngine([source], store=store, config=config).run()

    payload: dict[str, object] = {
        "queries": len(run.queries),
        "newly_discovered_in_run": len(run.jobs),
        "persisted": run.persisted,
        "database": str(args.db),
    }

    if args.match:
        candidate = _load_candidate(args.profile)
        ranked = _rank_jobs(candidate, run.jobs)
        payload["ranked_offers"] = ranked[: max(1, args.top)]
        payload["matched_offers"] = len(ranked)

    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

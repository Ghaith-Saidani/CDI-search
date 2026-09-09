from __future__ import annotations

import re
from .models import CandidateProfile, JobOffer, RequirementAssessment
from .technical_matching import match_technical_requirement

ROLE_KEYWORDS = {
    "Data Engineer": ("data engineer", "data engineering", "ingénieur data", "etl", "elt", "data pipeline", "pipeline de données", "warehouse"),
    "AI Engineer": ("ai engineer", "artificial intelligence", "ingénieur ia", "generative ai", "genai", "intelligence artificielle"),
    "ML/MLOps": ("machine learning", "ml engineer", "ingénieur machine learning", "mlops", "model deployment", "model serving"),
    "Data Scientist": ("data scientist", "data science", "statistical model"),
    "Data/AI Consultant": ("data consultant", "ai consultant", "consultant data", "consultant ia"),
    "Python/Data Developer": ("python", "data developer", "développeur data", "python developer"),
    "Data Platform Engineer": ("data platform engineer", "ingénieur plateforme data", "data platform"),
    "Data & AI Engineer": ("data & ai engineer", "data and ai engineer", "ingénieur data ia", "ingénieur data & ia"),
    "Applied AI / GenAI / LLM Engineer": ("applied ai", "genai engineer", "llm engineer", "generative ai engineer", "ingénieur ia générative"),
}
DATA_AI_TERMS = tuple({term for terms in ROLE_KEYWORDS.values() for term in terms} | {"llm", "deep learning", "analytics", "big data", "data"})
GENERIC_SOFTWARE_TERMS = ("frontend", "front-end", "full stack", "fullstack", "mobile developer", "java developer", ".net developer")


def _normalise(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def _contains(haystack: str, needle: str) -> bool:
    return _normalise(needle) in _normalise(haystack)


def classify_role_family(job: JobOffer) -> str:
    text = f"{job.position} {job.description}".lower()
    scores = {family: sum(term in text for term in terms) for family, terms in ROLE_KEYWORDS.items()}
    best, score = max(scores.items(), key=lambda item: item[1])
    return best if score else "Other / unclear"


def data_ai_relevance(job: JobOffer) -> int:
    text = _normalise(f"{job.position} {job.description}")
    hits = sum(term in text for term in DATA_AI_TERMS)
    # An explicit target role in the title is already strong relevance evidence;
    # descriptions with only a few generic keywords are not treated the same way.
    title = _normalise(job.position)
    explicit_family = any(term in title for terms in ROLE_KEYWORDS.values() for term in terms)
    score = min(25, (16 if explicit_family else 0) + hits * 3)
    if any(term in text for term in GENERIC_SOFTWARE_TERMS) and hits <= 1:
        score = min(score, 10)
    return score


def assess_technical(candidate: CandidateProfile, job: JobOffer) -> tuple[int, list[RequirementAssessment]]:
    if not job.technical_requirements:
        return 0, [RequirementAssessment("Technical requirements", "unknown", evidence="No technical requirements supplied in the offer.")]
    weights = {"mandatory": 3, "preferred": 2, "nice_to_have": 1}
    total_weight = sum(weights[r.importance] for r in job.technical_requirements)
    earned = 0.0
    assessments = []
    for requirement in job.technical_requirements:
        weight = weights[requirement.importance]
        match = match_technical_requirement(candidate, requirement.name)
        earned += weight * match.factor
        assessments.append(RequirementAssessment(
            requirement.name,
            match.status,
            requirement.importance,
            match_strength=match.classification,
            evidence=match.explanation,
        ))
    return round(25 * earned / total_weight), assessments


def _level_value(level: str) -> int:
    normalized = _normalise(level)
    values = {"a1": 1, "a2": 2, "b1": 3, "b2": 4, "c1": 5, "c2": 6, "native": 7, "fluent": 6, "professional": 5}
    return values.get(normalized, 0)


def score_experience(candidate: CandidateProfile, job: JobOffer) -> tuple[int, RequirementAssessment]:
    if job.min_years_experience is None:
        return 8, RequirementAssessment("Experience", "unknown", evidence="Offer does not state a minimum number of years.")
    if candidate.years_experience is None:
        return 0, RequirementAssessment(f"{job.min_years_experience:g}+ years experience", "unknown", evidence="Candidate years_experience is not supplied.")
    ratio = candidate.years_experience / max(job.min_years_experience, .5)
    status = "clearly_satisfy" if ratio >= 1 else "partially_satisfy" if ratio >= .5 else "not_satisfy"
    return min(15, round(15 * ratio)), RequirementAssessment(f"{job.min_years_experience:g}+ years experience", status, evidence=f"Candidate profile states {candidate.years_experience:g} year(s).")


def score_seniority(job: JobOffer) -> tuple[int, RequirementAssessment]:
    seniority = _normalise(job.seniority or "")
    if not seniority:
        return 5, RequirementAssessment("Junior / 0–2 years seniority", "unknown", evidence="Offer seniority is not supplied.")
    if any(word in seniority for word in ("junior", "graduate", "jeune diplômé", "entry", "0-2")):
        return 10, RequirementAssessment("Junior / 0–2 years seniority", "clearly_satisfy", evidence="Offer targets junior level.")
    if any(word in seniority for word in ("senior", "lead", "principal", "expert", "5+")):
        return 0, RequirementAssessment("Junior / 0–2 years seniority", "not_satisfy", evidence=f"Offer states {job.seniority!r}.")
    return 4, RequirementAssessment("Junior / 0–2 years seniority", "partially_satisfy", evidence=f"Offer states {job.seniority!r}.")


def score_education(candidate: CandidateProfile, job: JobOffer) -> tuple[int, RequirementAssessment]:
    if not job.education_required and not job.education_fields:
        return 7, RequirementAssessment("Education", "unknown", evidence="Offer has no stated education requirement.")
    if candidate.degree_level is None:
        return 0, RequirementAssessment("Education", "unknown", evidence="Candidate degree evidence is not supplied.")
    fields_match = not job.education_fields or any(_contains(field, candidate_field) or _contains(candidate_field, field) for field in job.education_fields for candidate_field in candidate.degree_fields)
    level_match = not job.education_required or _normalise(job.education_required) in _normalise(candidate.degree_level)
    score = 10 if fields_match and level_match else 5 if fields_match or level_match else 0
    status = "clearly_satisfy" if score == 10 else "partially_satisfy" if score else "not_satisfy"
    return score, RequirementAssessment("Education", status, evidence=f"Candidate: {candidate.degree_level}; fields: {', '.join(candidate.degree_fields) or 'not supplied'}.")


def score_languages(candidate: CandidateProfile, job: JobOffer) -> tuple[int, list[RequirementAssessment]]:
    if not job.languages:
        return 7, [RequirementAssessment("Languages / other requirements", "unknown", evidence="Offer has no stated language requirements.")]
    results = []
    earned = 0.0
    for language, required in job.languages.items():
        actual = next((level for name, level in candidate.languages.items() if _normalise(name) == _normalise(language)), None)
        if actual is None:
            status, factor, evidence = "unknown", 0, "Candidate language level is not supplied."
        elif _level_value(actual) >= _level_value(required):
            status, factor, evidence = "clearly_satisfy", 1, f"Candidate states {actual}."
        else:
            status, factor, evidence = "partially_satisfy", .4, f"Candidate states {actual}; offer requests {required}."
        earned += factor
        results.append(RequirementAssessment(f"{language}: {required}", status, evidence=evidence))
    return round(10 * earned / len(job.languages)), results

from __future__ import annotations

from .models import CandidateProfile, Evaluation, JobOffer, RequirementAssessment
from .scoring import (assess_technical, classify_role_family, data_ai_relevance, score_education,
                      score_experience, score_languages, score_seniority)

EXPLICIT_NON_CDI_TERMS = ("cdd", "internship", "stage", "freelance", "temporary", "temp", "intérim", "interim", "contractor", "apprenticeship", "alternance")


def _contract_status(contract: str | None) -> str:
    """Return cdi, non_cdi, or unknown without treating working hours as contract type."""
    if not contract:
        return "unknown"
    normalized = contract.lower()
    if "cdi" in normalized:
        return "cdi"
    if any(term in normalized for term in EXPLICIT_NON_CDI_TERMS):
        return "non_cdi"
    return "unknown"


def evaluate(candidate: CandidateProfile, job: JobOffer) -> Evaluation:
    relevance = data_ai_relevance(job)
    technical, technical_assessments = assess_technical(candidate, job)
    experience, experience_assessment = score_experience(candidate, job)
    seniority, seniority_assessment = score_seniority(job)
    education, education_assessment = score_education(candidate, job)
    languages, language_assessments = score_languages(candidate, job)
    location = 5 if "france" in job.location.lower() or job.location.strip() else 0
    contract_status = _contract_status(job.contract)
    explicit_non_cdi = contract_status == "non_cdi"
    other = languages if not explicit_non_cdi else max(0, languages - 5)
    assessments = technical_assessments + [experience_assessment, seniority_assessment, education_assessment] + language_assessments
    if contract_status == "cdi":
        assessments.append(RequirementAssessment("CDI contract", "clearly_satisfy", evidence=f"Offer contract: {job.contract}."))
    elif contract_status == "non_cdi":
        assessments.append(RequirementAssessment("CDI contract", "not_satisfy", evidence=f"Offer contract: {job.contract}."))
    else:
        assessments.append(RequirementAssessment("CDI contract (UNKNOWN / VERIFY)", "unknown", evidence=f"Offer contract information: {job.contract or 'not stated'}. This does not explicitly confirm CDI or a non-CDI contract."))
    total = relevance + technical + experience + seniority + education + location + other
    priority = "A" if total >= 80 else "B" if total >= 65 else "C" if total >= 50 else "SKIP"
    hard_gate = relevance < 15
    if hard_gate or explicit_non_cdi:
        decision = "DO NOT APPLY"
    elif priority == "A":
        decision = "APPLY — HIGH PRIORITY"
    elif priority == "B":
        decision = "APPLY"
    else:
        decision = "APPLY — SELECTIVE" if priority == "C" else "DO NOT APPLY"
    strong = [a.requirement for a in assessments if a.status == "clearly_satisfy"]
    gaps = [a.requirement for a in assessments if a.status in ("partially_satisfy", "not_satisfy")]
    red_flags = []
    if hard_gate: red_flags.append("Data/AI relevance is below the 15/25 hard gate.")
    if explicit_non_cdi: red_flags.append(f"Offer is {job.contract}, not CDI.")
    if seniority == 0: red_flags.append("Seniority is materially above the junior / 0–2-year target.")
    if experience == 0 and job.min_years_experience is not None: red_flags.append("Mandatory experience cannot be evidenced from the candidate profile.")
    for a in technical_assessments:
        if a.importance == "mandatory" and a.status == "not_satisfy": red_flags.append(f"Mandatory technology not evidenced: {a.requirement}.")
    family = classify_role_family(job)
    cv = "Data Engineer" if family == "Data Engineer" else "ML/MLOps" if family == "ML/MLOps" else "AI Engineer"
    angle = (f"Position as {candidate.positioning}, focusing only on confirmed evidence relevant to this {family} role. "
             f"Lead with the strongest demonstrated technical matches and explicitly frame partial matches as learning trajectory, not completed experience. "
             f"The role is {'a credible' if not hard_gate else 'not a sufficiently Data/AI-focused'} target for the January 2027 CDI search.")
    reason = "Rejected by the Data/AI relevance hard gate." if hard_gate else "Contract is not CDI." if explicit_non_cdi else f"Score {total}/100 ({priority}); apply only where the listed evidence is accurate."
    return Evaluation(
        job_information={"company": job.company, "position": job.position, "location": job.location, "contract": job.contract, "role_family": family},
        match_score={"data_ai_relevance": f"{relevance}/25", "technical_match": f"{technical}/25", "experience_match": f"{experience}/15", "seniority": f"{seniority}/10", "education": f"{education}/10", "location_mobility": f"{location}/5", "languages_other": f"{other}/10", "total": f"{total}/100", "priority": priority},
        strong_matches=strong, gaps=gaps, red_flags=red_flags,
        recommended_cv={"choice": cv, "reason": f"Role family classified as {family}."},
        application_angle=angle, final_decision={"decision": decision, "reason": reason}, requirement_assessments=assessments)

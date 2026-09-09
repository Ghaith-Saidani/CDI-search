from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

Importance = Literal["mandatory", "preferred", "nice_to_have"]


@dataclass
class TechnicalRequirement:
    name: str
    importance: Importance = "mandatory"


@dataclass
class CandidateProfile:
    positioning: str = "Ingénieur Data & IA — Data Engineering, Machine Learning & MLOps"
    target_contract: str = "CDI"
    target_country: str = "France"
    target_start: str = "2027-01"
    target_seniority: str = "junior"
    mobility: str = "France entière"
    confirmed_skills: list[str] = field(default_factory=list)
    partial_skills: list[str] = field(default_factory=list)
    years_experience: float | None = None
    degree_level: str | None = None
    degree_fields: list[str] = field(default_factory=list)
    languages: dict[str, str] = field(default_factory=dict)
    other_evidence: list[str] = field(default_factory=list)


@dataclass
class JobOffer:
    company: str
    position: str
    location: str
    contract: str | None = None
    description: str = ""
    seniority: str | None = None
    min_years_experience: float | None = None
    education_required: str | None = None
    education_fields: list[str] = field(default_factory=list)
    technical_requirements: list[TechnicalRequirement] = field(default_factory=list)
    languages: dict[str, str] = field(default_factory=dict)
    other_requirements: list[str] = field(default_factory=list)


@dataclass
class RequirementAssessment:
    requirement: str
    status: Literal["clearly_satisfy", "partially_satisfy", "not_satisfy", "unknown"]
    importance: str = ""
    match_strength: str = ""
    evidence: str = ""


@dataclass
class Evaluation:
    job_information: dict[str, Any]
    match_score: dict[str, Any]
    strong_matches: list[str]
    gaps: list[str]
    red_flags: list[str]
    recommended_cv: dict[str, str]
    application_angle: str
    final_decision: dict[str, str]
    requirement_assessments: list[RequirementAssessment]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

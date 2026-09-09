"""Controlled, auditable technical matching for the canonical candidate profile.

Requirement labels match exactly after normalization. Candidate assertions use only
listed skills and explicitly named records in ``other_evidence``; this is neither
fuzzy matching nor unrestricted prose search.
"""
from __future__ import annotations

from dataclasses import dataclass

from .models import CandidateProfile

DIRECT = "DIRECT MATCH"
STRONG = "STRONG RELATED EVIDENCE"
WEAK = "WEAK / INDIRECT EVIDENCE"
GAP = "GENUINE GAP"
UNKNOWN = "UNKNOWN"

FACTORS = {DIRECT: 1.0, STRONG: 0.65, WEAK: 0.25, GAP: 0.0, UNKNOWN: 0.0}
STATUSES = {DIRECT: "clearly_satisfy", STRONG: "partially_satisfy", WEAK: "partially_satisfy", GAP: "not_satisfy", UNKNOWN: "unknown"}


@dataclass(frozen=True)
class CapabilityEvidence:
    capability: str
    classification: str
    confirmed_skills: tuple[str, ...] = ()
    partial_skills: tuple[str, ...] = ()
    evidence_record: str | None = None
    evidence_anchors: tuple[str, ...] = ()
    require_all_evidence_anchors: bool = False
    rationale: str = ""
    boundary: str = ""


@dataclass(frozen=True)
class RequirementDefinition:
    label: str
    kind: str  # capability, technology_specific, compound
    capability: str | None = None
    components: tuple[tuple[str, str], ...] = ()
    boundary: str = ""


@dataclass(frozen=True)
class MatchResult:
    classification: str
    factor: float
    status: str
    explanation: str


# Bounded candidate assertions. A named other_evidence record must be found
# before its anchor phrases are considered.
CAPABILITY_EVIDENCE = (
    CapabilityEvidence("machine_learning", DIRECT, ("Scikit-learn", "Random Forest", "SMOTEENN", "MLflow"), evidence_record="Projet MLOps churn (2026)", evidence_anchors=("ROC-AUC 0.89", "F1 0.84"), require_all_evidence_anchors=True, rationale="Applied ML tooling and documented churn-model evaluation metrics evidence broad machine-learning practice."),
    CapabilityEvidence("machine_learning_foundations", STRONG, ("Scikit-learn", "Random Forest", "SMOTEENN", "PyTorch"), evidence_record="Projet MLOps churn (2026)", evidence_anchors=("ROC-AUC 0.89", "F1 0.84"), require_all_evidence_anchors=True, rationale="Applied ML stack and evaluation metrics strongly support fundamentals, without a separately documented foundations curriculum."),
    CapabilityEvidence("deep_learning", DIRECT, ("PyTorch", "DDPM", "VAE", "ResNet-50"), evidence_record="Projet de génération audio / reconnaissance d’émotions vocales", evidence_anchors=("PyTorch", "DDPM", "VAE", "ResNet-50"), rationale="Confirmed deep-learning frameworks and the documented audio-generation/speech-emotion project evidence deep-learning practice."),
    CapabilityEvidence("computer_vision", DIRECT, ("OpenCV", "Tesseract OCR", "LayoutLM", "MTCNN"), evidence_record="Capgemini Engineering, stage Data Scientist & Computer Vision", evidence_anchors=("OpenCV", "Tesseract OCR", "LayoutLM"), rationale="Confirmed computer-vision tooling and the named Computer Vision internship directly support this broad capability."),
    CapabilityEvidence("databases", DIRECT, ("PostgreSQL", "Neo4j", "Elasticsearch"), ("MongoDB",), rationale="Confirmed relational, graph, and search datastore experience supports broad database technologies; MongoDB remains partial evidence."),
    CapabilityEvidence("nlp", DIRECT, evidence_record="Projet crypto due diligence/scoring (2025)", evidence_anchors=("NLP/RAG",), rationale="The named crypto due-diligence project explicitly documents NLP/RAG work."),
    CapabilityEvidence("llm_systems", DIRECT, ("Qwen LLM", "RAG", "LangChain"), evidence_record="KBR PFE, Data Engineer / Fullstack Data", evidence_anchors=("recherche sémantique RAG/LLM",), rationale="Confirmed Qwen LLM/RAG/LangChain work and documented semantic RAG/LLM search support the LLM component."),
    CapabilityEvidence("semantic_search", DIRECT, evidence_record="KBR PFE, Data Engineer / Fullstack Data", evidence_anchors=("recherche sémantique RAG/LLM",), rationale="KBR PFE evidence explicitly documents semantic RAG/LLM search."),
    CapabilityEvidence("visualization", DIRECT, ("Power BI", "Streamlit"), rationale="Confirmed Power BI and Streamlit experience supports visualization."),
    CapabilityEvidence("web_application_delivery", DIRECT, ("FastAPI", "Streamlit"), rationale="Confirmed FastAPI and Streamlit experience supports web application delivery."),
    CapabilityEvidence("model_delivery", DIRECT, ("FastAPI", "Docker", "MLflow", "CI/CD"), evidence_record="Projet MLOps churn (2026)", evidence_anchors=("API FastAPI", "déploiement Docker Compose", "MLflow model registry"), require_all_evidence_anchors=True, rationale="Confirmed delivery tooling and the documented deployed churn project support general model production and maintenance."),
    CapabilityEvidence("model_evaluation", DIRECT, evidence_record="Projet MLOps churn (2026)", evidence_anchors=("ROC-AUC 0.89", "F1 0.84", "MLflow model registry"), require_all_evidence_anchors=True, rationale="Documented ROC-AUC/F1 metrics and MLflow model registry directly evidence general ML model evaluation, not LLM-specific evaluation."),
    CapabilityEvidence("vector_databases", WEAK, ("Neo4j", "Elasticsearch", "RAG"), rationale="Graph/search and RAG experience is adjacent.", boundary="No vector database or vector-index implementation is claimed."),
    CapabilityEvidence("agentic_systems", WEAK, ("LangChain", "Qwen LLM", "RAG"), rationale="LLM application tooling is adjacent.", boundary="No agent workflow or tool-use implementation is documented."),
    CapabilityEvidence("llm_observability", WEAK, ("MLflow",), evidence_record="Projet MLOps churn (2026)", evidence_anchors=("monitoring/dashboard",), rationale="General ML monitoring is documented.", boundary="No LLM tracing or LLM-specific observability is claimed."),
    CapabilityEvidence("production_cloud", WEAK, evidence_record="Formations/certifications citées", evidence_anchors=("AWS Academy",), rationale="AWS Academy is documented training evidence.", boundary="No production AWS, Azure, or GCP experience is claimed."),
)

REQUIREMENT_DEFINITIONS = (
    RequirementDefinition("machine learning", "capability", "machine_learning"),
    RequirementDefinition("machine learning fundamentals", "capability", "machine_learning_foundations"),
    RequirementDefinition("deep learning", "capability", "deep_learning"),
    RequirementDefinition("computer vision", "capability", "computer_vision"),
    RequirementDefinition("database technologies", "capability", "databases"),
    RequirementDefinition("semantic search", "capability", "semantic_search"),
    RequirementDefinition("vector databases", "capability", "vector_databases"),
    RequirementDefinition("agents", "capability", "agentic_systems"),
    RequirementDefinition("llm observability", "capability", "llm_observability"),
    RequirementDefinition("model evaluation", "capability", "model_evaluation"),
    RequirementDefinition("model production and maintenance", "capability", "model_delivery"),
    RequirementDefinition("cloud (aws/azure/gcp)", "capability", "production_cloud"),
    RequirementDefinition("data visualization / web apps", "compound", components=(("visualization", "visualization"), ("web application delivery", "web_application_delivery"))),
    RequirementDefinition("nlp / llm", "compound", components=(("NLP", "nlp"), ("LLM", "llm_systems"))),
    RequirementDefinition("llms / agentic systems", "compound", components=(("LLMs", "llm_systems"), ("agentic systems", "agentic_systems"))),
    RequirementDefinition("tensorflow", "technology_specific", boundary="PyTorch is documented, but PyTorch is not TensorFlow."),
    RequirementDefinition("hadoop / spark", "compound", components=(("Hadoop", "hadoop"), ("Spark", "spark"))),
    RequirementDefinition("time series", "technology_specific", boundary="No time-series modelling evidence is present in the candidate profile."),
)


def _normalise(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _definition_for(requirement: str) -> RequirementDefinition | None:
    return next((item for item in REQUIREMENT_DEFINITIONS if item.label == _normalise(requirement)), None)


def _matched_skills(skills: list[str], anchors: tuple[str, ...]) -> list[str]:
    available = {_normalise(skill): skill for skill in skills}
    return [available[_normalise(anchor)] for anchor in anchors if _normalise(anchor) in available]


def _matched_evidence(candidate: CandidateProfile, record: str | None, anchors: tuple[str, ...], require_all: bool) -> str | None:
    if not record:
        return None
    for entry in candidate.other_evidence:
        if record.lower() not in entry.lower():
            continue
        checks = [anchor.lower() in entry.lower() for anchor in anchors]
        if not anchors or (all(checks) if require_all else any(checks)):
            return record
    return None


def _capability_match(candidate: CandidateProfile, capability: str) -> MatchResult:
    record = next((item for item in CAPABILITY_EVIDENCE if item.capability == capability), None)
    if record is None:
        return MatchResult(GAP, 0.0, STATUSES[GAP], f"No candidate evidence assertion exists for {capability.replace('_', ' ')}.")
    confirmed = _matched_skills(candidate.confirmed_skills, record.confirmed_skills)
    partial = _matched_skills(candidate.partial_skills, record.partial_skills)
    other = _matched_evidence(candidate, record.evidence_record, record.evidence_anchors, record.require_all_evidence_anchors)
    if confirmed or partial or other:
        sources = []
        if confirmed:
            sources.append(f"confirmed_skills: {', '.join(confirmed)}")
        if partial:
            sources.append(f"partial_skills: {', '.join(partial)}")
        if other:
            sources.append(f"other_evidence record: {other}")
        explanation = f"{record.rationale} Evidence: {'; '.join(sources)}."
        if record.boundary:
            explanation += f" Boundary: {record.boundary}"
        return MatchResult(record.classification, FACTORS[record.classification], STATUSES[record.classification], explanation)
    if not candidate.confirmed_skills and not candidate.partial_skills and not candidate.other_evidence:
        return MatchResult(UNKNOWN, 0.0, STATUSES[UNKNOWN], "No candidate skill or documented evidence is supplied.")
    return MatchResult(GAP, 0.0, STATUSES[GAP], f"No supporting controlled evidence for {capability.replace('_', ' ')} is present in the candidate profile.")


def _exact_skill_match(candidate: CandidateProfile, requirement: str) -> MatchResult | None:
    name = _normalise(requirement)
    confirmed = [_normalise(skill) for skill in candidate.confirmed_skills]
    partial = [_normalise(skill) for skill in candidate.partial_skills]
    if any(name in skill or skill in name for skill in confirmed):
        return MatchResult(DIRECT, 1.0, STATUSES[DIRECT], "Exact/contained match in confirmed_skills.")
    if any(name in skill or skill in name for skill in partial):
        return MatchResult(STRONG, 0.5, STATUSES[STRONG], "Exact/contained match in partial_skills; preserved v1 half-credit.")
    return None


def _compound_match(candidate: CandidateProfile, components: tuple[tuple[str, str], ...]) -> MatchResult:
    results = [(label, _capability_match(candidate, capability)) for label, capability in components]
    classes = [result.classification for _, result in results]
    if all(value == DIRECT for value in classes):
        classification = DIRECT
    elif DIRECT in classes and any(value in (STRONG, WEAK) for value in classes):
        classification = STRONG
    elif STRONG in classes:
        classification = STRONG
    elif WEAK in classes:
        classification = WEAK
    elif all(value == UNKNOWN for value in classes):
        classification = UNKNOWN
    else:
        classification = GAP
    details = "; ".join(f"{label}: {result.classification} — {result.explanation}" for label, result in results)
    return MatchResult(classification, FACTORS[classification], STATUSES[classification], f"Compound requirement decomposition: {details}")


def match_technical_requirement(candidate: CandidateProfile, requirement: str) -> MatchResult:
    """Resolve a requirement with exact labels and controlled evidence only."""
    definition = _definition_for(requirement)
    if definition:
        if definition.kind == "capability":
            return _capability_match(candidate, definition.capability or "")
        if definition.kind == "compound":
            return _compound_match(candidate, definition.components)
        return MatchResult(GAP, 0.0, STATUSES[GAP], f"Technology-specific requirement. {definition.boundary}")
    direct_skill = _exact_skill_match(candidate, requirement)
    if direct_skill:
        return direct_skill
    if not candidate.confirmed_skills and not candidate.partial_skills and not candidate.other_evidence:
        return MatchResult(UNKNOWN, 0.0, STATUSES[UNKNOWN], "No candidate skill or documented evidence is supplied.")
    return MatchResult(GAP, 0.0, STATUSES[GAP], "No exact skill match or controlled requirement definition is available.")

import unittest
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from cdi_assistant import cli
from cdi_assistant.models import CandidateProfile, JobOffer, TechnicalRequirement
from cdi_assistant.service import evaluate
from cdi_assistant.technical_matching import (DIRECT, GAP, STRONG, WEAK,
                                               match_technical_requirement)


class ScoringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        payload = json.loads(Path("data/candidate_profile.json").read_text(encoding="utf-8"))
        cls.canonical_candidate = CandidateProfile(**payload)

    def test_generic_software_role_is_hard_gated(self):
        result = evaluate(CandidateProfile(), JobOffer(company="X", position="Java developer", location="Paris, France", contract="CDI"))
        self.assertEqual(result.match_score["data_ai_relevance"], "0/25")
        self.assertEqual(result.final_decision["decision"], "DO NOT APPLY")

    def test_junior_data_offer_can_match_confirmed_evidence(self):
        candidate = CandidateProfile(confirmed_skills=["Python", "SQL"], years_experience=1, degree_level="Master", degree_fields=["Data"])
        job = JobOffer(company="X", position="Junior Data Engineer", location="France", contract="CDI", seniority="junior", min_years_experience=1, education_required="Master", education_fields=["Data"], technical_requirements=[TechnicalRequirement("Python"), TechnicalRequirement("SQL")])
        result = evaluate(candidate, job)
        self.assertEqual(result.match_score["technical_match"], "25/25")
        self.assertNotEqual(result.final_decision["decision"], "DO NOT APPLY")

    def test_direct_skill_match(self):
        result = match_technical_requirement(CandidateProfile(confirmed_skills=["Python"]), "Python")
        self.assertEqual(result.classification, DIRECT)
        self.assertEqual(result.factor, 1.0)

    def test_partial_skill_retains_existing_half_credit(self):
        result = match_technical_requirement(CandidateProfile(partial_skills=["Airflow"]), "Airflow")
        self.assertEqual(result.classification, STRONG)
        self.assertEqual(result.factor, 0.5)

    def test_related_ml_evidence_match(self):
        result = match_technical_requirement(self.canonical_candidate, "Machine Learning fundamentals")
        self.assertEqual(result.classification, STRONG)
        self.assertIn("other_evidence record: Projet MLOps churn (2026)", result.explanation)

    def test_semantic_search_uses_bounded_other_evidence(self):
        result = match_technical_requirement(self.canonical_candidate, "Semantic search")
        self.assertEqual(result.classification, DIRECT)
        self.assertIn("KBR PFE evidence", result.explanation)

    def test_broad_capabilities_use_controlled_constituents(self):
        expected_direct = (
            "Machine learning", "Deep learning", "Computer Vision",
            "Database technologies", "NLP / LLM",
            "Data visualization / web apps", "Model production and maintenance",
        )
        for requirement in expected_direct:
            with self.subTest(requirement=requirement):
                result = match_technical_requirement(self.canonical_candidate, requirement)
                self.assertEqual(result.classification, DIRECT)
                self.assertIn("Evidence:", result.explanation)

    def test_specific_tensorflow_hadoop_spark_and_time_series_remain_gaps(self):
        for requirement in ("TensorFlow", "Hadoop / Spark", "Time series"):
            with self.subTest(requirement=requirement):
                result = match_technical_requirement(self.canonical_candidate, requirement)
                self.assertEqual(result.classification, GAP)

    def test_aws_academy_is_not_production_cloud_direct_match(self):
        result = match_technical_requirement(self.canonical_candidate, "Cloud (AWS/Azure/GCP)")
        self.assertEqual(result.classification, WEAK)
        self.assertIn("No production AWS, Azure, or GCP experience", result.explanation)

    def test_weak_indirect_vector_database_evidence_is_not_direct(self):
        result = match_technical_requirement(CandidateProfile(confirmed_skills=["Neo4j", "Elasticsearch", "RAG"]), "Vector databases")
        self.assertEqual(result.classification, WEAK)
        self.assertLess(result.factor, 1.0)

    def test_agent_tooling_is_not_false_direct_agent_match(self):
        result = match_technical_requirement(CandidateProfile(confirmed_skills=["LangChain", "Qwen LLM", "RAG"]), "Agents")
        self.assertEqual(result.classification, WEAK)

    def test_general_monitoring_is_not_false_llm_observability_match(self):
        candidate = CandidateProfile(confirmed_skills=["MLflow"], other_evidence=["monitoring/dashboard"])
        result = match_technical_requirement(candidate, "LLM observability")
        self.assertEqual(result.classification, WEAK)

    def test_unknown_requirement_is_a_genuine_gap_when_profile_has_evidence(self):
        result = match_technical_requirement(CandidateProfile(confirmed_skills=["Python"]), "Kubernetes")
        self.assertEqual(result.classification, GAP)

    def test_compound_llm_and_agentic_requirement_is_decomposed(self):
        result = match_technical_requirement(CandidateProfile(confirmed_skills=["Qwen LLM", "RAG", "LangChain"]), "LLMs / agentic systems")
        self.assertEqual(result.classification, STRONG)
        self.assertIn("LLMs: DIRECT MATCH", result.explanation)
        self.assertIn("agentic systems: WEAK / INDIRECT EVIDENCE", result.explanation)


class CliTests(unittest.TestCase):
    def test_job_uses_canonical_profile_automatically(self):
        job_path = Path("examples/job_offer.json")
        with patch("sys.argv", ["cdi-evaluate", "--job", str(job_path)]), redirect_stdout(io.StringIO()) as output:
            cli.main()
        result = json.loads(output.getvalue())
        self.assertEqual(result["job_information"]["position"], "Junior Data Engineer")
        self.assertIn("Python", result["strong_matches"])
        self.assertEqual(result["requirement_assessments"][0]["match_strength"], DIRECT)

    def test_corma_job_loads_through_job_path(self):
        job_path = Path("examples/corma_junior_ai_engineer.json")
        with patch("sys.argv", ["cdi-evaluate", "--job", str(job_path)]), redirect_stdout(io.StringIO()) as output:
            cli.main()
        result = json.loads(output.getvalue())
        self.assertEqual(result["job_information"]["company"], "Corma")
        self.assertEqual(result["job_information"]["position"], "Junior AI Engineer")
        self.assertEqual(result["match_score"]["technical_match"], "19/25")
        self.assertEqual(result["final_decision"]["decision"], "APPLY — HIGH PRIORITY")
        contract_assessment = result["requirement_assessments"][-1]
        self.assertEqual(contract_assessment["requirement"], "CDI contract (UNKNOWN / VERIFY)")
        self.assertEqual(contract_assessment["status"], "unknown")

    def test_capgemini_job_uses_broad_capability_registry(self):
        job_path = Path("examples/capgemini_invent_data_scientist.json")
        with patch("sys.argv", ["cdi-evaluate", "--job", str(job_path)]), redirect_stdout(io.StringIO()) as output:
            cli.main()
        result = json.loads(output.getvalue())
        self.assertEqual(result["match_score"]["technical_match"], "19/25")
        self.assertEqual(result["final_decision"]["decision"], "APPLY — HIGH PRIORITY")
        assessments = {item["requirement"]: item for item in result["requirement_assessments"]}
        self.assertEqual(assessments["Deep learning"]["match_strength"], DIRECT)
        self.assertEqual(assessments["TensorFlow"]["match_strength"], GAP)
        self.assertEqual(assessments["Cloud (AWS/Azure/GCP)"]["match_strength"], WEAK)

    def test_input_remains_supported(self):
        with TemporaryDirectory() as directory:
            request_path = Path(directory) / "request.json"
            request_path.write_text(json.dumps({
                "candidate": {"confirmed_skills": ["Python"]},
                "job": {"company": "X", "position": "Data Engineer", "location": "Paris, France", "technical_requirements": [{"name": "Python"}]}
            }), encoding="utf-8")
            with patch("sys.argv", ["cdi-evaluate", "--input", str(request_path)]), redirect_stdout(io.StringIO()) as output:
                cli.main()
        result = json.loads(output.getvalue())
        self.assertEqual(result["job_information"]["company"], "X")
        self.assertIn("Python", result["strong_matches"])

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .models import CandidateProfile, JobOffer, TechnicalRequirement
from .pdf_extraction import PdfExtractionError, extract_pdf, ingest_pdf_documents
from .service import evaluate

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_PROFILE_PATH = PROJECT_ROOT / "data" / "candidate_profile.json"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _job_from_data(job_data: dict) -> JobOffer:
    job_data = job_data.copy()
    job_data["technical_requirements"] = [
        TechnicalRequirement(**item) for item in job_data.get("technical_requirements", [])
    ]
    return JobOffer(**job_data)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate a French Data/AI CDI job offer.")
    parser.add_argument("--input", type=Path, help="JSON file containing candidate and job.")
    parser.add_argument("--job", type=Path, help="Job-offer JSON, or a job PDF for extraction-only ingestion.")
    parser.add_argument("--cv", type=Path, help="CV PDF for extraction-only ingestion with a PDF job offer.")
    parser.add_argument("--extract-pdf", type=Path, help="Extract one PDF to JSON without evaluation or parsing.")
    args = parser.parse_args()
    if args.extract_pdf:
        if args.input or args.job or args.cv:
            parser.error("--extract-pdf cannot be combined with --input, --job, or --cv.")
        try:
            print(json.dumps(extract_pdf(args.extract_pdf).to_dict(), ensure_ascii=False, indent=2))
        except PdfExtractionError as error:
            parser.error(str(error))
        return
    if args.input and (args.job or args.cv):
        parser.error("--input cannot be combined with --job or --cv.")
    if args.cv or (args.job and args.job.suffix.lower() == ".pdf"):
        if args.job is not None and args.job.suffix.lower() != ".pdf":
            parser.error("--cv is available only with a PDF supplied through --job.")
        try:
            print(json.dumps(ingest_pdf_documents(args.cv, args.job).to_dict(), ensure_ascii=False, indent=2))
        except PdfExtractionError as error:
            parser.error(str(error))
        return
    if args.job:
        candidate = CandidateProfile(**_load_json(CANONICAL_PROFILE_PATH))
        job = _job_from_data(_load_json(args.job))
    elif args.input:
        payload = _load_json(args.input)
        candidate = CandidateProfile(**payload["candidate"])
        job = _job_from_data(payload["job"])
    else:
        parser.error("one of --input, --job, or --extract-pdf is required.")
    print(json.dumps(evaluate(candidate, job).to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

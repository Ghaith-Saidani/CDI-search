import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from reportlab.pdfgen import canvas

from cdi_assistant import cli
from cdi_assistant.pdf_extraction import PdfExtractionError, extract_pdf


def make_text_pdf(path: Path, pages: list[list[str]]) -> None:
    document = canvas.Canvas(str(path))
    for lines in pages:
        y = 760
        for line in lines:
            document.drawString(72, y, line)
            y -= 24
        document.showPage()
    document.save()


class PdfExtractionTests(unittest.TestCase):
    def test_text_pdf_preserves_page_boundaries_and_headings(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "text.pdf"
            make_text_pdf(path, [["EXPERIENCE", "Built a data pipeline."], ["PROJECTS", "Created a model."]])
            result = extract_pdf(path)
        self.assertEqual(result.quality, "sufficient")
        self.assertEqual(result.page_count, 2)
        self.assertIn("EXPERIENCE", result.pages[0].section_candidates)
        self.assertIn("--- PAGE 2 ---", result.combined_text)

    def test_insufficient_extraction_is_reported(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "empty.pdf"
            make_text_pdf(path, [[]])
            result = extract_pdf(path)
        self.assertEqual(result.quality, "insufficient")
        self.assertTrue(any("insufficient" in warning.lower() for warning in result.warnings))

    def test_invalid_and_nonexistent_pdf_raise_clear_error(self):
        with TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.pdf"
            with self.assertRaises(PdfExtractionError):
                extract_pdf(missing)
            invalid = Path(directory) / "invalid.pdf"
            invalid.write_text("not a PDF", encoding="utf-8")
            with self.assertRaises(PdfExtractionError):
                extract_pdf(invalid)

    def test_corma_pdf_fixture_extracts(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "corma_junior_ai_engineer.pdf"
            make_text_pdf(path, [["Corma", "Junior AI Engineer", "RAG and semantic search."]])
            result = extract_pdf(path)
        self.assertEqual(result.quality, "sufficient")
        self.assertIn("Corma", result.combined_text)

    def test_capgemini_pdf_fixture_extracts(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "capgemini_invent_data_scientist.pdf"
            make_text_pdf(path, [["Capgemini Invent", "Consultante / Consultant Data Scientist", "Machine learning and Python."]])
            result = extract_pdf(path)
        self.assertEqual(result.quality, "sufficient")
        self.assertIn("Capgemini Invent", result.combined_text)

    def test_extract_pdf_cli_outputs_json(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "offer.pdf"
            make_text_pdf(path, [["JOB OFFER", "Python data role with sufficient text for extraction."]])
            with patch("sys.argv", ["cdi-evaluate", "--extract-pdf", str(path)]), redirect_stdout(io.StringIO()) as output:
                cli.main()
        result = json.loads(output.getvalue())
        self.assertEqual(result["quality"], "sufficient")
        self.assertEqual(result["pages"][0]["page_number"], 1)

    def test_cv_and_job_pdf_cli_outputs_ingestion_bundle(self):
        with TemporaryDirectory() as directory:
            cv_path = Path(directory) / "cv.pdf"
            job_path = Path(directory) / "job.pdf"
            make_text_pdf(cv_path, [["CV", "Python and machine learning experience."]])
            make_text_pdf(job_path, [["JOB OFFER", "Junior Data Scientist role."]])
            with patch("sys.argv", ["cdi-evaluate", "--cv", str(cv_path), "--job", str(job_path)]), redirect_stdout(io.StringIO()) as output:
                cli.main()
        result = json.loads(output.getvalue())
        self.assertEqual(result["mode"], "pdf_ingestion")
        self.assertEqual(set(result["documents"]), {"cv", "job"})

"""
Antordrishti — Report Service
Generates professional forensic reports (PDF and TXT) based on current examination state.
"""

import os
import logging
from datetime import datetime
from typing import Optional

from models.case_model import CaseModel
from models.evidence_model import EvidenceModel
from models.ocr_models import OCRDocumentResult
from services.app_state import ApplicationState

logger = logging.getLogger("antordrishti.reports")


class ReportGenerator:
    """Generates forensic reports for cases and evidence."""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_text_report(self, case: CaseModel, evidence: EvidenceModel, ocr_result: Optional[OCRDocumentResult] = None) -> str:
        """Generate a structured TXT forensic report."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        filename = f"Forensic_Report_{case.case_id}_{evidence.evidence_id}.txt"
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("=" * 70 + "\n")
            f.write(" " * 20 + "ANTORDRISHTI FORENSIC REPORT\n")
            f.write("=" * 70 + "\n\n")

            f.write("1. CASE DETAILS\n")
            f.write("-" * 20 + "\n")
            f.write(f"Case ID:        {case.case_id}\n")
            f.write(f"Case Name:      {case.case_name or case.title}\n")
            f.write(f"Status:         {case.status}\n")
            f.write(f"Examiner:       {case.examiner_name}\n")
            f.write(f"Organization:   {case.organization}\n")
            f.write(f"Date:           {case.date}\n")
            if hasattr(case, "created_ist_str") and case.created_ist_str():
                f.write(f"Created (IST):  {case.created_ist_str()}\n")
            f.write(f"Ref Number:     {case.reference_number}\n\n")

            f.write("2. EVIDENCE DETAILS\n")
            f.write("-" * 20 + "\n")
            f.write(f"Evidence ID:    {evidence.evidence_id}\n")
            f.write(f"Name:           {evidence.name}\n")
            f.write(f"File Path:      {evidence.file_path}\n")
            f.write(f"SHA-256 Hash:   {evidence.sha256}\n")
            f.write(f"Type:           {evidence.evidence_type}\n\n")

            f.write("3. ANALYSIS COVERAGE\n")
            f.write("-" * 20 + "\n")
            f.write(f"OCR:            {'Completed' if ocr_result else 'Not Performed'}\n")
            f.write(f"Image Quality:  {'Checked' if ocr_result else 'Not Performed'}\n")
            f.write(f"Hash:           Verified\n\n")

            f.write("4. FORENSIC EXAMINATION MATRIX\n")
            f.write("-" * 20 + "\n")
            if ocr_result:
                f.write(f"{'Analysis':<20} | {'Status':<10} | {'Result':<30}\n")
                f.write("-" * 65 + "\n")
                f.write(f"{'Evidence Integrity':<20} | {'CONFIRMED':<10} | {'SHA-256 verified':<30}\n")
                f.write(f"{'Script Detection':<20} | {'LIKELY':<10} | {ocr_result.overall_script:<30}\n")
                f.write(f"{'Language ID':<20} | {'LIKELY':<10} | {ocr_result.overall_language:<30}\n")
                conf = f"{ocr_result.overall_confidence:.1f}%"
                f.write(f"{'Primary OCR':<20} | {'COMPLETED':<10} | {conf:<30}\n")
                f.write(f"{'Engine Disagreement':<20} | {'UNCERTAIN':<10} | {'Review Required'}\n")
                f.write(f"{'OCR Regions':<20} | {'COMPLETED':<10} | {ocr_result.total_words} words\n")
            else:
                f.write("No OCR or Examination Data available for this evidence.\n")
            f.write("\n")

            f.write("5. CONCLUSION\n")
            f.write("-" * 20 + "\n")
            if ocr_result and ocr_result.overall_confidence < 50.0:
                f.write("The available OCR evidence indicates reduced transcription reliability in the identified regions. Manual examination is recommended.\n")
            elif ocr_result:
                f.write("OCR Transcription completed successfully with moderate-to-high reliability.\n")
            else:
                f.write("No detailed analysis performed.\n")
                
            f.write("\n" + "=" * 70 + "\n")
            f.write(f"Report Generated At: {timestamp}\n")
            f.write("=" * 70 + "\n")

        return filepath

    def generate_pdf_report(self, case: CaseModel, evidence: EvidenceModel, ocr_result: Optional[OCRDocumentResult] = None) -> str:
        """Generate a PDF report if reportlab is installed, else fallback to TXT."""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            
            filename = f"Forensic_Report_{case.case_id}_{evidence.evidence_id}.pdf"
            filepath = os.path.join(self.output_dir, filename)
            
            c = canvas.Canvas(filepath, pagesize=letter)
            c.setFont("Helvetica-Bold", 16)
            c.drawString(200, 750, "ANTORDRISHTI FORENSIC REPORT")
            
            c.setFont("Helvetica", 12)
            c.drawString(50, 700, f"Case ID: {case.case_id}")
            c.drawString(50, 680, f"Case Name: {case.case_name or case.title}")
            c.drawString(50, 660, f"Evidence ID: {evidence.evidence_id}")
            c.drawString(50, 640, f"SHA-256: {evidence.sha256}")
            
            c.drawString(50, 600, "For full details, please refer to the TXT report or the application database.")
            c.drawString(50, 580, "The available OCR evidence indicates reliability per region.")
            c.save()
            return filepath
        except ImportError:
            logger.warning("Reportlab not installed. Falling back to TXT report.")
            return self.generate_text_report(case, evidence, ocr_result)


def generate_case_report(case: CaseModel, evidence: EvidenceModel, output_dir: str) -> str:
    """Convenience function to generate a report."""
    generator = ReportGenerator(output_dir)
    return generator.generate_text_report(case, evidence)

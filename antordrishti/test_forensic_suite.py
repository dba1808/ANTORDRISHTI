"""
Verification Test Suite for ANTORDRISHTI
Tests CaseModel root-cause fix, schema migration, universal context,
and forensic metadata extraction across multiple image and PDF formats.
"""

import os
import sys
import tempfile
import unittest
from datetime import datetime

# Add project root to sys.path
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

from models.case_model import CaseModel, IST_TZ
from models.evidence_model import EvidenceModel
from models.document_model import DocumentModel
from services.db_service import DatabaseService
from services.app_state import ApplicationState, CurrentDocumentContext
from services.forensic_metadata_service import (
    examine_evidence_metadata,
    detect_file_signature,
    inspect_jpeg_structure,
    inspect_png_structure,
    inspect_tiff_structure,
    inspect_webp_structure,
    inspect_pdf_forensics,
    export_metadata_to_json,
    export_metadata_to_txt
)


class TestAntordrishtiForensicSuite(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_forensic.db")
        self.db = DatabaseService(self.db_path)

    def tearDown(self):
        self.db.close()

    def test_01_case_model_canonical_fields_and_aliases(self):
        """Test CaseModel.case_name canonical field and aliases."""
        case = CaseModel(
            case_id="CASE-2026-000123",
            case_name="Questioned Document Analysis",
            examiner_name="Forensic Examiner A",
            status="OPEN"
        )
        # Verify case_name and title are synchronized
        self.assertEqual(case.case_name, "Questioned Document Analysis")
        self.assertEqual(case.title, "Questioned Document Analysis")
        # Verify case_number alias
        self.assertEqual(case.case_number, "CASE-2026-000123")
        # Verify examiner alias
        self.assertEqual(case.examiner, "Forensic Examiner A")
        # Verify IST string
        self.assertIn("IST", case.created_ist_str())

        # Verify serialization and deserialization
        d = case.to_dict()
        self.assertEqual(d["case_name"], "Questioned Document Analysis")
        self.assertEqual(d["title"], "Questioned Document Analysis")

        restored = CaseModel.from_dict(d)
        self.assertEqual(restored.case_name, "Questioned Document Analysis")
        self.assertEqual(restored.title, "Questioned Document Analysis")
        self.assertEqual(restored.case_id, "CASE-2026-000123")

    def test_02_database_case_creation_and_auto_id(self):
        """Test CASE-YYYY-NNNNNN generation and persistence."""
        auto_id_1 = self.db.generate_case_id()
        year = datetime.now().strftime("%Y")
        self.assertTrue(auto_id_1.startswith(f"CASE-{year}-"))
        self.assertEqual(len(auto_id_1.split("-")[-1]), 6)

        case_data = {
            "case_id": auto_id_1,
            "case_name": "State vs Examiner Test",
            "examiner_name": "Dr. Sen",
            "status": "OPEN",
            "organization": "Forensic Science Lab"
        }
        success = self.db.create_case(case_data)
        self.assertTrue(success)

        # Retrieve and verify
        row = self.db.get_case(auto_id_1)
        self.assertIsNotNone(row)
        self.assertEqual(row["case_name"], "State vs Examiner Test")
        self.assertEqual(row["title"], "State vs Examiner Test")

        # Next auto ID must increment
        auto_id_2 = self.db.generate_case_id()
        self.assertNotEqual(auto_id_1, auto_id_2)

    def test_03_database_schema_migration_preserves_old_cases(self):
        """Verify that older records with only title receive case_name."""
        # Insert raw row with title only
        self.db._conn.execute(
            "INSERT INTO cases (case_id, title, examiner, created_at, modified_at) VALUES (?, ?, ?, ?, ?)",
            ("OLD-CASE-001", "Legacy Case Title", "Old Examiner", "2025-01-01T00:00:00", "2025-01-01T00:00:00")
        )
        self.db._conn.commit()

        # Re-run schema initialization/migration
        self.db._init_schema()

        row = self.db.get_case("OLD-CASE-001")
        self.assertEqual(row["case_name"], "Legacy Case Title")
        self.assertEqual(row["title"], "Legacy Case Title")

    def test_04_universal_app_state(self):
        """Test ApplicationState broadcast and CurrentDocumentContext."""
        state = ApplicationState()
        notified_contexts = []

        def on_context(ctx):
            notified_contexts.append(ctx)

        state.context_changed.connect(on_context)

        case = CaseModel(case_id="CASE-2026-000001", case_name="Context Test Case")
        state.set_case(case)

        self.assertEqual(len(notified_contexts), 1)
        self.assertEqual(notified_contexts[-1].case.case_name, "Context Test Case")
        self.assertIsNone(notified_contexts[-1].document)

        # Clear document, keep case
        state.clear_document(keep_case=True)
        self.assertEqual(notified_contexts[-1].case.case_id, "CASE-2026-000001")
        self.assertIsNone(notified_contexts[-1].document)

    def test_05_jpeg_metadata_and_quantization_analysis(self):
        """Test deep JPEG inspection with EXIF, COM, and DQT."""
        from PIL import Image, ExifTags
        test_jpg = os.path.join(self.temp_dir, "test_sample.jpg")

        # Create image with EXIF and comment
        img = Image.new("RGB", (320, 240), color=(100, 150, 200))
        exif = img.getexif()
        exif[ExifTags.Base.Make] = "Nikon Forensic"
        exif[ExifTags.Base.Model] = "D850-Forensic"
        exif[ExifTags.Base.Software] = "Antordrishti Test Harness"
        exif[ExifTags.Base.DateTime] = "2026:09:14 10:30:00"

        img.save(test_jpg, "JPEG", exif=exif, comment=b"Forensic Evidence Sample #42", quality=85)

        exam = examine_evidence_metadata(test_jpg, case_id="CASE-2026-000001", evidence_id="EVD-000001")
        self.assertEqual(exam["signature"]["detected_format"], "JPEG")
        self.assertTrue(exam["signature"]["is_consistent"])
        self.assertEqual(exam["exif"]["camera_make"], "Nikon Forensic")
        self.assertEqual(exam["exif"]["camera_model"], "D850-Forensic")
        self.assertEqual(exam["exif"]["software"], "Antordrishti Test Harness")
        self.assertTrue(exam["jpeg"]["is_jpeg"])
        self.assertIn("Forensic Evidence Sample #42", exam["jpeg"]["comments"])
        self.assertIsNotNone(exam["jpeg"]["estimated_quality"])

    def test_06_png_metadata_and_chunks(self):
        """Test deep PNG chunk and tEXt inspection."""
        from PIL import Image, PngImagePlugin
        test_png = os.path.join(self.temp_dir, "test_sample.png")

        img = Image.new("RGB", (200, 150), color=(50, 80, 120))
        meta = PngImagePlugin.PngInfo()
        meta.add_text("Author", "Forensic Lab Analyst")
        meta.add_text("Description", "Questioned Signature Scan")
        img.save(test_png, "PNG", pnginfo=meta)

        exam = examine_evidence_metadata(test_png, case_id="CASE-2026-000001", evidence_id="EVD-000002")
        self.assertEqual(exam["signature"]["detected_format"], "PNG")
        self.assertTrue(exam["signature"]["is_consistent"])
        self.assertTrue(exam["png"]["is_png"])
        self.assertEqual(exam["png"]["text_metadata"].get("Author"), "Forensic Lab Analyst")
        self.assertEqual(exam["png"]["text_metadata"].get("Description"), "Questioned Signature Scan")

    def test_07_format_mismatch_detection(self):
        """Verify that a PNG renamed to .jpg is caught as a FORMAT MISMATCH."""
        from PIL import Image
        fake_jpg = os.path.join(self.temp_dir, "fake_photo.jpg")
        img = Image.new("RGB", (100, 100), color=(255, 0, 0))
        # Save as PNG despite .jpg extension
        img.save(fake_jpg, "PNG")

        sig = detect_file_signature(fake_jpg)
        self.assertEqual(sig["detected_format"], "PNG")
        self.assertEqual(sig["declared_ext"], "JPG")
        self.assertFalse(sig["is_consistent"])
        self.assertIn("FORMAT MISMATCH", sig["warning"])

        exam = examine_evidence_metadata(fake_jpg)
        self.assertIn("FORMAT MISMATCH", exam["summary"]["flags"])

    def test_08_pdf_forensic_examination(self):
        """Test PDF forensic metadata extraction via PyMuPDF."""
        try:
            import fitz
        except ImportError:
            self.skipTest("PyMuPDF not installed")

        test_pdf = os.path.join(self.temp_dir, "test_doc.pdf")
        doc = fitz.open()
        page = doc.new_page(width=595, height=842)
        page.insert_text((50, 100), "ANTORDRISHTI QUESTIONED DOCUMENT EVIDENCE\nLine 2 Native PDF Text")
        doc.set_metadata({
            "title": "Questioned Will Examination",
            "author": "Forensic Expert",
            "creator": "LibreOffice 7.5",
            "producer": "PyMuPDF PDF Generator",
            "creationDate": "D:20260914100000+05'30'"
        })
        doc.save(test_pdf)
        doc.close()

        exam = examine_evidence_metadata(test_pdf, case_id="CASE-2026-000001", evidence_id="EVD-000003")
        self.assertEqual(exam["signature"]["detected_format"], "PDF")
        self.assertTrue(exam["pdf"]["is_pdf"])
        self.assertEqual(exam["pdf"]["page_count"], 1)
        self.assertEqual(exam["pdf"]["info"]["title"], "Questioned Will Examination")
        self.assertIn("Questioned Will Examination", [r[1] for r in exam["pdf"]["rows"] if r[0] == "Title"])
        self.assertIn("Native PDF Text", exam["pdf"]["native_text"])
        self.assertEqual(exam["pdf"]["page_classification"][0]["classification"], "TEXT")

    def test_09_export_json_and_txt(self):
        """Test exporting metadata report to JSON and TXT without crashing."""
        from PIL import Image
        test_img = os.path.join(self.temp_dir, "export_test.jpg")
        Image.new("RGB", (100, 100)).save(test_img, "JPEG")

        exam = examine_evidence_metadata(test_img, case_id="CASE-2026-000001", evidence_id="EVD-000004")
        json_out = os.path.join(self.temp_dir, "report.json")
        txt_out = os.path.join(self.temp_dir, "report.txt")

        ok_json = export_metadata_to_json(exam, json_out)
        ok_txt = export_metadata_to_txt(exam, txt_out)

        self.assertTrue(ok_json)
        self.assertTrue(ok_txt)
        self.assertTrue(os.path.exists(json_out) and os.path.getsize(json_out) > 0)
        self.assertTrue(os.path.exists(txt_out) and os.path.getsize(txt_out) > 0)

    def test_10_corrupt_file_handling(self):
        """Test zero-byte and corrupt files without unhandled crashes."""
        zero_file = os.path.join(self.temp_dir, "zero.jpg")
        with open(zero_file, "wb") as f:
            pass  # 0 bytes

        sig = detect_file_signature(zero_file)
        self.assertEqual(sig["detected_format"], "UNKNOWN")

        exam = examine_evidence_metadata(zero_file)
        self.assertIsNotNone(exam)
        self.assertEqual(exam["summary"]["metadata_status"], "LIMITED")


if __name__ == "__main__":
    unittest.main()

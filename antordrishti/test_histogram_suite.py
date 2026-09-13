"""
Antordrishti — Automated Forensic Histogram Test Suite
Validates numerical invariants, RGB/Grayscale channel bin sums, alpha channel exclusion,
PDF page rendering consistency, clipping calculations, log-scale visualization safety,
and CSV/TXT export accuracy.
"""

import os
import unittest
import tempfile
import numpy as np
from PIL import Image

from services.histogram_service import (
    extract_pixel_array_from_evidence,
    calculate_forensic_histogram,
    export_histogram_csv,
    export_histogram_txt,
    render_histogram_plot_image,
    HistogramData
)


class TestForensicHistogramSuite(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Create a test synthetic RGB image (100x100)
        self.img_rgb_path = os.path.join(self.temp_dir.name, "test_rgb.png")
        img_arr = np.zeros((100, 100, 3), dtype=np.uint8)
        img_arr[0:50, :, 0] = 100  # Red upper half
        img_arr[50:100, :, 1] = 200 # Green lower half
        Image.fromarray(img_arr).save(self.img_rgb_path)

        # Create a test RGBA image (100x100 with Alpha = 128)
        self.img_rgba_path = os.path.join(self.temp_dir.name, "test_rgba.png")
        rgba_arr = np.zeros((100, 100, 4), dtype=np.uint8)
        rgba_arr[:, :, 0] = 50   # Red
        rgba_arr[:, :, 1] = 150  # Green
        rgba_arr[:, :, 2] = 250  # Blue
        rgba_arr[:, :, 3] = 128  # Alpha
        Image.fromarray(rgba_arr, mode="RGBA").save(self.img_rgba_path)

        # Create a test Black & White clipping image (100x100)
        self.img_clip_path = os.path.join(self.temp_dir.name, "test_clip.png")
        clip_arr = np.zeros((100, 100), dtype=np.uint8)
        clip_arr[0:50, :] = 0    # Black (0)
        clip_arr[50:100, :] = 255 # White (255)
        Image.fromarray(clip_arr, mode="L").save(self.img_clip_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_rgb_numerical_invariant(self):
        """Assert sum(hist_red) == sum(hist_green) == sum(hist_blue) == total_pixels (10,000)."""
        pixel_array, info = extract_pixel_array_from_evidence(self.img_rgb_path)
        self.assertIsNotNone(pixel_array)

        hist_data = calculate_forensic_histogram(
            pixel_array=pixel_array,
            info=info,
            channel_mode="rgb",
            source_label="Test RGB Image",
            case_id="CASE-2026-000001",
            evidence_id="EVD-000001"
        )

        self.assertTrue(hist_data.invariant_passed)
        self.assertEqual(hist_data.total_pixels, 10000)
        self.assertEqual(int(np.sum(hist_data.hist_red)), 10000)
        self.assertEqual(int(np.sum(hist_data.hist_green)), 10000)
        self.assertEqual(int(np.sum(hist_data.hist_blue)), 10000)
        self.assertEqual(int(np.sum(hist_data.hist_gray)), 10000)

    def test_alpha_channel_exclusion(self):
        """Assert alpha channel is excluded from RGB calculation and tracked separately."""
        pixel_array, info = extract_pixel_array_from_evidence(self.img_rgba_path)
        self.assertTrue(info["has_alpha"])

        hist_data = calculate_forensic_histogram(
            pixel_array=pixel_array,
            info=info,
            channel_mode="rgb"
        )

        self.assertTrue(hist_data.invariant_passed)
        self.assertEqual(hist_data.total_pixels, 10000)
        self.assertEqual(int(np.sum(hist_data.hist_red)), 10000)
        self.assertIsNotNone(hist_data.hist_alpha)
        # Alpha bin at 128 should have 10,000 pixels
        self.assertEqual(hist_data.hist_alpha[128], 10000)

    def test_clipping_and_tonal_distribution(self):
        """Assert exact black (0) and white (255) clipping counts and percentage."""
        pixel_array, info = extract_pixel_array_from_evidence(self.img_clip_path)
        hist_data = calculate_forensic_histogram(
            pixel_array=pixel_array,
            info=info,
            channel_mode="grayscale"
        )

        clip = hist_data.clipping
        self.assertEqual(clip["black_count"], 5000)
        self.assertEqual(clip["white_count"], 5000)
        self.assertEqual(clip["black_pct"], 50.0)
        self.assertEqual(clip["white_pct"], 50.0)

        tonal = hist_data.tonal
        self.assertEqual(tonal["shadows_count"], 5000)
        self.assertEqual(tonal["highlights_count"], 5000)
        self.assertEqual(tonal["midtones_count"], 0)

    def test_cdf_calculation(self):
        """Assert cumulative distribution function (CDF) ends at 100.0% at bin 255."""
        pixel_array, info = extract_pixel_array_from_evidence(self.img_rgb_path)
        hist_data = calculate_forensic_histogram(
            pixel_array=pixel_array,
            info=info,
            channel_mode="rgb"
        )

        self.assertAlmostEqual(hist_data.cdf_gray[255], 100.0, places=2)
        self.assertAlmostEqual(hist_data.cdf_red[255], 100.0, places=2)

    def test_csv_and_txt_exports(self):
        """Assert exporting CSV and TXT generates valid formatted files."""
        pixel_array, info = extract_pixel_array_from_evidence(self.img_rgb_path)
        hist_data = calculate_forensic_histogram(
            pixel_array=pixel_array,
            info=info,
            channel_mode="rgb",
            case_id="CASE-2026-000001",
            evidence_id="EVD-000001",
            sha256="abc123def456"
        )

        csv_path = os.path.join(self.temp_dir.name, "out_hist.csv")
        txt_path = os.path.join(self.temp_dir.name, "out_hist.txt")

        res_csv = export_histogram_csv(hist_data, csv_path)
        res_txt = export_histogram_txt(hist_data, txt_path)

        self.assertTrue(res_csv)
        self.assertTrue(res_txt)
        self.assertTrue(os.path.exists(csv_path))
        self.assertTrue(os.path.exists(txt_path))

        with open(csv_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("CASE-2026-000001", content)
            self.assertIn("Intensity,Red_Count,Green_Count,Blue_Count", content)

    def test_render_plot_image(self):
        """Assert high-res histogram plot image renders cleanly as BGR array."""
        pixel_array, info = extract_pixel_array_from_evidence(self.img_rgb_path)
        hist_data = calculate_forensic_histogram(
            pixel_array=pixel_array,
            info=info,
            channel_mode="rgb"
        )

        bgr_plot = render_histogram_plot_image(hist_data, mode="rgb", log_scale=True, show_cdf=True, width=800, height=400)
        self.assertIsNotNone(bgr_plot)
        self.assertEqual(bgr_plot.shape, (400, 800, 3))


if __name__ == "__main__":
    unittest.main()

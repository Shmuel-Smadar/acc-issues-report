import unittest
from core.services.utils import norm_date, with_viewable_param, clean_comment_text, extract_viewable_guid
from tests.logging_config import CaseLoggerMixin


class UtilsTests(CaseLoggerMixin, unittest.TestCase):
    def test_norm_date_z_suffix(self):
        out = norm_date("2025-08-01T12:34:56Z")
        self.assertEqual(out, "2025-08-01")

    def test_norm_date_passthrough(self):
        out1 = norm_date("not-a-date")
        out2 = norm_date(None)
        self.assertEqual(out1, "not-a-date")
        self.assertEqual(out2, "")

    def test_with_viewable_param_adds_param(self):
        url = "https://example.com/view?x=1"
        out = with_viewable_param(url, "abc")
        self.assertIn("viewableGuid=abc", out)
        self.assertTrue(out.startswith("https://example.com/view?"))

    def test_clean_comment_text_collapses_whitespace(self):
        s = " line1\r\nline2 \n  line3 "
        out = clean_comment_text(s)
        self.assertEqual(out, "line1 line2 line3")

    def test_extract_viewable_guid_variants(self):
        issue1 = {"placements": [{"viewable": {"guid": "g1"}}]}
        issue2 = {"linkedDocuments": [{"details": {"viewable": {"id": "g2"}}}]}
        issue3 = {}
        out1 = extract_viewable_guid(issue1)
        out2 = extract_viewable_guid(issue2)
        out3 = extract_viewable_guid(issue3)
        self.assertEqual(out1, "g1")
        self.assertEqual(out2, "g2")
        self.assertIsNone(out3)

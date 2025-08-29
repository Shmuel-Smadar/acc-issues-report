import unittest
from core.services.csv_export import rows_to_csv
from core.dto import IssueRow
from tests.logging_config import CaseLoggerMixin


class CsvExportTests(CaseLoggerMixin, unittest.TestCase):
    def test_rows_to_csv_includes_headers_and_rows(self):
        row = IssueRow(
            project_id="p",
            project_name="n",
            document_id="d1",
            document_name="doc.pdf",
            document_path="Root",
            web_link="http://x",
            issue_id="i1",
            issue_type="T",
            issue_sub_type="S",
            issue_status="open",
            issue_due_date="2025-08-20",
            issue_start_date="2025-08-10",
            issue_title="Title",
            issue_description="Desc",
            issue_comments="C1",
        )
        content = rows_to_csv([row])
        s = content.decode("utf-8")
        self.assertIn("project id,project name,document id,document name,document path,link to the document page the issue located in,issue id,issue type,issue sub type,issue status,issue due date,issue start date,issue title,issue description,issue comments", s)
        self.assertIn("p,n,d1,doc.pdf,Root,http://x,i1,T,S,open,2025-08-20,2025-08-10,Title,Desc,C1", s)

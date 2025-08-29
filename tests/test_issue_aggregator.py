from django.test import SimpleTestCase, override_settings
from core.dto import Document
from core.services.aggregate import IssueAggregator
from tests.logging_config import CaseLoggerMixin


class FakeIssues:
    def __init__(self, type_map, subtype_map, comments_map):
        self._type_map = type_map
        self._subtype_map = subtype_map
        self._comments_map = comments_map

    def issue_types_map(self, project_id):
        return self._type_map, self._subtype_map

    def get_comments(self, project_id, issue_id):
        return self._comments_map.get(issue_id, [])


class FakeClient:
    def __init__(self, issues_list, docs_by_urn, comments_map):
        self._issues_list = issues_list
        self._docs_by_urn = docs_by_urn
        self.issues = FakeIssues({"t1": "Quality"}, {"s1": "Clash"}, comments_map)

    def get_project_id_by_name(self, name):
        return "b.pid123"

    def list_issues(self, issues_project_id):
        return self._issues_list

    def get_item_info(self, dm_project_id, urn):
        return self._docs_by_urn.get(urn)


@override_settings(TARGET_PROJECT_NAME="DEV TASK 1 Project")
class IssueAggregatorTests(CaseLoggerMixin, SimpleTestCase):
    def test_collect_rows_filters_non_pdfs_and_maps_types(self):
        issues_list = [
            {
                "id": "i1",
                "issueTypeId": "t1",
                "issueSubtypeId": "s1",
                "status": "open",
                "dueDate": "2025-08-20T10:00:00Z",
                "startDate": "2025-08-10T10:00:00Z",
                "title": "A",
                "description": "desc",
                "placements": [{"lineageUrn": "urn:1", "viewable": {"guid": "g123"}}],
                "linkedDocuments": [{"urn": "urn:2", "details": {"viewable": {"id": "g999"}}}],
            }
        ]
        docs_by_urn = {
            "urn:1": Document(id="urn:1", name="plan.pdf", path="Root/Plans", web_link="https://acc/doc1", is_pdf=True),
            "urn:2": Document(id="urn:2", name="notes.txt", path="Root/Notes", web_link="https://acc/doc2", is_pdf=False),
        }
        comments_map = {
            "i1": [
                {"createdAt": "2025-08-01T10:00:00Z", "body": " First "},
                {"createdAt": "2025-08-02T10:00:00Z", "body": " Second "},
            ]
        }
        client = FakeClient(issues_list, docs_by_urn, comments_map)
        rows = IssueAggregator(client).collect_rows()
        self.assertEqual(len(rows), 1)
        r = rows[0].to_csv_row()
        self.assertEqual(r["issue type"], "Quality")
        self.assertEqual(r["issue sub type"], "Clash")
        self.assertEqual(r["issue due date"], "2025-08-20")
        self.assertIn("viewableGuid=g123", r["link to the document page the issue located in"])
        self.assertEqual(r["issue comments"], "First, Second")

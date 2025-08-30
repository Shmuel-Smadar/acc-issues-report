from unittest.mock import patch
from django.test import TestCase, Client, override_settings
from core.dto import IssueRow
from tests.logging_config import CaseLoggerMixin


@override_settings(
    FORGE_CLIENT_ID="cid",
    FORGE_CLIENT_SECRET="sec",
    FORGE_CALLBACK_URL="http://testserver/auth/callback/",
    FORGE_SCOPE="account:read data:read",
    FORGE_BASE_URL="https://developer.api.autodesk.com",
    TARGET_PROJECT_NAME="DEV TASK 1 Project",
    ACC_ACCOUNT_ID="acc123",
)
class WebViewsTests(CaseLoggerMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.client = Client()

    def test_index_unauthenticated(self):
        class DummyQS:
            def order_by(self, *args, **kwargs):
                return self
            def first(self):
                return None
        class DummyModel:
            objects = DummyQS()
        with patch("web.views_auth.OAuthToken", DummyModel):
            resp = self.client.get("/")
            self.assertEqual(resp.status_code, 302)
            self.assertIn("/auth/login/", resp["Location"])

    def test_show_token_none(self):
        class DummyQS:
            def order_by(self, *args, **kwargs):
                return self
            def first(self):
                return None
        class DummyModel:
            objects = DummyQS()
        with patch("web.views_auth.OAuthToken", DummyModel):
            resp = self.client.get("/token/")
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.content.decode(), "No token stored")

    def test_login_start_redirect(self):
        resp = self.client.get("/auth/login/")
        self.assertEqual(resp.status_code, 302)
        loc = resp["Location"]
        self.assertIn("authentication/v2/authorize", loc)
        self.assertIn("client_id=cid", loc)
        self.assertIn("redirect_uri=http%3A%2F%2Ftestserver%2Fauth%2Fcallback%2F", loc)

    @override_settings(MIDDLEWARE=[
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    ])
    def test_report_csv_success(self):
        class FakeIA:
            def __init__(self, client): pass
            def collect_rows(self):
                return [IssueRow(
                    project_id="p1",
                    project_name="DEV TASK 1 Project",
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
                )]
        with patch("web.views_report.IssueAggregator", FakeIA):
            resp = self.client.get("/report.csv")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("project id,project name,document id", resp.content.decode("utf-8"))

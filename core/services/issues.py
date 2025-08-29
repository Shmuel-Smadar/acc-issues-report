import requests
from .auth import AuthSession


class IssuesService:
    def __init__(self, auth: AuthSession):
        self.auth = auth
        self.base = self.auth.base

    def list_issues(self, issues_project_id: str) -> list[dict]:
        out: list[dict] = []
        limit = 100
        offset = 0
        headers = self.auth.headers()
        while True:
            url = f"{self.base}/construction/issues/v1/projects/{issues_project_id}/issues?limit={limit}&offset={offset}"
            r = requests.get(url, headers=headers, timeout=30)
            if r.status_code != 200:
                raise RuntimeError(f"Failed to list issues: {r.text}")
            j = r.json()
            out.extend(j.get("results", []))
            pag = j.get("pagination") or {}
            total = int(pag.get("totalResults", len(out)))
            offset += limit
            if offset >= total or not j.get("results"):
                break
        return out

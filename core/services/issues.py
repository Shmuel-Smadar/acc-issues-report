import logging
from .auth import AuthSession

class IssuesService:
    def __init__(self, auth: AuthSession):
        self.auth = auth
        self.base = self.auth.base
        self.logger = logging.getLogger("app")

    def list_issues(self, issues_project_id: str) -> list[dict]:
        out: list[dict] = []
        limit = 100
        offset = 0
        while True:
            url = f"{self.base}/construction/issues/v1/projects/{issues_project_id}/issues?limit={limit}&offset={offset}"
            self.logger.info("event=issues.page_fetch url=%s limit=%s offset=%s", url, limit, offset)
            r = self.auth.get(url, timeout=30)
            if r.status_code != 200:
                self.logger.warning("event=issues.page_fetch result=fail status=%s", r.status_code)
                raise RuntimeError(f"Failed to list issues: {r.text}")
            j = r.json()
            batch = j.get("results", [])
            out.extend(batch)
            pag = j.get("pagination") or {}
            total = int(pag.get("totalResults", len(out)))
            self.logger.info("event=issues.page_fetch result=ok got=%s total=%s", len(batch), total)
            offset += limit
            if offset >= total or not batch:
                break
        self.logger.info("event=issues.list total=%s", len(out))
        return out

    def issue_types_map(self, issues_project_id: str) -> tuple[dict, dict]:
        url = f"{self.base}/construction/issues/v1/projects/{issues_project_id}/issue-types?include=subtypes"
        self.logger.info("event=issues.types_fetch url=%s", url)
        r = self.auth.get(url, timeout=30)
        if r.status_code != 200:
            self.logger.warning("event=issues.types_fetch result=fail status=%s", r.status_code)
            raise RuntimeError(f"Failed to get issue types: {r.text}")
        j = r.json()
        type_map: dict[str, str] = {}
        subtype_map: dict[str, str] = {}
        for t in j.get("results", []):
            tid = t.get("id")
            tname = t.get("name")
            if tid and tname:
                type_map[tid] = tname
            for st in (t.get("subtypes") or []):
                sid = st.get("id")
                sname = st.get("name")
                if sid and sname:
                    subtype_map[sid] = sname
        self.logger.info("event=issues.types_fetch result=ok types=%s subtypes=%s", len(type_map), len(subtype_map))
        return type_map, subtype_map

    def get_comments(self, issues_project_id: str, issue_id: str) -> list[dict]:
        url = f"{self.base}/construction/issues/v1/projects/{issues_project_id}/issues/{issue_id}/comments"
        r = self.auth.get(url, timeout=30)
        if r.status_code != 200:
            return []
        return r.json().get("results", [])

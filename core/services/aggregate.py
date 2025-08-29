from django.conf import settings
from core.dto import Document, IssueRow
from .utils import norm_date, extract_viewable_guid, with_viewable_param, clean_comment_text


class ProjectService:
    def __init__(self, client):
        self.client = client

    def list_and_print_projects(self):
        projects = self.client.list_projects_admin()
        if not projects:
            raise RuntimeError("No projects found")
        names = [p.get("name") for p in projects]
        if settings.TARGET_PROJECT_NAME in names:
            proj = next(p for p in projects if p.get("name") == settings.TARGET_PROJECT_NAME)
        else:
            raise RuntimeError(f"Project '{settings.TARGET_PROJECT_NAME}' not found. Available projects: {names}")
        return names


class IssueAggregator:
    def __init__(self, client):
        self.client = client

    def _issues_project_id(self, dm_project_id: str) -> str:
        return dm_project_id[2:] if dm_project_id.startswith("b.") else dm_project_id

    def collect_rows(self) -> list[IssueRow]:
        dm_project_id = self.client.get_project_id_by_name(settings.TARGET_PROJECT_NAME)
        issues_project_id = self._issues_project_id(dm_project_id)
        type_map, subtype_map = self.client.issues.issue_types_map(issues_project_id)
        issues = self.client.list_issues(issues_project_id)
        info_cache: dict[str, Document | None] = {}
        rows: list[IssueRow] = []
        for iss in issues:
            urns = set()
            for p in iss.get("placements", []) or []:
                u = p.get("lineageUrn")
                if u:
                    urns.add(u)
            for d in iss.get("linkedDocuments", []) or []:
                u = d.get("urn")
                if u:
                    urns.add(u)
            comments = self.client.issues.get_comments(issues_project_id, iss.get("id"))
            if comments:
                comments_sorted = sorted(comments, key=lambda c: c.get("createdAt") or "")
                bodies = [clean_comment_text(c.get("body")) for c in comments_sorted]
                bodies = [b for b in bodies if b]
                all_comments = ", ".join(bodies)
            else:
                all_comments = ""
            guid = extract_viewable_guid(iss)
            for u in sorted(urns):
                if u not in info_cache:
                    try:
                        info_cache[u] = self.client.get_item_info(dm_project_id, u)
                    except Exception:
                        info_cache[u] = None
                info = info_cache[u]
                if not info or not info.is_pdf:
                    continue
                deep_link = with_viewable_param(info.web_link, guid)
                rows.append(
                    IssueRow(
                        project_id=dm_project_id,
                        project_name=settings.TARGET_PROJECT_NAME,
                        document_id=u,
                        document_name=info.name,
                        document_path=info.path,
                        web_link=deep_link,
                        issue_id=iss.get("id", ""),
                        issue_type=type_map.get(iss.get("issueTypeId", ""), ""),
                        issue_sub_type=subtype_map.get(iss.get("issueSubtypeId", ""), ""),
                        issue_status=iss.get("status", ""),
                        issue_due_date=norm_date(iss.get("dueDate")),
                        issue_start_date=norm_date(iss.get("startDate")),
                        issue_title=(iss.get("title") or "") or "",
                        issue_description=(iss.get("description") or "").strip(),
                        issue_comments=all_comments,
                    )
                )
        return rows

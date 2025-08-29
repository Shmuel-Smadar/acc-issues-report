from django.http import JsonResponse, HttpResponseBadRequest
from django.conf import settings
from core.services.acc_client import ACCClient


def report(request):
    client = ACCClient()
    try:
        dm_project_id = client.get_project_id_by_name(settings.TARGET_PROJECT_NAME)
    except Exception as e:
        return HttpResponseBadRequest(str(e))
    issues_project_id = dm_project_id[2:] if dm_project_id.startswith("b.") else dm_project_id
    try:
        issues = client.list_issues(issues_project_id)
    except Exception as e:
        return HttpResponseBadRequest(str(e))
    all_issues = []
    for i in issues:
        all_issues.append({
            "id": i.get("id"),
            "title": i.get("title"),
            "status": i.get("status"),
            "dueDate": i.get("dueDate"),
            "startDate": i.get("startDate"),
            "placements": len(i.get("placements", [])),
            "linkedDocuments": len(i.get("linkedDocuments", [])),
        })
    info_cache = {}
    pdf_issues = []
    for i in issues:
        urns = set()
        for p in i.get("placements", []):
            u = p.get("lineageUrn")
            if u:
                urns.add(u)
        for d in i.get("linkedDocuments", []):
            u = d.get("urn")
            if u:
                urns.add(u)
        for u in urns:
            if u not in info_cache:
                try:
                    info_cache[u] = client.get_item_info(dm_project_id, u)
                except Exception:
                    info_cache[u] = None
            info = info_cache[u]
            if not info or not info.get("is_pdf"):
                continue
            pdf_issues.append({
                "project_id": dm_project_id,
                "project_name": settings.TARGET_PROJECT_NAME,
                "document_id": u,
                "document_name": info.get("name") or "",
                "document_path": info.get("path") or "",
                "web_link": info.get("webView") or "",
                "issue_id": i.get("id"),
                "issue_type_id": i.get("issueTypeId"),
                "issue_sub_type_id": i.get("issueSubtypeId"),
                "issue_status": i.get("status"),
                "issue_due_date": i.get("dueDate"),
                "issue_start_date": i.get("startDate"),
                "issue_title": i.get("title"),
                "issue_description": i.get("description"),
            })
    return JsonResponse({"all_issues": all_issues, "pdf_issues": pdf_issues})

import time, urllib.parse, requests
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse, HttpResponseBadRequest
from django.conf import settings
from core.models import OAuthToken
from core.services.acc_client import ACCClient

def index(request):
    tok = OAuthToken.objects.order_by("-updated_at").first()
    authed = bool(tok and tok.expires_at > int(time.time()))
    return JsonResponse({
        "authenticated": authed,
        "login_url": "/auth/login/"
    })

def login_start(request):
    qs = urllib.parse.urlencode({
        "response_type": "code",
        "client_id": settings.FORGE_CLIENT_ID,
        "redirect_uri": settings.FORGE_CALLBACK_URL,
        "scope": settings.FORGE_SCOPE,
    })
    return HttpResponseRedirect(f"{settings.FORGE_BASE_URL}/authentication/v2/authorize?{qs}")

def oauth_callback(request):
    code = request.GET.get("code")
    if not code:
        return HttpResponseBadRequest("missing code")
    r = requests.post(
        f"{settings.FORGE_BASE_URL}/authentication/v2/token",
        data={
            "grant_type": "authorization_code",
            "client_id": settings.FORGE_CLIENT_ID,
            "client_secret": settings.FORGE_CLIENT_SECRET,
            "code": code,
            "redirect_uri": settings.FORGE_CALLBACK_URL,
        },
        timeout=30
    )
    if r.status_code != 200:
        return HttpResponseBadRequest(r.text)
    p = r.json()
    OAuthToken.objects.all().delete()
    OAuthToken.objects.create(
        access_token=p["access_token"],
        refresh_token=p.get("refresh_token", ""),
        expires_at=int(time.time()) + int(p.get("expires_in", 0))
    )
    return HttpResponseRedirect("/")

def list_files(request):
    client = ACCClient()
    project_id = client.get_project_id_by_name(settings.TARGET_PROJECT_NAME)
    if not project_id:
        return HttpResponseBadRequest("ACC_PROJECT_ID not set")
    files = client.list_all_files(project_id)
    return JsonResponse({"files": files})

def show_token(request):
    tok = OAuthToken.objects.order_by("-updated_at").first()
    if not tok:
        return HttpResponse("No token stored")
    return HttpResponse(tok.access_token, content_type="text/plain")

def download_by_project_name(request):
    client = ACCClient()
    try:
        url = client.signed_url_for_first_pdf_in_project("DEV TASK 1 Project")
    except Exception as e:
        return HttpResponseBadRequest(str(e))
    return HttpResponseRedirect(url)

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
            if not info or not info.is_pdf:
                continue
            pdf_issues.append({
                "project_id": dm_project_id,
                "project_name": settings.TARGET_PROJECT_NAME,
                "document_id": u,
                "document_name": info.name or "",
                "document_path": info.path or "",
                "web_link": info.web_link or "",
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

import time, urllib.parse, requests
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse, HttpResponseBadRequest
from django.conf import settings
from core.models import OAuthToken
from core.services.acc_client import ACCClient
from core.services.aggregate import ProjectService


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
    project_id = settings.ACC_PROJECT_ID
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

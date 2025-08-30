import time
import urllib.parse
import logging
import requests
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse, HttpResponseBadRequest
from django.conf import settings
from core.models import OAuthToken

logger = logging.getLogger("app")

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
    url = f"{settings.FORGE_BASE_URL}/authentication/v2/authorize?{qs}"
    logger.info("event=auth.login_start url=%s", url)
    return HttpResponseRedirect(url)

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
        logger.warning("event=auth.callback_exchange result=fail status=%s", r.status_code)
        return HttpResponseBadRequest(r.text)
    p = r.json()
    OAuthToken.objects.all().delete()
    OAuthToken.objects.create(
        access_token=p["access_token"],
        refresh_token=p.get("refresh_token", ""),
        expires_at=int(time.time()) + int(p.get("expires_in", 0))
    )
    logger.info("event=auth.callback_exchange result=success")
    return HttpResponseRedirect("/")

def show_token(request):
    tok = OAuthToken.objects.order_by("-updated_at").first()
    if not tok:
        return HttpResponse("No token stored")
    return HttpResponse(tok.access_token, content_type="text/plain")

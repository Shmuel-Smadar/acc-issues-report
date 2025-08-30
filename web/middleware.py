import logging
from django.http import HttpResponseRedirect
from core.services.auth import AuthSession, AuthExpired

class EnsureForgeAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger("app")

    def __call__(self, request):
        path = request.path or ""
        if path.startswith("/auth/") or path.startswith("/admin/") or path == "/token/":
            return self.get_response(request)
        try:
            AuthSession().ensure_token()
        except Exception:
            self.logger.info("event=auth.redirect reason=no_token path=%s", path)
            return HttpResponseRedirect("/auth/login/")
        try:
            return self.get_response(request)
        except AuthExpired:
            self.logger.info("event=auth.redirect reason=expired path=%s", path)
            return HttpResponseRedirect("/auth/login/")

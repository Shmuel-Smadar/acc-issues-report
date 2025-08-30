from django.http import HttpResponseRedirect
from core.services.auth import AuthSession, AuthExpired


class EnsureForgeAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path or ""
        if path.startswith("/auth/") or path.startswith("/admin/") or path == "/token/":
            return self.get_response(request)
        try:
            AuthSession().ensure_token()
        except Exception:
            return HttpResponseRedirect("/auth/login/")
        try:
            return self.get_response(request)
        except AuthExpired:
            return HttpResponseRedirect("/auth/login/")

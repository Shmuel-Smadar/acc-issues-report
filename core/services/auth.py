import time
import requests
from django.conf import settings
from core.models import OAuthToken
from .http_retry import request_with_retries


class AuthExpired(Exception):
    pass


class AuthSession:
    def __init__(self):
        self.base = settings.FORGE_BASE_URL.rstrip("/")
        self.max_retries = getattr(settings, "FORGE_RETRY_MAX_RETRIES", 5)
        self.backoff_base = getattr(settings, "FORGE_RETRY_BACKOFF_BASE", 0.5)
        self.backoff_max = getattr(settings, "FORGE_RETRY_BACKOFF_MAX", 10.0)

    def _row(self) -> OAuthToken | None:
        return OAuthToken.objects.order_by("-updated_at").first()

    def ensure_token(self) -> str:
        row = self._row()
        if not row:
            raise RuntimeError("Not authenticated")
        if row.expires_at - 60 <= int(time.time()):
            self._refresh(row)
        return row.access_token

    def headers(self) -> dict:
        return {"Authorization": f"Bearer {self.ensure_token()}"}

    def _clear_tokens(self):
        OAuthToken.objects.all().delete()

    def _refresh(self, row: OAuthToken):
        url = f"{self.base}/authentication/v2/token"
        data = {
            "grant_type": "refresh_token",
            "client_id": settings.FORGE_CLIENT_ID,
            "client_secret": settings.FORGE_CLIENT_SECRET,
            "refresh_token": row.refresh_token,
            "redirect_uri": settings.FORGE_CALLBACK_URL,
        }
        r = requests.post(url, data=data, timeout=30)
        if r.status_code != 200:
            self._clear_tokens()
            raise RuntimeError("Token refresh failed")
        p = r.json()
        row.access_token = p["access_token"]
        row.refresh_token = p.get("refresh_token", row.refresh_token)
        row.expires_at = int(time.time()) + int(p.get("expires_in", 0))
        row.save()

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        hdrs_in = kwargs.pop("headers", {}) or {}
        timeout = kwargs.pop("timeout", 30)

        def make_request(h):
            merged = {}
            merged.update(h)
            merged.update(hdrs_in)
            return requests.request(method, url, headers=merged, timeout=timeout, **kwargs)

        def get_headers():
            return self.headers()

        def refresh_on_401():
            row = self._row()
            if not row:
                self._clear_tokens()
                raise AuthExpired("Access token invalid or expired")
            try:
                self._refresh(row)
            except Exception:
                self._clear_tokens()
                raise AuthExpired("Access token invalid or expired")

        resp = request_with_retries(
            make_request,
            get_headers,
            refresh_on_401,
            max_retries=self.max_retries,
            backoff_base=self.backoff_base,
            backoff_max=self.backoff_max,
        )
        if resp.status_code == 401:
            self._clear_tokens()
            raise AuthExpired("Access token invalid or expired")
        return resp

    def get(self, url: str, **kwargs) -> requests.Response:
        return self._request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        return self._request("POST", url, **kwargs)

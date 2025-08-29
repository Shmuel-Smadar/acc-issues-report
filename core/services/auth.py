import time
import requests
from django.conf import settings
from core.models import OAuthToken


class AuthSession:
    def __init__(self):
        self.base = settings.FORGE_BASE_URL.rstrip("/")

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
            raise RuntimeError("Token refresh failed")
        p = r.json()
        row.access_token = p["access_token"]
        row.refresh_token = p.get("refresh_token", row.refresh_token)
        row.expires_at = int(time.time()) + int(p.get("expires_in", 0))
        row.save()

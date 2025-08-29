import time
import urllib.parse
from typing import Dict, Optional, Tuple
import requests
from django.conf import settings
from core.models import OAuthToken


class ACCClient:
    def __init__(self):
        self.base = settings.FORGE_BASE_URL.rstrip("/")

    def _row(self) -> Optional[OAuthToken]:
        return OAuthToken.objects.order_by("-updated_at").first()

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self._ensure_token()}"}

    def _ensure_token(self) -> str:
        row = self._row()
        if not row:
            raise RuntimeError("Not authenticated")
        if row.expires_at - 60 <= int(time.time()):
            self._refresh(row)
        return row.access_token

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

    def _hub_id(self) -> str:
        if not settings.ACC_ACCOUNT_ID:
            raise RuntimeError("ACC_ACCOUNT_ID not set in settings")
        return f"b.{settings.ACC_ACCOUNT_ID}"

    def get_project_id_by_name(self, project_name: str) -> str:
        url = f"{self.base}/project/v1/hubs/{self._hub_id()}/projects"
        r = requests.get(url, headers=self._headers(), timeout=30)
        if r.status_code != 200:
            raise RuntimeError(f"Failed to list projects: {r.text}")
        data = r.json().get("data", [])
        for p in data:
            if (p.get("attributes") or {}).get("name") == project_name:
                return p.get("id")
        raise RuntimeError(f"Project '{project_name}' not found")

    def get_first_top_folder_id(self, project_id: str) -> str:
        url = f"{self.base}/project/v1/hubs/{self._hub_id()}/projects/{project_id}/topFolders"
        r = requests.get(url, headers=self._headers(), timeout=30)
        if r.status_code != 200:
            raise RuntimeError(f"Failed to get top folders: {r.text}")
        arr = r.json().get("data", [])
        if not arr:
            raise RuntimeError("No top folders found")
        return arr[0].get("id")

    def _folder_contents(self, project_id: str, folder_id: str) -> dict:
        enc_folder = urllib.parse.quote(folder_id, safe="")
        url = f"{self.base}/data/v1/projects/{project_id}/folders/{enc_folder}/contents"
        print(project_id)
        r = requests.get(url, headers=self._headers(), timeout=30)
        if r.status_code != 200:
            raise RuntimeError(f"Failed to list folder contents: {r.text}")
        return r.json()

    def _first_pdf_storage_from_contents(self, contents: dict) -> Tuple[str, str, str]:
        included = contents.get("included", [])
        for v in included:
            if v.get("type") != "versions":
                continue
            attrs = v.get("attributes") or {}
            name = attrs.get("name") or attrs.get("displayName") or ""
            file_type = attrs.get("fileType") or ""
            if file_type.lower() == "pdf" or name.lower().endswith(".pdf"):
                rel = v.get("relationships", {})
                storage = rel.get("storage")
                if not storage:
                    rel_links = (v.get("links") or {}).get("relationships") or {}
                    storage = rel_links.get("storage")
                if not storage:
                    continue
                data = storage.get("data") or {}
                storage_id = data.get("id") or ""
                prefix = "urn:adsk.objects:os.object:"
                if not storage_id.startswith(prefix):
                    continue
                rest = storage_id[len(prefix):]
                parts = rest.split("/", 1)
                if len(parts) != 2:
                    continue
                return parts[0], parts[1], name
        raise RuntimeError("No PDF found in folder")

    def get_first_pdf_storage(self, project_id: str, folder_id: str) -> Tuple[str, str, str]:
        contents = self._folder_contents(project_id, folder_id)
        return self._first_pdf_storage_from_contents(contents)

    def signed_s3_url(self, bucket_key: str, object_key: str) -> str:
        url = f"{self.base}/oss/v2/buckets/{bucket_key}/objects/{object_key}/signeds3download"
        r = requests.get(url, headers=self._headers(), timeout=30)
        if r.status_code != 200:
            raise RuntimeError(f"Failed to get signed URL: {r.text}")
        return r.json().get("url")

    def signed_url_for_first_pdf_in_project(self, project_name: str) -> str:
        project_id = self.get_project_id_by_name(project_name)
        folder_id = self.get_first_top_folder_id(project_id)
        bucket, obj, _ = self.get_first_pdf_storage(project_id, folder_id)
        return self.signed_s3_url(bucket, obj)

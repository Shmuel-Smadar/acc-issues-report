import requests
from django.conf import settings
from .auth import AuthSession


class ProjectsService:
    def __init__(self, auth: AuthSession):
        self.auth = auth
        self.base = self.auth.base

    def _hub_id(self) -> str:
        if not settings.ACC_ACCOUNT_ID:
            raise RuntimeError("ACC_ACCOUNT_ID not set in settings")
        return f"b.{settings.ACC_ACCOUNT_ID}"

    def get_project_id_by_name(self, project_name: str) -> str:
        url = f"{self.base}/project/v1/hubs/{self._hub_id()}/projects"
        r = requests.get(url, headers=self.auth.headers(), timeout=30)
        if r.status_code != 200:
            raise RuntimeError(f"Failed to list projects: {r.text}")
        data = r.json().get("data", [])
        for p in data:
            if (p.get("attributes") or {}).get("name") == project_name:
                return p.get("id")
        raise RuntimeError(f"Project '{project_name}' not found")

    def get_first_top_folder_id(self, project_id: str) -> str:
        url = f"{self.base}/project/v1/hubs/{self._hub_id()}/projects/{project_id}/topFolders"
        r = requests.get(url, headers=self.auth.headers(), timeout=30)
        if r.status_code != 200:
            raise RuntimeError(f"Failed to get top folders: {r.text}")
        arr = r.json().get("data", [])
        if not arr:
            raise RuntimeError("No top folders found")
        return arr[0].get("id")

    def get_top_folder_ids(self, project_id: str) -> list[str]:
        url = f"{self.base}/project/v1/hubs/{self._hub_id()}/projects/{project_id}/topFolders"
        r = requests.get(url, headers=self.auth.headers(), timeout=30)
        if r.status_code != 200:
            raise RuntimeError(f"Failed to get top folders: {r.text}")
        return [d.get("id") for d in r.json().get("data", []) if d.get("id")]

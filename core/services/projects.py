import logging
from django.conf import settings
from .auth import AuthSession

class ProjectsService:
    def __init__(self, auth: AuthSession):
        self.auth = auth
        self.base = self.auth.base
        self.logger = logging.getLogger("app")

    def _hub_id(self) -> str:
        if not settings.ACC_ACCOUNT_ID:
            raise RuntimeError("ACC_ACCOUNT_ID not set in settings")
        return f"b.{settings.ACC_ACCOUNT_ID}"

    def get_project_id_by_name(self, project_name: str) -> str:
        url = f"{self.base}/project/v1/hubs/{self._hub_id()}/projects"
        self.logger.info("event=projects.list url=%s", url)
        r = self.auth.get(url, timeout=30)
        if r.status_code != 200:
            self.logger.warning("event=projects.list result=fail status=%s", r.status_code)
            raise RuntimeError(f"Failed to list projects: {r.text}")
        data = r.json().get("data", [])
        self.logger.info("event=projects.list result=ok count=%s", len(data))
        for p in data:
            if (p.get("attributes") or {}).get("name") == project_name:
                pid = p.get("id")
                self.logger.info("event=projects.match result=found id=%s name=%s", pid, project_name)
                return pid
        self.logger.info("event=projects.match result=not_found name=%s", project_name)
        raise RuntimeError(f"Project '{project_name}' not found")

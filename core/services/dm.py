import urllib.parse
from collections import deque
from typing import Tuple, Optional, List
import logging
from .auth import AuthSession
from .projects import ProjectsService
from core.dto import Document

class DataManagementService:
    def __init__(self, auth: AuthSession, projects: ProjectsService):
        self.auth = auth
        self.projects = projects
        self.base = self.auth.base
        self.logger = logging.getLogger("app")

    def _folder_contents(self, project_id: str, folder_id: str) -> dict:
        enc_folder = urllib.parse.quote(folder_id, safe="")
        url = f"{self.base}/data/v1/projects/{project_id}/folders/{enc_folder}/contents"
        r = self.auth.get(url, timeout=30)
        if r.status_code != 200:
            raise RuntimeError(f"Failed to list folder contents: {r.text}")
        return r.json()

    def _folder_contents_all(self, project_id: str, folder_id: str) -> dict:
        enc_folder = urllib.parse.quote(folder_id, safe="")
        url = f"{self.base}/data/v1/projects/{project_id}/folders/{enc_folder}/contents"
        data_accum: List[dict] = []
        included_accum: List[dict] = []
        while url:
            self.logger.info("event=dm.folder_contents url=%s", url)
            r = self.auth.get(url, timeout=30)
            if r.status_code != 200:
                raise RuntimeError(f"Failed to list folder contents: {r.text}")
            j = r.json()
            data_accum.extend(j.get("data", []))
            included = j.get("included", [])
            if included:
                included_accum.extend(included)
            links = j.get("links") or {}
            next_link = links.get("next")
            if isinstance(next_link, dict):
                url = next_link.get("href") or next_link.get("url") or ""
            elif isinstance(next_link, str):
                url = next_link
            else:
                url = ""
        self.logger.info("event=dm.folder_contents result=ok data=%s included=%s", len(data_accum), len(included_accum))
        return {"data": data_accum, "included": included_accum}

    def signed_s3_url(self, bucket_key: str, object_key: str) -> str:
        url = f"{self.base}/oss/v2/buckets/{bucket_key}/objects/{object_key}/signeds3download"
        self.logger.info("event=dm.signed_url bucket=%s object=%s", bucket_key, object_key)
        r = self.auth.get(url, timeout=30)
        if r.status_code != 200:
            raise RuntimeError(f"Failed to get signed URL: {r.text}")
        return r.json().get("url")

    def item_tip(self, dm_project_id: str, item_urn: str) -> dict:
        enc_item = urllib.parse.quote(item_urn, safe="")
        url = f"{self.base}/data/v1/projects/{dm_project_id}/items/{enc_item}/tip"
        self.logger.info("event=dm.item_tip urn=%s", item_urn)
        r = self.auth.get(url, timeout=30)
        if r.status_code != 200:
            raise RuntimeError(f"Failed to get item tip: {r.text}")
        return r.json().get("data") or {}

    def get_item_parent_folder_id(self, dm_project_id: str, item_urn: str) -> Optional[str]:
        enc_item = urllib.parse.quote(item_urn, safe="")
        url = f"{self.base}/data/v1/projects/{dm_project_id}/items/{enc_item}/parent"
        r = self.auth.get(url, timeout=30)
        if r.status_code != 200:
            return None
        data = r.json().get("data") or {}
        return data.get("id")

    def get_folder(self, dm_project_id: str, folder_id: str) -> dict:
        enc_folder = urllib.parse.quote(folder_id, safe="")
        url = f"{self.base}/data/v1/projects/{dm_project_id}/folders/{enc_folder}"
        r = self.auth.get(url, timeout=30)
        if r.status_code != 200:
            raise RuntimeError(f"Failed to get folder: {r.text}")
        return r.json().get("data") or {}

    def get_folder_parent_id(self, dm_project_id: str, folder_id: str) -> Optional[str]:
        enc_folder = urllib.parse.quote(folder_id, safe="")
        url = f"{self.base}/data/v1/projects/{dm_project_id}/folders/{enc_folder}/parent"
        r = self.auth.get(url, timeout=30)
        if r.status_code != 200:
            return None
        data = r.json().get("data") or {}
        return data.get("id")

    def build_folder_path(self, dm_project_id: str, start_folder_id: Optional[str]) -> str:
        if not start_folder_id:
            return ""
        names: List[str] = []
        current = start_folder_id
        visited = set()
        while current and current not in visited:
            visited.add(current)
            f = self.get_folder(dm_project_id, current)
            attrs = f.get("attributes") or {}
            name = attrs.get("displayName") or attrs.get("name") or ""
            if name:
                names.append(name)
            current = self.get_folder_parent_id(dm_project_id, current)
        names.reverse()
        return "/".join(names)

    def get_item_info(self, dm_project_id: str, item_urn: str) -> Document:
        tip = self.item_tip(dm_project_id, item_urn)
        attrs = tip.get("attributes") or {}
        links = tip.get("links") or {}
        web = links.get("webView", {}) if isinstance(links, dict) else {}
        web_href = web.get("href") if isinstance(web, dict) else ""
        name = attrs.get("name") or attrs.get("displayName") or ""
        file_type = (attrs.get("fileType") or "").lower()
        is_pdf = file_type == "pdf" or name.lower().endswith(".pdf")
        folder_id = self.get_item_parent_folder_id(dm_project_id, item_urn)
        path = self.build_folder_path(dm_project_id, folder_id)
        self.logger.info("event=dm.item_info urn=%s name=%s pdf=%s path_len=%s", item_urn, name, is_pdf, len(path))
        return Document(id=item_urn, name=name, path=path, web_link=web_href, is_pdf=is_pdf)

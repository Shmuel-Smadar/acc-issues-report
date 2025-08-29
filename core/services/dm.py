import urllib.parse
from collections import deque
from typing import Tuple, Optional, List
import requests
from .auth import AuthSession
from .projects import ProjectsService
from core.dto import Document

class DataManagementService:
    def __init__(self, auth: AuthSession, projects: ProjectsService):
        self.auth = auth
        self.projects = projects
        self.base = self.auth.base

    def _folder_contents(self, project_id: str, folder_id: str) -> dict:
        enc_folder = urllib.parse.quote(folder_id, safe="")
        url = f"{self.base}/data/v1/projects/{project_id}/folders/{enc_folder}/contents"
        r = requests.get(url, headers=self.auth.headers(), timeout=30)
        if r.status_code != 200:
            raise RuntimeError(f"Failed to list folder contents: {r.text}")
        return r.json()

    def _folder_contents_all(self, project_id: str, folder_id: str) -> dict:
        enc_folder = urllib.parse.quote(folder_id, safe="")
        url = f"{self.base}/data/v1/projects/{project_id}/folders/{enc_folder}/contents"
        data_accum: List[dict] = []
        included_accum: List[dict] = []
        headers = self.auth.headers()
        while url:
            r = requests.get(url, headers=headers, timeout=30)
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
        return {"data": data_accum, "included": included_accum}

    def _first_pdf_storage_from_contents(self, contents: dict) -> Tuple[str, str, str]:
        included = contents.get("included", [])
        for v in included:
            if v.get("type") != "versions":
                continue
            attrs = v.get("attributes") or {}
            name = attrs.get("name") or attrs.get("displayName") or ""
            file_type = attrs.get("fileType") or ""
            if file_type.lower() == "pdf" or name.lower().endswith(".pdf"):
                rel = v.get("relationships", {}) or {}
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
        r = requests.get(url, headers=self.auth.headers(), timeout=30)
        if r.status_code != 200:
            raise RuntimeError(f"Failed to get signed URL: {r.text}")
        return r.json().get("url")

    def _extract_pdf_names_from_contents(self, contents: dict) -> List[str]:
        names: List[str] = []
        included = contents.get("included", []) or []
        for v in included:
            if v.get("type") != "versions":
                continue
            attrs = v.get("attributes") or {}
            name = attrs.get("name") or attrs.get("displayName") or ""
            file_type = (attrs.get("fileType") or "").lower()
            if file_type == "pdf" or name.lower().endswith(".pdf"):
                if name:
                    names.append(name)
        return names

    def list_all_files(self, project_id: str) -> List[str]:
        pdf_names = set()
        queue = deque(self.projects.get_top_folder_ids(project_id))
        seen = set()
        while queue:
            folder_id = queue.popleft()
            if folder_id in seen:
                continue
            seen.add(folder_id)
            contents = self._folder_contents_all(project_id, folder_id)
            for name in self._extract_pdf_names_from_contents(contents):
                pdf_names.add(name)
            for d in contents.get("data", []):
                if d.get("type") == "folders":
                    sub_id = d.get("id")
                    if sub_id and sub_id not in seen:
                        queue.append(sub_id)
        return sorted(pdf_names)

    def item_tip(self, dm_project_id: str, item_urn: str) -> dict:
        enc_item = urllib.parse.quote(item_urn, safe="")
        url = f"{self.base}/data/v1/projects/{dm_project_id}/items/{enc_item}/tip"
        r = requests.get(url, headers=self.auth.headers(), timeout=30)
        if r.status_code != 200:
            raise RuntimeError(f"Failed to get item tip: {r.text}")
        return r.json().get("data") or {}

    def get_item_parent_folder_id(self, dm_project_id: str, item_urn: str) -> Optional[str]:
        enc_item = urllib.parse.quote(item_urn, safe="")
        url = f"{self.base}/data/v1/projects/{dm_project_id}/items/{enc_item}/parent"
        r = requests.get(url, headers=self.auth.headers(), timeout=30)
        if r.status_code != 200:
            return None
        data = r.json().get("data") or {}
        return data.get("id")

    def get_folder(self, dm_project_id: str, folder_id: str) -> dict:
        enc_folder = urllib.parse.quote(folder_id, safe="")
        url = f"{self.base}/data/v1/projects/{dm_project_id}/folders/{enc_folder}"
        r = requests.get(url, headers=self.auth.headers(), timeout=30)
        if r.status_code != 200:
            raise RuntimeError(f"Failed to get folder: {r.text}")
        return r.json().get("data") or {}

    def get_folder_parent_id(self, dm_project_id: str, folder_id: str) -> Optional[str]:
        enc_folder = urllib.parse.quote(folder_id, safe="")
        url = f"{self.base}/data/v1/projects/{dm_project_id}/folders/{enc_folder}/parent"
        r = requests.get(url, headers=self.auth.headers(), timeout=30)
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
        return Document(id=item_urn, name=name, path=path, web_link=web_href, is_pdf=is_pdf)

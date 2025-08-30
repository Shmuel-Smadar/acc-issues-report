from typing import Tuple, Optional, List
from .auth import AuthSession
from .projects import ProjectsService
from .dm import DataManagementService
from .issues import IssuesService
from core.dto import Document

class ACCClient:
    def __init__(self):
        self.auth = AuthSession()
        self.projects = ProjectsService(self.auth)
        self.dm = DataManagementService(self.auth, self.projects)
        self.issues = IssuesService(self.auth)

    def get_project_id_by_name(self, project_name: str) -> str:
        return self.projects.get_project_id_by_name(project_name)

    def get_first_top_folder_id(self, project_id: str) -> str:
        return self.projects.get_first_top_folder_id(project_id)

    def get_top_folder_ids(self, project_id: str) -> List[str]:
        return self.projects.get_top_folder_ids(project_id)

    def signed_s3_url(self, bucket_key: str, object_key: str) -> str:
        return self.dm.signed_s3_url(bucket_key, object_key)
    def list_issues(self, issues_project_id: str) -> List[dict]:
        return self.issues.list_issues(issues_project_id)

    def item_tip(self, dm_project_id: str, item_urn: str) -> dict:
        return self.dm.item_tip(dm_project_id, item_urn)

    def get_item_parent_folder_id(self, dm_project_id: str, item_urn: str) -> Optional[str]:
        return self.dm.get_item_parent_folder_id(dm_project_id, item_urn)

    def get_folder(self, dm_project_id: str, folder_id: str) -> dict:
        return self.dm.get_folder(dm_project_id, folder_id)

    def get_folder_parent_id(self, dm_project_id: str, folder_id: str) -> Optional[str]:
        return self.dm.get_folder_parent_id(dm_project_id, folder_id)

    def build_folder_path(self, dm_project_id: str, start_folder_id: Optional[str]) -> str:
        return self.dm.build_folder_path(dm_project_id, start_folder_id)

    def get_item_info(self, dm_project_id: str, item_urn: str) -> Document:
        return self.dm.get_item_info(dm_project_id, item_urn)

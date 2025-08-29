from dataclasses import dataclass
from typing import Optional, Mapping

@dataclass(frozen=True)
class Project:
    id: str
    name: str

@dataclass(frozen=True)
class Document:
    id: str
    name: str
    path: str
    web_link: str = ""
    is_pdf: bool = False

@dataclass(frozen=True)
class IssueRow:
    project_id: str
    project_name: str
    document_id: str
    document_name: str
    document_path: str
    web_link: str
    issue_id: str
    issue_type: str
    issue_sub_type: str
    issue_status: str
    issue_due_date: Optional[str]
    issue_start_date: Optional[str]
    issue_title: str
    issue_description: str
    issue_comments: str

    def to_csv_row(self) -> Mapping[str, str]:
        return {
            "project id": self.project_id,
            "project name": self.project_name,
            "document id": self.document_id,
            "document name": self.document_name,
            "document path": self.document_path,
            "link to the document page the issue located in": self.web_link,
            "issue id": self.issue_id,
            "issue type": self.issue_type,
            "issue sub type": self.issue_sub_type,
            "issue status": self.issue_status,
            "issue due date": self.issue_due_date or "",
            "issue start date": self.issue_start_date or "",
            "issue title": self.issue_title,
            "issue description": self.issue_description,
            "issue comments": self.issue_comments,
        }

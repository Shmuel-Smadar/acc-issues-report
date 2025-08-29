import datetime as dt
import urllib.parse
from typing import Optional


def norm_date(s: Optional[str]) -> str:
    if not s:
        return ""
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).date().isoformat()
    except Exception:
        return s


def extract_viewable_guid(issue: dict) -> Optional[str]:
    for p in (issue.get("placements") or []):
        v = p.get("viewable") or {}
        guid = v.get("guid") or v.get("id")
        if guid:
            return guid
    for d in (issue.get("linkedDocuments") or []):
        v = ((d.get("details") or {}).get("viewable") or {})
        guid = v.get("guid") or v.get("id")
        if guid:
            return guid
    return None


def with_viewable_param(url: str, guid: Optional[str]) -> str:
    if not url or not guid:
        return url
    u = urllib.parse.urlsplit(url)
    qs = urllib.parse.parse_qsl(u.query, keep_blank_values=True)
    qs.append(("viewableGuid", guid))
    new_q = urllib.parse.urlencode(qs)
    return urllib.parse.urlunsplit((u.scheme, u.netloc, u.path, new_q, u.fragment))


def clean_comment_text(s: Optional[str]) -> str:
    if not s:
        return ""
    s = s.replace("\r\n", "\n").replace("\r", "\n").strip()
    s = " ".join(s.split())
    return s

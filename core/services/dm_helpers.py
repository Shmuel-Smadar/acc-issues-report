from typing import Tuple, List

def extract_pdf_names_from_contents(contents: dict) -> List[str]:
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

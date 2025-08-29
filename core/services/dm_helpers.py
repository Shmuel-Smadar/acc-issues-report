from typing import Tuple, List


def first_pdf_storage_from_contents(contents: dict) -> Tuple[str, str, str]:
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

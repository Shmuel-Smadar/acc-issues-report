import csv
import io
import logging
from typing import Iterable, Mapping, Any

CSV_HEADERS = [
    "project id",
    "project name",
    "document id",
    "document name",
    "document path",
    "link to the document page the issue located in",
    "issue id",
    "issue type",
    "issue sub type",
    "issue status",
    "issue due date",
    "issue start date",
    "issue title",
    "issue description",
    "issue comments",
]

_logger = logging.getLogger("app")

def _to_mapping(row: Any) -> Mapping[str, str]:
    if hasattr(row, "to_csv_row"):
        return row.to_csv_row()
    if isinstance(row, Mapping):
        return row
    raise TypeError(f"Unsupported row type: {type(row).__name__}")

def rows_to_csv(rows: Iterable[Any]) -> bytes:
    buf = io.StringIO(newline="")
    writer = csv.DictWriter(buf, fieldnames=CSV_HEADERS, extrasaction="ignore")
    writer.writeheader()
    n = 0
    for r in rows:
        writer.writerow(_to_mapping(r))
        n += 1
    _logger.info("event=csv.rows_written count=%s", n)
    return buf.getvalue().encode("utf-8")

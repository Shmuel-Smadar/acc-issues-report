import logging
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.conf import settings
from core.services.acc_client import ACCClient
from core.services.aggregate import IssueAggregator
from core.services.csv_export import rows_to_csv

logger = logging.getLogger("app")

def report_csv(request):
    client = ACCClient()
    logger.info("event=report.http_start project=%s", settings.TARGET_PROJECT_NAME)
    try:
        rows = IssueAggregator(client).collect_rows()
    except Exception as e:
        logger.error("event=report.http_error error=%s", str(e))
        return HttpResponseBadRequest(str(e))
    content = rows_to_csv(rows)
    resp = HttpResponse(content, content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = 'attachment; filename="acc_issues_report.csv"'
    logger.info("event=report.http_written rows=%s bytes=%s", len(rows), len(content))
    return resp

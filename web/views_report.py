from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.conf import settings
from core.services.acc_client import ACCClient
from core.services.aggregate import IssueAggregator
from core.services.csv_export import rows_to_csv


def report_csv(request):
    client = ACCClient()
    try:
        rows = IssueAggregator(client).collect_rows()
    except Exception as e:
        return HttpResponseBadRequest(str(e))
    content = rows_to_csv(rows)
    resp = HttpResponse(content, content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = 'attachment; filename="acc_issues_report.csv"'
    return resp

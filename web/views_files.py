from django.http import JsonResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.conf import settings
from core.services.acc_client import ACCClient


def list_files(request):
    client = ACCClient()
    project_id = client.get_project_id_by_name(settings.TARGET_PROJECT_NAME)
    if not project_id:
        return HttpResponseBadRequest("ACC_PROJECT_ID not set")
    files = client.list_all_files(project_id)
    return JsonResponse({"files": files})


def download_by_project_name(request):
    client = ACCClient()
    try:
        url = client.signed_url_for_first_pdf_in_project(settings.TARGET_PROJECT_NAME)
    except Exception as e:
        return HttpResponseBadRequest(str(e))
    return HttpResponseRedirect(url)

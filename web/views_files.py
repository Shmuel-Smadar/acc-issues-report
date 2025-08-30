from django.http import JsonResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.conf import settings
from core.services.acc_client import ACCClient

def download_by_project_name(request):
    client = ACCClient()
    try:
        url = client.signed_url_for_first_pdf_in_project(settings.TARGET_PROJECT_NAME)
    except Exception as e:
        return HttpResponseBadRequest(str(e))
    return HttpResponseRedirect(url)

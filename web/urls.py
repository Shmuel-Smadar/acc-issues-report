from django.urls import path
from .views_auth import index, login_start, oauth_callback, show_token
from .views_files import download_by_project_name
from .views_report import report_csv

urlpatterns = [
    path("", index, name="index"),
    path("auth/login/", login_start, name="login_start"),
    path("auth/callback/", oauth_callback, name="oauth_callback"),
    path("token/", show_token),
    path("download", download_by_project_name, name="download_by_project_name"),
    path("report.csv", report_csv, name="report_csv"),
]

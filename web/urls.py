from django.urls import path
from .views import index, login_start, oauth_callback, list_files, show_token, download_by_project_name

urlpatterns = [
    path("", index, name="index"),
    path("auth/login/", login_start, name="login_start"),
    path("auth/callback/", oauth_callback, name="oauth_callback"),
    path("files/", list_files, name="list_files"),
    path("token/", show_token),
    path("download", download_by_project_name, name="download_by_project_name"),
]

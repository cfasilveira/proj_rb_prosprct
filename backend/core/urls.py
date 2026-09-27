from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import path
from django.views.generic import RedirectView

from .views import dashboard

app_name = "core"

urlpatterns = [
    path("", login_required(dashboard), name="dashboard"),
    path("saude/", lambda request: JsonResponse({"status": "ok"}), name="health"),
    path("favicon.ico", RedirectView.as_view(url="/static/favicon.ico", permanent=False)),
]

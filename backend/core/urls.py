from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import path
from django.views.generic import RedirectView

from .views import dashboard, privacidade

app_name = "core"

urlpatterns = [
    path("", login_required(dashboard), name="dashboard"),
    path("privacidade/", privacidade, name="privacidade"),
    path("saude/", lambda request: JsonResponse({"status": "ok"}), name="health"),
    path("favicon.ico", RedirectView.as_view(url="/static/favicon-32.png", permanent=False)),
]

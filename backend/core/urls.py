from django.contrib.auth.decorators import login_required
from django.urls import path
from django.views.generic import RedirectView

from .views import dashboard, privacidade, saude, service_worker

app_name = "core"

urlpatterns = [
    path("", login_required(dashboard), name="dashboard"),
    path("privacidade/", privacidade, name="privacidade"),
    path("saude/", saude, name="health"),
    path("sw.js", service_worker, name="sw"),
    path("favicon.ico", RedirectView.as_view(url="/static/favicon-32.png", permanent=False)),
]

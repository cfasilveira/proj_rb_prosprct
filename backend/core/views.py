from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def dashboard(request: HttpRequest) -> HttpResponse:
    """Dashboard por perfil - implementado na etapa E4."""
    return render(request, "core/dashboard.html", {})

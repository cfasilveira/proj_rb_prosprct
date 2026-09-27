"""Gestão de promotoras — apenas gestor (PRD RF-02)."""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from core.models import Perfil

from .forms import PromotoraForm


class GestorRequiredMixin(LoginRequiredMixin):
    """Acesso restrito ao perfil gestor (RF-02, AC-05)."""

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.perfil.is_gestor:
            raise PermissionDenied("Área restrita ao gestor.")
        return super().dispatch(request, *args, **kwargs)


def _promotoras_com_contagem():
    return (
        Perfil.objects.filter(role=Perfil.ROLE_PROMOTORA)
        .select_related("user")
        .annotate(
            total=Count("user__revendedoras", distinct=True),
            ativas=Count(
                "user__revendedoras",
                filter=Q(user__revendedoras__desativado_em__isnull=True),
                distinct=True,
            ),
        )
        .order_by("-total", "nome_completo")
    )


class PromotoraListView(GestorRequiredMixin, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        return render(
            request,
            "accounts/promotora_list.html",
            {"promotoras": _promotoras_com_contagem()},
        )


class PromotoraCreateView(GestorRequiredMixin, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        return render(
            request,
            "accounts/promotora_form.html",
            {"form": PromotoraForm(), "titulo": "Nova promotora"},
        )

    def post(self, request: HttpRequest) -> HttpResponse:
        form = PromotoraForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Promotora criada ✓")
            return redirect("accounts:promotora_list")
        return render(
            request,
            "accounts/promotora_form.html",
            {"form": form, "titulo": "Nova promotora"},
        )


class PromotoraUpdateView(GestorRequiredMixin, View):
    def get_object(self, request, pk):
        return get_object_or_404(
            Perfil.objects.select_related("user"),
            pk=pk,
            role=Perfil.ROLE_PROMOTORA,
        )

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        perfil = self.get_object(request, pk)
        form = PromotoraForm(
            initial={
                "nome_completo": perfil.nome_completo,
                "email": perfil.user.email,
                "territorio": perfil.territorio,
            },
            instance=perfil,
        )
        return render(
            request,
            "accounts/promotora_form.html",
            {"form": form, "titulo": f"Editar {perfil.nome_completo}", "perfil": perfil},
        )

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        perfil = self.get_object(request, pk)
        form = PromotoraForm(request.POST, instance=perfil)
        if form.is_valid():
            form.save()
            messages.success(request, "Promotora atualizada ✓")
            return redirect("accounts:promotora_list")
        return render(
            request,
            "accounts/promotora_form.html",
            {"form": form, "titulo": f"Editar {perfil.nome_completo}", "perfil": perfil},
        )


class PromotoraDesativarView(GestorRequiredMixin, View):
    """Desativação soft: mantém cadastros e histórico (RF-02)."""

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        perfil = get_object_or_404(
            Perfil, pk=pk, role=Perfil.ROLE_PROMOTORA
        )
        if perfil.user_id == request.user.id:
            messages.error(request, "Você não pode desativar a própria conta.")
        else:
            perfil.ativo = not perfil.ativo
            perfil.save(update_fields=["ativo"])
            messages.success(
                request,
                "Promotora reativada ✓" if perfil.ativo else "Promotora desativada ✓",
            )
        return redirect("accounts:promotora_list")

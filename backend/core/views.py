"""Dashboard por perfil (PRD RF-05)."""
from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone

from prospeccao.models import Revendedora

from . import relatorios

PERIODOS = {
    "dia": "Hoje",
    "semana": "7 dias",
    "mes": "30 dias",
    "total": "Sempre",
}


def _desde(periodo: str):
    agora = timezone.now()
    if periodo == "dia":
        return agora - timedelta(days=1)
    if periodo == "semana":
        return agora - timedelta(days=7)
    if periodo == "mes":
        return agora - timedelta(days=30)
    return None


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    perfil = request.user.perfil
    periodo = request.GET.get("periodo", "total")
    if periodo not in PERIODOS:
        periodo = "total"

    queryset = Revendedora.ativas()
    if not perfil.is_gestor:
        queryset = queryset.filter(promotora=request.user)
    desde = _desde(periodo)
    if desde:
        queryset = queryset.filter(criado_em__gte=desde)

    total = queryset.count()
    ja_revendem = queryset.filter(ja_revende=True).count()
    pct = round(100 * ja_revendem / total) if total else 0

    ultimos = queryset.select_related("promotora", "cidade")[:10]

    por_promotora = []
    if perfil.is_gestor:
        from django.db.models import Count, Q

        por_promotora = list(
            Revendedora.ativas()
            .values(
                "promotora__id",
                "promotora__first_name",
                "promotora__last_name",
                "promotora__perfil__nome_completo",
                "promotora__perfil__territorio",
                "promotora__perfil__ativo",
            )
            .annotate(
                total=Count("id"),
                ja_revendem=Count("id", filter=Q(ja_revende=True)),
            )
            .order_by("-total")
        )
        for linha in por_promotora:
            linha["pct"] = (
                round(100 * linha["ja_revendem"] / linha["total"]) if linha["total"] else 0
            )

    contexto = {
        "perfil": perfil,
        "total": total,
        "ja_revendem": ja_revendem,
        "pct": pct,
        "ultimos": ultimos,
        "por_promotora": por_promotora,
        "periodo": periodo,
        "periodos": PERIODOS,
        "ano_atual": datetime.now().year,
    }

    if request.GET.get("exportar") == "pdf":
        conteudo = relatorios.pdf_dashboard(
            perfil=perfil,
            periodo_nome=PERIODOS[periodo],
            total=total,
            ja_revendem=ja_revendem,
            pct=pct,
            ultimos=list(ultimos),
            por_promotora=por_promotora,
        )
        resposta = HttpResponse(conteudo, content_type="application/pdf")
        resposta["Content-Disposition"] = f'attachment; filename="dashboard_{periodo}.pdf"'
        return resposta

    return render(request, "core/dashboard.html", contexto)


def privacidade(request: HttpRequest) -> HttpResponse:
    """Página de informações de dados pessoais (PRD RNF-06, LGPD)."""
    return render(request, "core/privacidade.html", {})

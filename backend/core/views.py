"""Dashboard por perfil (PRD RF-05)."""
from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.db import DatabaseError, connection
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils import timezone

from prospeccao.models import Revendedora

from . import exportacao, relatorios

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

    if request.GET.get("exportar") == "csv":
        resposta = HttpResponse(
            exportacao.csv_revendedoras(queryset), content_type="text/csv; charset=utf-8"
        )
        resposta["Content-Disposition"] = f'attachment; filename="revendedoras_{periodo}.csv"'
        return resposta

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


def service_worker(request: HttpRequest) -> HttpResponse:
    """Service Worker em `/sw.js` — escopo padrão `/` (AC-06, offline do shell).

    Servido como rota (e não como estático) para o `register()` não cair em
    `/static/js/…`, onde o worker só enxergaria pedidos da própria pasta.
    """
    return HttpResponse(
        render_to_string("sw.js"), content_type="application/javascript; charset=utf-8"
    )


def saude(request: HttpRequest) -> JsonResponse:
    """Health check do serviço: responde só se o banco aceitar conexão."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except DatabaseError:
        return JsonResponse({"status": "erro", "banco": "indisponivel"}, status=503)
    return JsonResponse({"status": "ok"})

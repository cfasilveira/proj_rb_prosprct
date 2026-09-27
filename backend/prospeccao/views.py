"""Views do cadastro de revendedoras (App Flow §2)."""
import datetime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import DeleteView, DetailView, ListView

from core.models import Perfil

from . import importacao
from .forms import (
    MAX_REDES,
    REVISAO,
    RevendedoraForm,
    draft_de_revendedora,
    limpa_telefones,
    opcoes_catalogo,
    valida_etapa,
)
from .models import Marca, Revendedora
from .services import criar_revendedora, obter_ou_criar_cidade

DRAFT_KEY = "revendedora_draft"
EDIT_KEY = "revendedora_edit_id"


def _escopo(queryset, user):
    """Escopo de acesso por perfil (RF-05, AC-05)."""
    if user.perfil.is_gestor:
        return queryset
    return queryset.filter(promotora=user)


def _serializa(valor):
    if hasattr(valor, "strftime"):
        return valor.strftime("%d/%m/%Y")
    return valor


def _dados_escalares(form: RevendedoraForm, draft: dict, campos: list[str]):
    """Grava no draft só os campos escalares válidos da etapa."""
    for campo in campos:
        if campo in {"telefones", "redes", "marcas", "interesses", "cidade"}:
            continue
        if campo in form.cleaned_data:
            draft[campo] = _serializa(form.cleaned_data[campo])


def _parse_telefones(request: HttpRequest) -> list[str]:
    return limpa_telefones(request.POST.getlist("telefone"))


def _parse_redes(request: HttpRequest) -> list[dict]:
    redes = []
    for i in range(MAX_REDES):
        perfil = (request.POST.get(f"rede_perfil_{i}") or "").strip()
        rede_id = request.POST.get(f"rede_id_{i}") or ""
        if not perfil and not rede_id:
            continue
        redes.append(
            {
                "rede_id": int(rede_id) if rede_id else None,
                "perfil": perfil,
                "contato": request.POST.get(f"rede_contato_{i}") == "on",
                "seguir": request.POST.get(f"rede_seguir_{i}") == "on",
            }
        )
    return redes


class RevendedoraWizardView(LoginRequiredMixin, View):
    """Wizard em 5 telas: 4 etapas de form + revisão (App Flow §2)."""

    template = "prospeccao/revendedora_wizard.html"

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if request.GET.get("sucesso"):
            request.session.pop(DRAFT_KEY, None)
            request.session.pop(EDIT_KEY, None)
            return render(request, "prospeccao/revendedora_sucesso.html")

        if "editar" in request.GET:
            revendedora = get_object_or_404(
                _escopo(Revendedora.ativas(), request.user), pk=request.GET["editar"]
            )
            request.session[DRAFT_KEY] = draft_de_revendedora(revendedora)
            request.session[EDIT_KEY] = revendedora.pk
            return redirect("prospeccao:revendedora_nova")

        draft = request.session.get(DRAFT_KEY, {})
        if not draft:
            draft = {"vende_outras_marcas": "nao", "telefones": [], "redes": [],
                     "marca_ids": [], "marca_nova": "", "interesses": []}
            request.session[DRAFT_KEY] = draft

        etapa = int(request.GET.get("etapa", 1))
        if etapa > 1 and not draft.get("nome_completo"):
            return redirect("prospeccao:revendedora_nova")
        return self._render(request, etapa, draft)

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        etapa = int(request.POST.get("etapa", 1))
        acao = request.POST.get("acao", "avancar")
        draft = request.session.get(DRAFT_KEY, {})

        if acao == "voltar":
            destino = max(etapa - 1, 1)
            return redirect(f"{reverse('prospeccao:revendedora_nova')}?etapa={destino}")

        if etapa == REVISAO:
            return self._salvar(request, draft)

        # dados escalares: draft cobre o que não veio no POST
        data = {k: v for k, v in draft.items() if not isinstance(v, (list, dict))}
        data.update(request.POST.dict())
        form = RevendedoraForm(data=data)

        # listas da etapa atual
        if etapa == 1:
            try:
                draft["telefones"] = _parse_telefones(request)
            except Exception:  # noqa: BLE001 - erro vira mensagem de campo
                form.add_error(None, "Telefone inválido: use DDD + número.")
                draft.setdefault("telefones", [])
            draft["redes"] = _parse_redes(request)
        elif etapa == 3:
            draft["marca_ids"] = [int(v) for v in request.POST.getlist("marca_id")]
            draft["marca_nova"] = (request.POST.get("marca_nova") or "").strip()

        draft["vende_outras_marcas"] = request.POST.get("vende_outras_marcas") or "nao"
        if etapa == 4:
            draft["interesses"] = [int(v) for v in request.POST.getlist("interesse_id")]

        erros = valida_etapa(form, draft, etapa)
        if not erros:
            _dados_escalares(form, draft, ["nome_completo", "email", "data_nascimento",
                                           "cpf", "rg", "cep", "endereco", "bairro",
                                           "cidade_nome", "cidade_uf"])
            if etapa == 2 and draft.get("cpf"):
                duplicado = Revendedora.objects.filter(cpf=draft["cpf"])
                edit_id = request.session.get(EDIT_KEY)
                if edit_id:
                    duplicado = duplicado.exclude(pk=edit_id)
                if duplicado.exists():
                    erros["cpf"] = ["Este CPF já está em uso."]
        if not erros:
            request.session[DRAFT_KEY] = draft
            return redirect(f"{reverse('prospeccao:revendedora_nova')}?etapa={etapa + 1}")

        request.session[DRAFT_KEY] = draft
        return self._render(request, etapa, draft, form=form, erros=erros)

    def _render(self, request, etapa, draft, form=None, erros=None) -> HttpResponse:
        from .models import ProdutoInteresse, RedeSocial

        if form is None:
            form = RevendedoraForm(
                data={k: v for k, v in draft.items() if not isinstance(v, (list, dict))}
            )
        redes_draft = [r for r in draft.get("redes", []) if r.get("perfil")]
        redes_input = redes_draft + [
            {"rede_id": None, "perfil": "", "contato": False, "seguir": False}
        ][: max(MAX_REDES - len(redes_draft), 0)] or [
            {"rede_id": None, "perfil": "", "contato": False, "seguir": False}
        ]
        contexto = {
            "form": form,
            "draft": draft,
            "etapa": etapa,
            "revisao": etapa == REVISAO,
            "erros": erros or {},
            "editando": bool(request.session.get(EDIT_KEY)),
            "telefones_input": draft.get("telefones") or [""],
            "redes_input": redes_input,
            "marcas_draft": list(
                Marca.objects.filter(id__in=draft.get("marca_ids", [])).values_list("nome", flat=True)
            ),
            "interesses_draft": ProdutoInteresse.objects.filter(
                id__in=draft.get("interesses", [])
            ),
            "resumo_redes": [
                {
                    "nome": dict(RedeSocial.objects.values_list("id", "nome")).get(
                        r.get("rede_id"), "—"
                    ),
                    "perfil": r.get("perfil"),
                    "contato": r.get("contato"),
                    "seguir": r.get("seguir"),
                }
                for r in redes_draft
            ],
            **opcoes_catalogo(),
        }
        return render(request, self.template, contexto)

    def _salvar(self, request, draft) -> HttpResponse:
        if not draft.get("nome_completo"):
            return redirect("prospeccao:revendedora_nova")

        cidade = obter_ou_criar_cidade(draft["cidade_nome"], draft["cidade_uf"])
        data_nascimento = draft.get("data_nascimento") or None
        if isinstance(data_nascimento, str):
            data_nascimento = datetime.datetime.strptime(data_nascimento, "%d/%m/%Y").date()
        dados = {
            "nome_completo": draft["nome_completo"],
            "cpf": draft.get("cpf") or None,
            "rg": draft.get("rg", ""),
            "email": draft.get("email", ""),
            "data_nascimento": data_nascimento,
            "endereco": draft.get("endereco", ""),
            "bairro": draft.get("bairro", ""),
            "cidade": cidade,
            "cep": draft.get("cep") or "",
            "vende_outras_marcas": draft.get("vende_outras_marcas") == "sim",
        }
        telefones = [
            {"numero": n, "tipo": "whatsapp", "principal": i == 0}
            for i, n in enumerate(draft.get("telefones", []))
        ]
        if dados["vende_outras_marcas"]:
            nomes = list(
                Marca.objects.filter(id__in=draft.get("marca_ids", [])).values_list("nome", flat=True)
            )
            if draft.get("marca_nova"):
                nomes.append(draft["marca_nova"])
            marcas = nomes
        else:
            marcas = None

        redes = [
            {
                "rede_id": r["rede_id"],
                "perfil": r["perfil"],
                "para_contato": r.get("contato", False),
                "para_seguir": r.get("seguir", False),
            }
            for r in draft.get("redes", [])
            if r.get("perfil") and r.get("rede_id")
        ]

        edit_id = request.session.get(EDIT_KEY)
        try:
            if edit_id:
                from .services import atualizar_revendedora

                revendedora = get_object_or_404(
                    _escopo(Revendedora.ativas(), request.user), pk=edit_id
                )
                atualizar_revendedora(
                    revendedora, dados=dados, telefones=telefones, marcas=marcas,
                    interesses=draft.get("interesses", []), redes=redes,
                )
                mensagens = "Revendedora atualizada ✓"
            else:
                criar_revendedora(
                    promotora=request.user, dados=dados, telefones=telefones,
                    marcas=marcas, interesses=draft.get("interesses", []), redes=redes,
                )
                mensagens = "Revendedora cadastrada ✓"
        except ValidationError as erro:
            return self._render(
                request, REVISAO, draft,
                erros={"geral": erro.messages},
            )

        messages.success(request, mensagens)
        request.session.pop(DRAFT_KEY, None)
        request.session.pop(EDIT_KEY, None)
        return redirect(f"{reverse('prospeccao:revendedora_nova')}?sucesso=1")


class RevendedoraListView(LoginRequiredMixin, ListView):
    template_name = "prospeccao/revendedora_list.html"
    context_object_name = "revendedoras"

    def get_queryset(self):
        return _escopo(Revendedora.ativas(), self.request.user).select_related(
            "promotora", "cidade"
        )


class RevendedoraDetailView(LoginRequiredMixin, DetailView):
    template_name = "prospeccao/revendedora_detail.html"
    context_object_name = "revendedora"

    def get_queryset(self):
        return _escopo(Revendedora.ativas(), self.request.user).select_related(
            "promotora", "cidade"
        ).prefetch_related("telefones", "marcas_revendidas", "interesses", "redes__rede")


class RevendedoraDeleteView(LoginRequiredMixin, DeleteView):
    """Exclusão lógica (RF-03, soft delete)."""

    template_name = "prospeccao/revendedora_confirm_delete.html"
    context_object_name = "revendedora"

    def get_queryset(self):
        return _escopo(Revendedora.ativas(), self.request.user)

    def form_valid(self, form):
        self.object.desativar()
        messages.success(self.request, "Revendedora removida da carteira.")
        return redirect("prospeccao:revendedora_list")


CHAVE_IMPORTACAO = "importacao_planilha"
MAX_PREVIA = 200
TIPO_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _promotoras_ativas():
    return (
        Perfil.objects.filter(role=Perfil.ROLE_PROMOTORA, ativo=True)
        .select_related("user")
        .order_by("nome_completo")
    )


class ImportarExcelView(LoginRequiredMixin, View):
    """Planilha Excel -> prévia com erros linha a linha -> grava em lote.

    Nada é gravado na análise: a prévia só mostra o que aconteceria, e a
    confirmação revalida e chama `criar_revendedora` linha a linha.
    """

    template = "prospeccao/importar.html"

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if request.GET.get("modelo"):
            resposta = HttpResponse(importacao.modelo(), content_type=TIPO_XLSX)
            resposta["Content-Disposition"] = 'attachment; filename="modelo_revendedoras.xlsx"'
            return resposta
        return self._render(request)

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        acao = request.POST.get("acao", "")

        if acao == "cancelar":
            request.session.pop(CHAVE_IMPORTACAO, None)
            messages.info(request, "Importação cancelada.")
            return redirect("prospeccao:importar")

        if acao == "confirmar":
            return self._confirma(request)

        if acao == "analisar":
            return self._analisar(request)

        return self._render(request)

    def _promotora_alvo(self, request: HttpRequest):
        """Promotora que vai receber os cadastros (gestor escolhe; promotoras, elas mesmas)."""
        if not request.user.perfil.is_gestor:
            return request.user
        escolhida = request.POST.get("promotora_id")
        if not escolhida:
            return None
        perfil = (
            _promotoras_ativas().filter(pk=escolhida).first()
        )
        return perfil.user if perfil else None

    def _analisar(self, request: HttpRequest) -> HttpResponse:
        arquivo = request.FILES.get("planilha")
        promotora = self._promotora_alvo(request)

        if not arquivo:
            messages.error(request, "Escolha um arquivo .xlsx para importar.")
            return self._render(request, request.POST.get("promotora_id"))
        if promotora is None:
            messages.error(request, "Escolha a promotora que vai receber os cadastros.")
            return self._render(request, request.POST.get("promotora_id"))

        try:
            linhas = importacao.ler_planilha(arquivo)
        except importacao.ErroDePlanilha as erro:
            messages.error(request, str(erro))
            return self._render(request, promotora.pk)

        request.session[CHAVE_IMPORTACAO] = {"linhas": linhas, "promotora_id": promotora.pk}
        return self._render(request, promotora.pk)

    def _confirma(self, request: HttpRequest) -> HttpResponse:
        pacote = request.session.get(CHAVE_IMPORTACAO)
        if not pacote:
            messages.error(request, "Envie uma planilha primeiro.")
            return redirect("prospeccao:importar")

        perfil = Perfil.objects.select_related("user").filter(pk=pacote["promotora_id"]).first()
        if perfil is None or not perfil.ativo:
            messages.error(request, "A promotora escolhida não está mais disponível.")
            request.session.pop(CHAVE_IMPORTACAO, None)
            return redirect("prospeccao:importar")
        if not request.user.perfil.is_gestor and perfil.user_id != request.user.pk:
            messages.error(request, "Você só pode importar para a própria carteira.")
            request.session.pop(CHAVE_IMPORTACAO, None)
            return redirect("prospeccao:importar")

        resultados = importacao.analisa(pacote["linhas"])
        resumo = importacao.importa(resultados, perfil.user)

        for falha in resumo["falhas"]:
            messages.error(request, falha)

        if not resumo["criadas"]:
            messages.error(
                request,
                "Nenhuma linha pôde ser importada. Corrija a planilha e envie de novo.",
            )
            return self._render(request, perfil.pk)

        request.session.pop(CHAVE_IMPORTACAO, None)
        aviso = f"{resumo['criadas']} revendedora(s) importada(s) para {perfil.nome_completo}."
        if resumo["puladas"]:
            aviso += f" {resumo['puladas']} linha(s) com erro foram ignoradas."
        messages.success(request, aviso)
        return redirect("prospeccao:importar")

    def _render(self, request: HttpRequest, promotora_selecionada=None) -> HttpResponse:
        pacote = request.session.get(CHAVE_IMPORTACAO)
        resultados = importacao.analisa(pacote["linhas"]) if pacote else []
        validas = sum(1 for linha in resultados if linha.ok)
        gestor = request.user.perfil.is_gestor
        try:
            selecionada = int(promotora_selecionada) if promotora_selecionada else None
        except (TypeError, ValueError):
            selecionada = None
        contexto = {
            "pacote": pacote,
            "resultados": resultados[:MAX_PREVIA],
            "total": len(resultados),
            "validas": validas,
            "com_erro": len(resultados) - validas,
            "promotoras": _promotoras_ativas() if gestor else [],
            "promotora_atual": selecionada or (pacote or {}).get("promotora_id"),
            "max_previa": MAX_PREVIA,
        }
        return render(request, self.template, contexto)

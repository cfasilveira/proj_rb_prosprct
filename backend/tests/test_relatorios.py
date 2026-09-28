"""Testes da exportação em PDF (PRD fase 2 — fase 2: exportação de relatórios)."""
import base64
import codecs
import re
import unicodedata
import zlib
from types import SimpleNamespace

import pytest
from django.urls import reverse

import relatorio
from core import relatorios

pytestmark = pytest.mark.django_db

DASHBOARD = reverse("core:dashboard")


def _texto_do_pdf(pdf: bytes) -> str:
    """Extrai o texto dos PDF (ASCII85 + Flate) para conferir o conteúdo.

    Só decodifica as streams de página (`/ASCII85Decode`), senão os gráficos
    embutidos viram lixo e escondem o texto.
    """
    pedacos = []
    for trecho in re.finditer(rb"<<([^<>]*)>>\s*stream\r?\n(.*?)endstream", pdf, re.S):
        cabecalho, bruto = trecho.group(1), trecho.group(2).strip()
        if b"ASCII85Decode" not in cabecalho:
            continue
        if bruto.endswith(b"~>"):
            bruto = bruto[:-2]
        try:
            pedacos.append(zlib.decompress(base64.a85decode(bruto)))
        except Exception:  # noqa: BLE001
            continue
    texto = b" ".join(pedacos).decode("latin-1", "replace")
    texto = re.sub(r"\\([0-7]{1,3})", lambda m: chr(int(m.group(1), 8)), texto)
    texto = texto.replace("\\(", "(").replace("\\)", ")")
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()


@pytest.fixture
def gestor(django_user_model):
    user = django_user_model.objects.create_user(
        email="gestor@pdf.com", password="x", username="gestor_pdf"
    )
    user.perfil.role = "gestor"
    user.perfil.save()
    return user


@pytest.fixture
def promotora(django_user_model):
    return django_user_model.objects.create_user(
        email="promo@pdf.com", password="x", username="promo_pdf"
    )


def test_dashboard_continua_sendo_html_por_padrao(client, gestor):
    client.force_login(gestor)
    resposta = client.get(DASHBOARD)
    assert resposta.status_code == 200
    assert "text/html" in resposta["Content-Type"]
    assert not resposta.content.startswith(b"%PDF-")
    assert b"exportar=pdf" in resposta.content


def test_dashboard_exporta_pdf(client, gestor):
    client.force_login(gestor)
    resposta = client.get(f"{DASHBOARD}?periodo=total&exportar=pdf")
    assert resposta.status_code == 200
    assert resposta["Content-Type"] == "application/pdf"
    assert "attachment" in resposta["Content-Disposition"]
    assert resposta.content.startswith(b"%PDF-")

    texto = _texto_do_pdf(resposta.content)
    assert "RB Prospecta" in texto
    assert "Cadastro por promotora" in texto
    assert "Ultimos cadastros" in texto or "Últimos cadastros" in texto


def test_dashboard_pdf_da_promotora_nao_mostra_a_carteira_consolidada(client, promotora):
    client.force_login(promotora)
    resposta = client.get(f"{DASHBOARD}?exportar=pdf")
    assert resposta.status_code == 200
    assert resposta.content.startswith(b"%PDF-")

    texto = _texto_do_pdf(resposta.content)
    assert "Cadastro por promotora" not in texto
    assert "Carteira de" in texto


def test_dashboard_pdf_requer_login(client):
    assert client.get(f"{DASHBOARD}?exportar=pdf").status_code == 302


def test_pdf_do_dashboard_com_dados_vazios():
    """Sem cadastro nenhum o PDF ainda precisa sair (sem ZeroDivisionError)."""
    perfil = SimpleNamespace(is_gestor=True, nome_completo="Gestor Teste")
    pdf = relatorios.pdf_dashboard(
        perfil=perfil,
        periodo_nome="Sempre",
        total=0,
        ja_revendem=0,
        pct=0,
        ultimos=[],
        por_promotora=[],
    )
    assert pdf.startswith(b"%PDF-")
    assert "Cadastro por promotora" in _texto_do_pdf(pdf)


def test_pdf_das_analises_com_grafico_plotly():
    import graficos

    fig = graficos.a1(
        [
            {"promotora_nome": "Ana Souza", "cadastradas": 17, "ja_revendem": 10, "pct": 58.8},
            {"promotora_nome": "Beatriz Lima", "cadastradas": 16, "ja_revendem": 11, "pct": 68.8},
        ]
    )
    pdf = relatorio.gerar_pdf(
        "RB Prospecta · A1 — Cadastros",
        "Periodo: sempre · Todas as promotoras",
        [
            relatorio.kpis([("Cadastradas", 33), ("Ja revendem", 21)]),
            relatorio.grafico("Cadastros por promotora", fig, "Fonte: teste."),
            relatorio.tabela("Detalhe", ["Promotora", "Cadastradas"], [["Ana Souza", 17]]),
        ],
    )
    assert pdf.startswith(b"%PDF-")
    texto = _texto_do_pdf(pdf)
    assert "Cadastros por promotora" in texto
    assert "Ana Souza" in texto


def test_gerar_csv_das_analises():
    """CSV das análises: `;`, BOM e None como célula vazia (PRD fase 2)."""
    bytes_csv = relatorio.gerar_csv(
        [
            {"promotora_nome": "Ana", "cadastradas": 17, "pct": 58.8},
            {"promotora_nome": "Bia;Zika", "cadastradas": 16, "pct": None},
        ]
    )
    assert bytes_csv.startswith(codecs.BOM_UTF8)
    linhas = bytes_csv.decode("utf-8-sig").splitlines()
    assert linhas[0] == "promotora_nome;cadastradas;pct"
    assert linhas[1] == "Ana;17;58.8"
    assert linhas[2] == '"Bia;Zika";16;'


def test_gerar_csv_com_colunas_na_ordem_escolhida():
    bytes_csv = relatorio.gerar_csv([{"b": 1, "a": 2}], ["a", "b"])
    assert bytes_csv.decode("utf-8-sig").splitlines() == ["a;b", "2;1"]


def _configura_url_do_analytics(monkeypatch, settings):
    cfg = settings.DATABASES["default"]
    senha = cfg.get("PASSWORD") or ""
    url = (
        f"postgres://{cfg['USER']}:{senha}"
        f"@{cfg.get('HOST') or 'localhost'}:{cfg.get('PORT') or 5432}/{cfg['NAME']}"
    )
    monkeypatch.setattr("db.DATABASE_URL", url)


@pytest.mark.django_db(transaction=True)
def test_relatorio_completo_cobre_a1_a4(monkeypatch, settings, django_user_model):
    """A Home gera um único PDF com as 4 análises (PRD fase 2)."""
    from prospeccao.models import Cidade, ProdutoInteresse, RedeSocial
    from prospeccao.seeds import PRODUTOS, REDES
    from prospeccao.services import criar_revendedora

    for ordem, nome in enumerate(PRODUTOS, start=1):
        ProdutoInteresse.objects.get_or_create(nome=nome, defaults={"ordem": ordem})
    for nome in REDES:
        RedeSocial.objects.get_or_create(nome=nome)

    promotora = django_user_model.objects.create_user(
        email="promo@completo.com", password="x", username="promo_completo"
    )
    cidade = Cidade.objects.get_or_create(nome="Recife", uf="PE")[0]
    criar_revendedora(
        promotora=promotora,
        dados={"nome_completo": "Ana Souza", "cidade": cidade, "vende_outras_marcas": True},
        telefones=[{"numero": "81999998888"}],
        marcas=["Natura"],
        interesses=list(ProdutoInteresse.objects.values_list("id", flat=True))[:2],
    )

    _configura_url_do_analytics(monkeypatch, settings)
    pdf = relatorio.completo()
    assert pdf.startswith(b"%PDF-")
    texto = _texto_do_pdf(pdf)
    assert "Cadastros por promotora" in texto
    assert "Marcas ja revendidas" in texto or "Marcas já revendidas" in texto
    assert "Interesse em produtos" in texto

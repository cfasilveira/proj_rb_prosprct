"""Testes da exportação em CSV do dashboard (PRD fase 2 — exportação de relatórios)."""
import codecs
import csv
import io
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from core import exportacao
from prospeccao.models import Cidade, ProdutoInteresse, Revendedora
from prospeccao.services import criar_revendedora

pytestmark = pytest.mark.django_db

DASHBOARD = reverse("core:dashboard")


@pytest.fixture
def promotora(django_user_model):
    return django_user_model.objects.create_user(
        email="promo@csv.com", password="x", username="promo_csv"
    )


@pytest.fixture
def promotora2(django_user_model):
    return django_user_model.objects.create_user(
        email="promo2@csv.com", password="x", username="promo2_csv"
    )


@pytest.fixture
def gestor(django_user_model):
    user = django_user_model.objects.create_user(
        email="gestor@csv.com", password="x", username="gestor_csv"
    )
    user.perfil.role = "gestor"
    user.perfil.save()
    return user


@pytest.fixture
def cidade():
    return Cidade.objects.create(nome="Curitiba", uf="PR")


def _cria(promotora, cidade, nome, cpf=None, com_marca=False):
    return criar_revendedora(
        promotora=promotora,
        dados={
            "nome_completo": nome,
            "cidade": cidade,
            "vende_outras_marcas": com_marca,
            "cpf": cpf,
            "rg": "12345",
            "email": "contato@revenda.com",
            "bairro": "Centro",
            "endereco": "Rua das Flores, 12",
            "cep": "80010010",
            "observacao": "Prefere contato à tarde",
        },
        telefones=[{"numero": "41999998888", "principal": True}, {"numero": "4133334444"}],
        marcas=["Natura"] if com_marca else None,
        interesses=[ProdutoInteresse.objects.first().pk],
    )


def _linhas(resposta) -> list[dict]:
    """Lê o arquivo como o Excel faria: BOM + separador `;`."""
    texto = resposta.content.decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(texto), delimiter=";"))


def _cabecalho(resposta) -> list[str]:
    primeira_linha = resposta.content.split(b"\r\n")[0]
    return primeira_linha.decode("utf-8-sig").split(";")


def test_csv_requer_login(client):
    assert client.get(f"{DASHBOARD}?exportar=csv").status_code == 302


def test_dashboard_oferece_os_dois_formatos(client, gestor):
    client.force_login(gestor)
    resposta = client.get(DASHBOARD)
    assert b"exportar=csv" in resposta.content
    assert b"exportar=pdf" in resposta.content


def test_csv_responde_com_download(client, gestor):
    client.force_login(gestor)
    resposta = client.get(f"{DASHBOARD}?exportar=csv")
    assert resposta.status_code == 200
    assert "text/csv" in resposta["Content-Type"]
    assert resposta["Content-Disposition"] == 'attachment; filename="revendedoras_total.csv"'
    assert resposta.content.startswith(codecs.BOM_UTF8)


def test_csv_traz_as_colunas_e_os_dados_da_revendedora(client, gestor, promotora, cidade):
    _cria(promotora, cidade, "José da Conceição", cpf="12345678901", com_marca=True)

    client.force_login(gestor)
    resposta = client.get(f"{DASHBOARD}?exportar=csv")

    assert _cabecalho(resposta) == exportacao.COLUNAS
    (linha,) = _linhas(resposta)
    assert linha["Nome completo"] == "José da Conceição"
    assert linha["CPF"] == "123.456.789-01"
    assert linha["RG"] == "12345"
    assert linha["E-mail"] == "contato@revenda.com"
    assert linha["Telefone(s)"] == "41999998888 / 4133334444"
    assert (linha["Cidade"], linha["UF"]) == ("Curitiba", "PR")
    assert linha["Bairro"] == "Centro"
    assert linha["Endereço"] == "Rua das Flores, 12"
    assert linha["CEP"] == "80010010"
    assert linha["Promotora"] == promotora.perfil.nome_completo
    assert linha["Marcas revendidas"] == "Natura"
    assert linha["Interesses"] != ""
    assert linha["Observação"] == "Prefere contato à tarde"
    assert linha["Cadastrada em"]


def test_csv_deriva_ja_revende_das_marcas(client, gestor, promotora, cidade):
    _cria(promotora, cidade, "Com marca", com_marca=True)
    _cria(promotora, cidade, "Sem marca", com_marca=False)

    client.force_login(gestor)
    ja_revende = {
        linha["Nome completo"]: linha["Já revende"]
        for linha in _linhas(client.get(f"{DASHBOARD}?exportar=csv"))
    }
    assert ja_revende == {"Com marca": "sim", "Sem marca": "não"}


def test_csv_respeita_o_escopo_da_promotora(client, promotora, promotora2, cidade):
    _cria(promotora, cidade, "Da minha carteira")
    _cria(promotora2, cidade, "De outra carteira")

    client.force_login(promotora)
    resposta = client.get(f"{DASHBOARD}?exportar=csv")
    nomes = [linha["Nome completo"] for linha in _linhas(resposta)]
    assert nomes == ["Da minha carteira"]


def test_csv_respeita_o_filtro_de_periodo(client, gestor, promotora, cidade):
    antiga = _cria(promotora, cidade, "Antiga")
    Revendedora.objects.filter(pk=antiga.pk).update(
        criado_em=timezone.now() - timedelta(days=40)
    )
    _cria(promotora, cidade, "Recente")

    client.force_login(gestor)
    nomes = [
        linha["Nome completo"]
        for linha in _linhas(client.get(f"{DASHBOARD}?periodo=mes&exportar=csv"))
    ]
    assert nomes == ["Recente"]


def test_csv_com_carteira_vazia_so_cabecalho(client, gestor):
    client.force_login(gestor)
    resposta = client.get(f"{DASHBOARD}?exportar=csv")
    assert resposta.status_code == 200
    assert _cabecalho(resposta) == exportacao.COLUNAS
    assert _linhas(resposta) == []


def test_csv_preserva_acentos(client, gestor, promotora, cidade):
    _cria(promotora, cidade, "Conceição Assunção")

    client.force_login(gestor)
    assert _linhas(client.get(f"{DASHBOARD}?exportar=csv"))[0]["Nome completo"] == (
        "Conceição Assunção"
    )


def test_csv_exclui_revendedora_ja_anonimizada(client, gestor, promotora, cidade):
    revendedora = _cria(promotora, cidade, "Dados pessoais")
    revendedora.excluir_dados_pessoais()

    client.force_login(gestor)
    assert _linhas(client.get(f"{DASHBOARD}?exportar=csv")) == []


def test_csv_nao_dispara_consulta_por_linha(
    client, gestor, promotora, cidade, django_assert_max_num_queries
):
    """O detalhe inteiro precisa sair em poucas queries (sem N+1)."""
    for indice in range(5):
        _cria(promotora, cidade, f"Revendedora {indice}", com_marca=True)

    client.force_login(gestor)
    with django_assert_max_num_queries(10):
        client.get(f"{DASHBOARD}?exportar=csv")


def test_valor_desconhecido_de_exportar_continua_sendo_html(client, gestor):
    client.force_login(gestor)
    resposta = client.get(f"{DASHBOARD}?exportar=zip")
    assert "text/html" in resposta["Content-Type"]


def test_cpf_invalido_nao_quebra_a_mascara():
    assert exportacao._cpf(None) == ""
    assert exportacao._cpf("") == ""
    assert exportacao._cpf("123") == "123"

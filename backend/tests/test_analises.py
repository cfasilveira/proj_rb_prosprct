"""Testes de E5: queries das análises A1–A4 (PRD RF-06, AC-04)."""
import re
from datetime import timedelta

import analytics.db as db
import analytics.graficos as graficos
import analytics.queries as queries
import pytest
from django.utils import timezone

from prospeccao.models import Cidade, ProdutoInteresse, Revendedora
from prospeccao.services import criar_revendedora

# transaction=True: as queries abrem conexão psycopg própria e precisam ver commits
pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture(autouse=True)
def garante_seeds():
    """transaction=True trunca as tabelas entre testes — recria os catálogos."""
    from prospeccao.models import ProdutoInteresse, RedeSocial
    from prospeccao.seeds import PRODUTOS, REDES

    for i, nome in enumerate(PRODUTOS, start=1):
        ProdutoInteresse.objects.get_or_create(nome=nome, defaults={"ordem": i})
    for nome in REDES:
        RedeSocial.objects.get_or_create(nome=nome)


@pytest.fixture(autouse=True)
def analytics_no_test_db(monkeypatch, settings):
    """Faz o analytics conectar no banco de teste do pytest-django."""
    cfg = settings.DATABASES["default"]
    senha = cfg.get("PASSWORD") or ""
    url = (
        f"postgres://{cfg['USER']}:{senha}"
        f"@{cfg.get('HOST') or 'localhost'}:{cfg.get('PORT') or 5432}/{cfg['NAME']}"
    )
    monkeypatch.setattr(db, "DATABASE_URL", url)


@pytest.fixture
def promo1(django_user_model):
    return django_user_model.objects.create_user(
        email="p1@test.com", password="x", username="p1"
    )


@pytest.fixture
def promo2(django_user_model):
    return django_user_model.objects.create_user(
        email="p2@test.com", password="x", username="p2"
    )


@pytest.fixture
def curitiba():
    return Cidade.objects.create(nome="Curitiba", uf="PR")


@pytest.fixture
def londrina():
    return Cidade.objects.create(nome="Londrina", uf="PR")


def _rev(promotora, cidade, nome, marcas=None, categorias=1):
    interesse_ids = list(ProdutoInteresse.objects.values_list("id", flat=True))[:categorias]
    return criar_revendedora(
        promotora=promotora,
        dados={
            "nome_completo": nome,
            "cidade": cidade,
            "vende_outras_marcas": bool(marcas),
        },
        telefones=[{"numero": "41999998888"}],
        marcas=marcas,
        interesses=interesse_ids,
    )


@pytest.fixture
def carteira(promo1, promo2, curitiba, londrina):
    """4 revendedoras: 2 da promo1 (1 já revende), 2 da promo2 (2 já revendem)."""
    _rev(promo1, curitiba, "Ana", marcas=["MarcaA"], categorias=2)
    _rev(promo1, londrina, "Bia", categorias=2)
    _rev(promo2, curitiba, "Cris", marcas=["MarcaA", "MarcaB"], categorias=1)
    _rev(promo2, curitiba, "Duda", marcas=["MarcaB"], categorias=3)
    return True


def test_a1_por_promotora(carteira):
    linhas = db.executar(queries.SQL_A1, queries.params())
    por_nome = {linha["promotora_nome"]: linha for linha in linhas}

    assert len(linhas) == 2
    assert por_nome["p1@test.com"]["cadastradas"] == 2
    assert por_nome["p1@test.com"]["ja_revendem"] == 1
    assert por_nome["p2@test.com"]["cadastradas"] == 2
    assert por_nome["p2@test.com"]["ja_revendem"] == 2
    assert por_nome["p1@test.com"]["pct"] == 50.0


def test_a1_soma_bate_com_total(carteira):
    linhas = db.executar(queries.SQL_A1, queries.params())
    a2 = db.executar(queries.SQL_A2, queries.params())[0]
    assert sum(linha["cadastradas"] for linha in linhas) == a2["total"] == 4


def test_a2_consolidado(carteira):
    a2 = db.executar(queries.SQL_A2, queries.params())[0]
    assert a2["total"] == 4
    assert a2["ja_revendem"] == 3
    assert a2["nao_revendem"] == 1
    assert a2["pct"] == 75.0


def test_a2_por_cidade(carteira):
    linhas = db.executar(queries.SQL_A2_CIDADE, queries.params())
    por_cidade = {linha["cidade"]: linha for linha in linhas}
    assert por_cidade["Curitiba/PR"]["total"] == 3
    assert por_cidade["Londrina/PR"]["total"] == 1


def test_a3_marcas(carteira):
    linhas = db.executar(queries.SQL_A3, queries.params())
    por_marca = {linha["marca"]: linha for linha in linhas}
    assert por_marca["MarcaA"]["revendedoras"] == 2
    assert por_marca["MarcaB"]["revendedoras"] == 2
    # pct é sobre as 3 que já revendem
    assert por_marca["MarcaA"]["pct"] == pytest.approx(66.7, abs=0.1)


def test_a4_interesse(carteira):
    linhas = db.executar(queries.SQL_A4, queries.params())
    categorias = [linha["categoria"] for linha in linhas]
    assert len(linhas) >= 3
    # 4 revendedoras, a primeira tem 2 interesses
    assert linhas[0]["interessadas"] >= 1
    assert "Cosméticos" in categorias
    ordens = [linha["ordem"] for linha in linhas]
    assert ordens == sorted(ordens)  # ordenado por ordem do seed


def test_filtro_por_promotora(carteira, promo1):
    linhas = db.executar(queries.SQL_A1, queries.params(promotora_id=promo1.pk))
    assert len(linhas) == 1
    assert linhas[0]["cadastradas"] == 2

    a2 = db.executar(queries.SQL_A2, queries.params(promotora_id=promo1.pk))[0]
    assert a2["total"] == 2
    assert a2["ja_revendem"] == 1


def test_filtro_por_periodo(carteira):
    antiga = Revendedora.objects.first()
    Revendedora.objects.filter(pk=antiga.pk).update(
        criado_em=timezone.now() - timedelta(days=40)
    )
    params = queries.params(de=timezone.now() - timedelta(days=7))
    a2 = db.executar(queries.SQL_A2, params)[0]
    assert a2["total"] == 3


def test_filtro_por_cidade(carteira, londrina):
    a2 = db.executar(queries.SQL_A2, queries.params(cidade_id=londrina.pk))[0]
    assert a2["total"] == 1


def test_exclusao_logica_some_das_analises(carteira):
    Revendedora.objects.first().desativar()
    a2 = db.executar(queries.SQL_A2, queries.params())[0]
    assert a2["total"] == 3


def test_carteira_vazia_nao_quebra(carteira):
    # filtro sem resultados devolve linha com total 0
    params = queries.params(cidade_id=999999)
    a2 = db.executar(queries.SQL_A2, params)[0]
    assert a2["total"] == 0
    assert a2["pct"] is None
    # A1/A3/A4 com filtro impossível → vazio
    assert db.executar(queries.SQL_A1, params) == []
    assert db.executar(queries.SQL_A3, params) == []
    assert db.executar(queries.SQL_A4, params) == []


def test_autenticacao_de_gestor():
    """Smoke: a checagem de perfil usa o Django (não valida senha aqui)."""
    db.configura_django_auth()
    from django.contrib.auth import get_user_model

    assert get_user_model()._meta.db_table == "accounts_user"


def test_graficos_a_partir_das_queries_reais(carteira):
    """Query real → figura Plotly, sem erro de tipo (regressão A3/A4)."""
    a1 = graficos.a1(db.executar(queries.SQL_A1, queries.params()))
    a2 = graficos.a2(db.executar(queries.SQL_A2, queries.params())[0])
    a3 = graficos.a3(db.executar(queries.SQL_A3, queries.params()))
    a4 = graficos.a4(db.executar(queries.SQL_A4, queries.params()))

    assert len(a1.data) == 1 and a1.layout.yaxis.title.text is None
    assert a2.data[0].values == (3, 1)
    assert len(a3.data) == 1 and a3.layout.yaxis.title.text is None
    assert len(a4.data) == 1
    assert a4.layout.xaxis.title.text is None and a4.layout.yaxis.title.text is None
    for fig in (a1, a3, a4):
        hover = fig.data[0].hovertemplate
        assert hover and not re.search(r"(?:^|<br>)=", hover)

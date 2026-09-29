"""Testes de E6: as 4 páginas do Streamlit executam de ponta a ponta.

Usa `streamlit.testing.v1.AppTest` para pegar bugs que só estouram na página:
o plotly não era o único — A4 também quebrava com `list.drop(columns=...)`,
já que `db.executar` devolve `list[dict]` e não DataFrame.
"""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import db
from prospeccao.models import Cidade, ProdutoInteresse, RedeSocial
from prospeccao.seeds import PRODUTOS, REDES
from prospeccao.services import criar_revendedora

RAIZ = Path(__file__).resolve().parents[2]

PAGINAS = [
    "1_A1_cadastros_por_promotora.py",
    "2_A2_ja_revendem.py",
    "3_A3_marcas.py",
    "4_A4_interesse_produtos.py",
]

# transaction=True: a página abre conexão psycopg própria e precisa ver commits
pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture(autouse=True)
def aponta_analytics_para_o_banco_de_teste(monkeypatch, settings):
    cfg = settings.DATABASES["default"]
    senha = cfg.get("PASSWORD") or ""
    url = (
        f"postgres://{cfg['USER']}:{senha}"
        f"@{cfg.get('HOST') or 'localhost'}:{cfg.get('PORT') or 5432}/{cfg['NAME']}"
    )
    monkeypatch.setattr(db, "DATABASE_URL", url)


@pytest.fixture(autouse=True)
def carteira(django_user_model):
    """Catálogos + carteira mínima para as queries devolverem linha."""
    for ordem, nome in enumerate(PRODUTOS, start=1):
        ProdutoInteresse.objects.get_or_create(nome=nome, defaults={"ordem": ordem})
    for nome in REDES:
        RedeSocial.objects.get_or_create(nome=nome)

    promo = django_user_model.objects.create_user(
        email="pag@test.com", password="x", username="pag"
    )
    cidade = Cidade.objects.get_or_create(nome="Recife", uf="PE")[0]
    criar_revendedora(
        promotora=promo,
        dados={
            "nome_completo": "Ana Souza",
            "cidade": cidade,
            "vende_outras_marcas": True,
        },
        telefones=[{"numero": "81999998888"}],
        marcas=["Natura"],
        interesses=list(ProdutoInteresse.objects.values_list("id", flat=True))[:2],
    )
    return True


def _executa(pagina: str) -> AppTest:
    at = AppTest.from_file(RAIZ / "analytics" / "pages" / pagina, default_timeout=60)
    at.session_state["gestor"] = "gestor@test.com"
    at.run()
    return at


@pytest.mark.parametrize("pagina", PAGINAS)
def test_pagina_executa_sem_excecao(pagina):
    at = _executa(pagina)
    assert [str(exc.value) for exc in at.exception] == []
    assert at.title, "a página deve renderizar o título"


@pytest.mark.parametrize("pagina", PAGINAS)
def test_pagina_renderiza_grafico_e_tabela(pagina):
    """Não basta não explodir: o filtro padrão precisa chegar ao gráfico."""
    at = _executa(pagina)
    assert len(at.get("plotly_chart")) == 1
    assert len(at.get("dataframe")) >= 1


def test_a3_mostra_as_marcas_da_carteira():
    at = _executa("3_A3_marcas.py")
    texto = at.dataframe[0].value.to_string()
    assert "Natura" in texto


def test_a4_lista_as_categorias_sem_a_coluna_de_ordem():
    at = _executa("4_A4_interesse_produtos.py")
    colunas = list(at.dataframe[0].value.columns)
    assert "categoria" in colunas
    assert "ordem" not in colunas


@pytest.mark.parametrize("pagina", PAGINAS)
def test_pagina_oferece_exportacao_csv_e_pdf(pagina):
    """Cada análise precisa de CSV (dados) e PDF (relatório) — PRD fase 2."""
    at = _executa(pagina)
    assert [str(exc.value) for exc in at.exception] == []
    botoes = at.get("download_button")
    assert [botao.label for botao in botoes] == [
        "⬇️ Baixar CSV desta análise",
        "📄 Baixar PDF desta análise",
    ]


@pytest.mark.parametrize("pagina", PAGINAS)
def test_pagina_injeta_css_de_celular(pagina):
    """No celular as 3 colunas de KPI empilham em vez de espremer (brief §4)."""
    at = _executa(pagina)
    assert [str(exc.value) for exc in at.exception] == []
    assert any("max-width: 640px" in str(m.value) for m in at.markdown)


def test_home_autentica_gestor_pelo_formulario(django_user_model):
    """O login do analytics valida contra `auth_user` (RF-06.3) sem quebrar.

    Regressão do F3.5: `AxesBackend` exige um `request`, e a tela estourava
    `AxesBackendRequestParameterRequired` em vez de autenticar.
    """
    user = django_user_model.objects.create_user(
        email="gestor@app.com", password="Segredo123", username="gestor_app"
    )
    user.perfil.role = "gestor"
    user.perfil.save()

    at = AppTest.from_file(RAIZ / "analytics" / "Home.py", default_timeout=60)
    at.run()
    at.text_input[0].set_value("gestor@app.com")
    at.text_input[1].set_value("Segredo123")
    at.button[0].click()
    at.run()

    assert [str(exc.value) for exc in at.exception] == []
    assert at.session_state["gestor"] == "gestor@app.com"


def test_home_gera_o_relatorio_completo_a1_a4():
    at = AppTest.from_file(RAIZ / "analytics" / "Home.py", default_timeout=120)
    at.session_state["gestor"] = "gestor@test.com"
    at.run()
    assert [str(exc.value) for exc in at.exception] == []

    botao = next(b for b in at.button if b.label == "Gerar PDF com A1–A4")
    botao.click()
    at.run()

    assert [str(exc.value) for exc in at.exception] == []
    baixar = at.get("download_button")
    assert len(baixar) == 1
    assert "relatorio_completo" in baixar[0].label or baixar[0].label.startswith("📄")

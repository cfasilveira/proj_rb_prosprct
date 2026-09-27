"""Testes de E6: os gráficos A1–A4 constroem sem erro (plotly 7.x).

Regressão: `labels={"...": None}` fazia o plotly explodir com
`TypeError: unsupported operand type(s) for +: 'NoneType' and 'str'`
em `plotly/express/_core.py` (a chave do hover é o rótulo, não a coluna).
"""
import re

import analytics.graficos as graficos
import pytest

LINHAS_A1 = [
    {"promotora_nome": "Ana Souza", "cadastradas": 17, "ja_revendem": 10, "pct": 58.8},
    {"promotora_nome": "Beatriz Lima", "cadastradas": 16, "ja_revendem": 11, "pct": 68.8},
]

LINHA_A2 = {"total": 57, "ja_revendem": 42, "nao_revendem": 15, "pct": 73.7}

LINHAS_A3 = [
    {"marca": "Granado", "revendedoras": 17, "pct": 40.5},
    {"marca": "Mary Kay", "revendedoras": 16, "pct": 38.1},
    {"marca": "Natura", "revendedoras": 12, "pct": 28.6},
]

LINHAS_A4 = [
    {"categoria": "Cosméticos", "ordem": 1, "interessadas": 11, "pct": 19.3},
    {"categoria": "Vitaminas", "ordem": 2, "interessadas": 14, "pct": 24.6},
]

ROTULO_VAZIO = re.compile(r"(?:^|<br>)=")


def _hover(fig) -> str:
    return fig.data[0].hovertemplate or ""


def _titulo(eixo) -> str | None:
    return eixo.title.text if eixo.title is not None else None


def test_a1_constroi():
    fig = graficos.a1(LINHAS_A1)
    assert len(fig.data) == 1
    assert _titulo(fig.layout.xaxis) is None
    assert _titulo(fig.layout.yaxis) is None


def test_a2_donut_constroi():
    fig = graficos.a2(LINHA_A2)
    assert fig.data[0].values == (42, 15)
    assert fig.data[0].hole == 0.55


def test_a3_constroi_sem_typeerror():
    """Regressão do erro reportado em /A3_marcas."""
    fig = graficos.a3(LINHAS_A3)
    assert len(fig.data) == 1
    assert _titulo(fig.layout.yaxis) is None


def test_a3_hover_mantem_o_rotulo_da_marca():
    hover = _hover(graficos.a3(LINHAS_A3))
    assert "Marca=" in hover
    assert not ROTULO_VAZIO.search(hover)


def test_a4_constroi_sem_typeerror():
    """Regressão do erro reportado em /A4_interesse_produtos."""
    fig = graficos.a4(LINHAS_A4)
    assert len(fig.data) == 1
    assert _titulo(fig.layout.xaxis) is None
    assert _titulo(fig.layout.yaxis) is None


def test_a4_hover_mantem_o_rotulo_da_categoria():
    hover = _hover(graficos.a4(LINHAS_A4))
    assert "Categoria=" in hover
    assert not ROTULO_VAZIO.search(hover)


def test_a4_mostra_percentual_nas_barras():
    fig = graficos.a4(LINHAS_A4)
    assert "%{text:.0f}%" in fig.data[0].texttemplate


@pytest.mark.parametrize("construtor, linhas", [("a1", LINHAS_A1), ("a3", LINHAS_A3), ("a4", LINHAS_A4)])
def test_nenhum_rotulo_nulo_chega_ao_plotly(construtor, linhas):
    hover = _hover(getattr(graficos, construtor)(linhas))
    chaves = re.findall(r"([^<>=]+)=", hover)
    assert chaves and all(chave.strip() for chave in chaves)


def test_a3_com_pct_nulo_nao_quebra():
    """O SQL usa NULLIF: pct pode voltar None sem derrubar o gráfico."""
    fig = graficos.a3([{"marca": "X", "revendedoras": 1, "pct": None}])
    assert len(fig.data) == 1


def test_a1_com_pct_nulo_nao_quebra():
    fig = graficos.a1([{"promotora_nome": "Ana", "cadastradas": 1, "ja_revendem": 0, "pct": None}])
    assert len(fig.data) == 1

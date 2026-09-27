"""Construção dos gráficos das análises A1–A4.

Sem dependência de Streamlit — testáveis com pytest (mesma convenção de
`queries.py`). As páginas em `pages/` só montam a tela e chamam estas funções.
"""
import plotly.express as px
import plotly.graph_objects as go

# Escala da marca (docs/UI_UX_Brief.md): azul claro → azul institucional.
PALETA = ["#EAF1FD", "#1B4DB1"]


def a1(linhas: list[dict]):
    """Barras de revendedoras cadastradas por promotora."""
    fig = px.bar(
        linhas,
        x="promotora_nome",
        y="cadastradas",
        text="cadastradas",
        color="pct",
        color_continuous_scale=PALETA,
        labels={"promotora_nome": "Promotora", "cadastradas": "Cadastradas", "pct": "% já revendem"},
    )
    fig.update_layout(yaxis_title=None, xaxis_title=None, coloraxis_colorbar_title="% revende")
    return fig


def a2(linha: dict):
    """Rosca da conversão geral (já revendem × ainda não)."""
    donut = go.Figure(
        go.Pie(
            labels=["Já revendem", "Ainda não"],
            values=[linha["ja_revendem"], linha["nao_revendem"]],
            hole=0.55,
            marker_colors=["#128C5A", "#DADCE0"],
            textinfo="label+value",
        )
    )
    donut.update_layout(height=360, margin=dict(t=10, b=10))
    return donut


def a3(linhas: list[dict]):
    """Barras horizontais das marcas que a carteira já revende."""
    fig = px.bar(
        linhas,
        x="revendedoras",
        y="marca",
        orientation="h",
        text="revendedoras",
        color="pct",
        color_continuous_scale=PALETA,
        labels={"marca": "Marca", "revendedoras": "Revendedoras", "pct": "% das que já revendem"},
    )
    fig.update_layout(
        yaxis={"categoryorder": "total ascending"},
        yaxis_title=None,
        coloraxis_colorbar_title="%",
    )
    return fig


def a4(linhas: list[dict]):
    """Barras das categorias de produto de interesse."""
    fig = px.bar(
        linhas,
        x="categoria",
        y="interessadas",
        text="pct",
        color="interessadas",
        color_continuous_scale=PALETA,
        labels={"categoria": "Categoria", "interessadas": "Interessadas", "color": "Interessadas"},
    )
    fig.update_layout(yaxis_title=None, xaxis_title=None)
    fig.update_traces(texttemplate="%{text:.0f}%", textposition="outside")
    return fig

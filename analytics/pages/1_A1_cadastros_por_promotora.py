"""A1 — Quantidade de revendedoras cadastradas por promotora."""
import plotly.express as px
import streamlit as st

import db
import queries
from ui import kpi, protege_pagina, sidebar_filtros

protege_pagina()
st.title("A1 · Cadastros por promotora")

filtros = sidebar_filtros()
linhas = db.executar(queries.SQL_A1, filtros)

if not linhas:
    st.info("Nenhuma revendedora no período/filtro selecionado.")
    st.stop()

total = sum(linha["cadastradas"] for linha in linhas)
ja_revendem = sum(linha["ja_revendem"] for linha in linhas)
c1, c2, c3 = st.columns(3)
kpi(c1, "Cadastradas", total)
kpi(c2, "Já revendem", ja_revendem)
kpi(c3, "Promotoras ativas", len(linhas))

fig = px.bar(
    linhas,
    x="promotora_nome",
    y="cadastradas",
    text="cadastradas",
    color="pct",
    color_continuous_scale=["#EAF1FD", "#1B4DB1"],
    labels={"promotora_nome": "Promotora", "cadastradas": "Cadastradas", "pct": "% já revendem"},
)
fig.update_layout(yaxis_title=None, xaxis_title=None, coloraxis_colorbar_title="% revende")
st.plotly_chart(fig, use_container_width=True)

st.dataframe(linhas, use_container_width=True, hide_index=True)

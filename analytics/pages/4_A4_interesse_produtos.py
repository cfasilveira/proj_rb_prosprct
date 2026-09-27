"""A4 — Quais produtos as revendedoras têm interesse em revender."""
import plotly.express as px
import streamlit as st

import db
import queries
from ui import protege_pagina, sidebar_filtros

protege_pagina()
st.title("A4 · Interesse em produtos")

filtros = sidebar_filtros()
linhas = db.executar(queries.SQL_A4, filtros)

if not linhas:
    st.info("Nenhum interesse registrado no período/filtro selecionado.")
    st.stop()

fig = px.bar(
    linhas,
    x="categoria",
    y="interessadas",
    text="pct",
    color="interessadas",
    color_continuous_scale=["#EAF1FD", "#1B4DB1"],
    labels={"categoria": None, "interessadas": "Interessadas", "color": "Interessadas"},
)
fig.update_layout(yaxis_title=None, xaxis_title=None)
fig.update_traces(texttemplate="%{text:.0f}%", textposition="outside")
st.plotly_chart(fig, use_container_width=True)

st.dataframe(linhas.drop(columns=["ordem"]), use_container_width=True, hide_index=True)

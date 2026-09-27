"""A3 — Quais marcas essas revendedoras já revendem."""
import plotly.express as px
import streamlit as st

import db
import queries
from ui import protege_pagina, sidebar_filtros

protege_pagina()
st.title("A3 · Marcas já revendidas")

filtros = sidebar_filtros()
linhas = db.executar(queries.SQL_A3, filtros)

if not linhas:
    st.info("Nenhuma marca mapeada no período/filtro selecionado.")
    st.stop()

st.caption(f"{len(linhas)} marca(s) distinta(s) na carteira filtrada.")

fig = px.bar(
    linhas,
    x="revendedoras",
    y="marca",
    orientation="h",
    text="revendedoras",
    color="pct",
    color_continuous_scale=["#EAF1FD", "#1B4DB1"],
    labels={"marca": None, "revendedoras": "Revendedoras", "pct": "% das que já revendem"},
)
fig.update_layout(yaxis={"categoryorder": "total ascending"}, coloraxis_colorbar_title="%")
st.plotly_chart(fig, use_container_width=True)

st.dataframe(linhas, use_container_width=True, hide_index=True)

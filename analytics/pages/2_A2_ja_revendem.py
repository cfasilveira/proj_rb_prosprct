"""A2 — Das revendedoras cadastradas, quantas já revendem."""
import plotly.graph_objects as go
import streamlit as st

import db
import queries
from ui import kpi, protege_pagina, sidebar_filtros

protege_pagina()
st.title("A2 · Quantas já revendem")

filtros = sidebar_filtros()
linha = db.executar(queries.SQL_A2, filtros)[0]
por_cidade = db.executar(queries.SQL_A2_CIDADE, filtros)

if linha["total"] == 0:
    st.info("Nenhuma revendedora no período/filtro selecionado.")
    st.stop()

c1, c2, c3 = st.columns(3)
kpi(c1, "Total cadastrado", linha["total"])
kpi(c2, "Já revendem", linha["ja_revendem"], destaque=True)
kpi(c3, "Conversão", f'{linha["pct"] or 0}%')

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
st.plotly_chart(donut, use_container_width=True)

if por_cidade:
    st.subheader("Por cidade")
    st.dataframe(por_cidade, use_container_width=True, hide_index=True)

"""A3 — Quais marcas essas revendedoras já revendem."""
import streamlit as st

import db
import graficos
import queries
import relatorio
from ui import botao_csv, botao_pdf, protege_pagina, sidebar_filtros

protege_pagina()
st.title("A3 · Marcas já revendidas")

filtros = sidebar_filtros()
linhas = db.executar(queries.SQL_A3, filtros)

if not linhas:
    st.info("Nenhuma marca mapeada no período/filtro selecionado.")
    st.stop()

st.caption(f"{len(linhas)} marca(s) distinta(s) na carteira filtrada.")

fig = graficos.a3(linhas)
st.plotly_chart(fig, use_container_width=True)
st.dataframe(linhas, use_container_width=True, hide_index=True)

botao_csv(linhas, "a3_marcas_revendidas.csv")

botao_pdf(
    "A3 · Marcas já revendidas",
    [
        relatorio.texto(
            f"{len(linhas)} marca(s) distinta(s) na carteira filtrada. "
            "% calculado sobre as revendedoras que já revendem."
        ),
        relatorio.grafico("Marcas já revendidas", fig, "Fonte: prospeccao_revendedora_marca."),
        relatorio.tabela(
            "Detalhe por marca",
            ["Marca", "Revendedoras", "% das que já revendem"],
            [[m["marca"], m["revendedoras"], f'{m["pct"] or 0}%'] for m in linhas],
        ),
    ],
    "a3_marcas_revendidas.pdf",
    str(linhas),
)

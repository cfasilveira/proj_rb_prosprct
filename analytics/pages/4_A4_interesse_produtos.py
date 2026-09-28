"""A4 — Quais produtos as revendedoras têm interesse em revender."""
import streamlit as st

import db
import graficos
import queries
import relatorio
from ui import botao_csv, botao_pdf, protege_pagina, sidebar_filtros

protege_pagina()
st.title("A4 · Interesse em produtos")

filtros = sidebar_filtros()
linhas = db.executar(queries.SQL_A4, filtros)

if not linhas:
    st.info("Nenhum interesse registrado no período/filtro selecionado.")
    st.stop()

fig = graficos.a4(linhas)
st.plotly_chart(fig, use_container_width=True)

# db.executar devolve list[dict] (não DataFrame): projeta sem a ordem do seed.
tabela = [{chave: valor for chave, valor in linha.items() if chave != "ordem"} for linha in linhas]
st.dataframe(tabela, use_container_width=True, hide_index=True)

botao_csv(tabela, "a4_interesse_produtos.csv")

botao_pdf(
    "A4 · Interesse em produtos",
    [
        relatorio.grafico("Interesse em produtos", fig, "% = interessadas sobre a base filtrada."),
        relatorio.tabela(
            "Detalhe por categoria",
            ["Categoria", "Interessadas", "%"],
            [[p["categoria"], p["interessadas"], f'{p["pct"] or 0}%'] for p in linhas],
        ),
    ],
    "a4_interesse_produtos.pdf",
    str(linhas),
)

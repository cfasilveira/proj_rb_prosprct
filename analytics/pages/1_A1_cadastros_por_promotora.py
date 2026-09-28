"""A1 — Quantidade de revendedoras cadastradas por promotora."""
import streamlit as st

import db
import graficos
import queries
import relatorio
from ui import botao_csv, botao_pdf, kpi, protege_pagina, sidebar_filtros

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

fig = graficos.a1(linhas)
st.plotly_chart(fig, use_container_width=True)

st.dataframe(linhas, use_container_width=True, hide_index=True)

botao_csv(linhas, "a1_cadastros_por_promotora.csv")

botao_pdf(
    "A1 · Cadastros por promotora",
    [
        relatorio.kpis(
            [("Cadastradas", total), ("Já revendem", ja_revendem), ("Promotoras ativas", len(linhas))]
        ),
        relatorio.grafico(
            "Cadastros por promotora",
            fig,
            "Cor = % da promotora que já revende. Fonte: prospeccao_revendedora.",
        ),
        relatorio.tabela(
            "Detalhe por promotora",
            ["Promotora", "Cadastradas", "Já revendem", "% já revendem"],
            [
                [
                    linha["promotora_nome"],
                    linha["cadastradas"],
                    linha["ja_revendem"],
                    f'{linha["pct"] or 0}%',
                ]
                for linha in linhas
            ],
        ),
    ],
    "a1_cadastros_por_promotora.pdf",
    str(linhas),
)

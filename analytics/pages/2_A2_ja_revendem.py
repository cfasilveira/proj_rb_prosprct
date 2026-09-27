"""A2 — Das revendedoras cadastradas, quantas já revendem."""
import streamlit as st

import db
import graficos
import queries
import relatorio
from ui import botao_pdf, kpi, protege_pagina, sidebar_filtros

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

donut = graficos.a2(linha)
st.plotly_chart(donut, use_container_width=True)

if por_cidade:
    st.subheader("Por cidade")
    st.dataframe(por_cidade, use_container_width=True, hide_index=True)

blocos = [
    relatorio.kpis(
        [
            ("Total cadastrado", linha["total"]),
            ("Já revendem", linha["ja_revendem"]),
            ("Conversão", f'{linha["pct"] or 0}%'),
        ]
    ),
    relatorio.grafico(
        "Conversão geral",
        donut,
        "Fatias = revendedoras que já revendem × as que ainda não revendem.",
    ),
]
if por_cidade:
    blocos.append(
        relatorio.tabela(
            "Por cidade",
            ["Cidade", "Cadastradas", "Já revendem", "% já revendem"],
            [
                [c["cidade"], c["total"], c["ja_revendem"], f'{c["pct"] or 0}%']
                for c in por_cidade
            ],
        )
    )

botao_pdf("A2 · Quantas já revendem", blocos, "a2_ja_revendem.pdf",
          str(linha) + str(por_cidade))

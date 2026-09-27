"""Componentes compartilhados das páginas de análise."""
from datetime import UTC, datetime, timedelta

import streamlit as st

import db
import queries

PERIODOS = {"Sempre": None, "Hoje": 1, "7 dias": 7, "30 dias": 30}


def sidebar_filtros() -> dict:
    """Filtros laterais comuns → parâmetros das queries."""
    st.sidebar.header("Filtros")

    periodo = st.sidebar.selectbox("Período", list(PERIODOS.keys()))
    dias = PERIODOS[periodo]
    de = ate = None
    if dias:
        ate = datetime.now(UTC) + timedelta(days=1)
        de = datetime.now(UTC) - timedelta(days=dias)

    promotoras = db.opcoes_promotoras()
    nomes = ["Todas"] + [p["nome"] for p in promotoras]
    escolha = st.sidebar.selectbox("Promotora", nomes)
    promotora_id = next(
        (p["id"] for p in promotoras if p["nome"] == escolha), None
    ) if escolha != "Todas" else None

    cidades = db.opcoes_cidades()
    nomes_cidades = ["Todas"] + [c["nome"] for c in cidades]
    escolha_cidade = st.sidebar.selectbox("Cidade", nomes_cidades)
    cidade_id = next(
        (c["id"] for c in cidades if c["nome"] == escolha_cidade), None
    ) if escolha_cidade != "Todas" else None

    st.sidebar.caption(f"Período: {periodo.lower()} · {escolha} · {escolha_cidade}")
    return queries.params(de=de, ate=ate, promotora_id=promotora_id, cidade_id=cidade_id)


def kpi(coluna, rotulo: str, valor, destaque: bool = False):
    rotulo_html = f"<p style='margin:0;font-size:0.85rem;color:#5F6368'>{rotulo}</p>"
    cor = "#1B4DB1" if destaque else "#1A1A1A"
    valor_html = (
        f"<p style='margin:4px 0 0;font-size:2rem;font-weight:700;color:{cor}'>{valor}</p>"
    )
    coluna.markdown(f"<div style='padding:8px 0'>{rotulo_html}{valor_html}</div>",
                    unsafe_allow_html=True)


def protege_pagina():
    """Interrompe a página se não houver sessão de gestor."""
    if "gestor" not in st.session_state:
        st.warning("Faça login na página inicial para ver as análises.")
        st.page_link("Home.py", label="Ir para o login", icon="🔐")
        st.stop()

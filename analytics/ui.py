"""Componentes compartilhados das páginas de análise."""
from datetime import UTC, datetime, timedelta

import streamlit as st

import db
import queries
import relatorio

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

    rotulo = f"Período: {periodo.lower()} · {escolha} · {escolha_cidade}"
    st.session_state["rotulo_filtros"] = rotulo
    st.sidebar.caption(rotulo)
    return queries.params(de=de, ate=ate, promotora_id=promotora_id, cidade_id=cidade_id)


def botao_pdf(titulo: str, blocos: list[dict], arquivo: str, assinatura: str):
    """Botão de download do PDF desta página (PRD fase 2 — exportação).

    O PDF só é regenerado quando os dados mudam: kaleido + reportlab custam
    ~2s e não vale a pena a cada rerun do Streamlit.
    """
    subtitulo = st.session_state.get("rotulo_filtros", "Período: sempre · Todas · Todas")
    memo = st.session_state.setdefault("pdf_memo", {})
    chave = (titulo, subtitulo, assinatura)
    try:
        if memo.get("chave") != chave:
            memo["bytes"] = relatorio.gerar_pdf(titulo, subtitulo, blocos)
            memo["chave"] = chave
    except Exception as erro:  # kaleido/reportlab podem faltar no ambiente
        st.error(f"Não foi possível gerar o PDF: {erro}")
        return
    st.download_button(
        "📄 Baixar PDF desta análise",
        data=memo["bytes"],
        file_name=arquivo,
        mime="application/pdf",
        use_container_width=True,
    )


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

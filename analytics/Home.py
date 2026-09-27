"""RB Prospecta · Análises (Streamlit) — acesso restrito ao gestor (PRD RF-06)."""
import streamlit as st

import db

st.set_page_config(
    page_title="RB Prospecta · Análises",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "gestor" not in st.session_state:
    st.title("RB Prospecta · Análises")
    st.caption("Área restrita ao gestor do canal.")

    with st.form("login", clear_on_submit=False):
        email = st.text_input("E-mail", autocomplete="email")
        senha = st.text_input("Senha", type="password")
        enviado = st.form_submit_button("Entrar", use_container_width=True)
        if enviado:
            if db.autentica_gestor(email.strip().lower(), senha):
                st.session_state["gestor"] = email.strip().lower()
                st.rerun()
            else:
                st.error("Credenciais inválidas ou perfil sem acesso de gestor.")

    st.stop()

st.title("Análises da carteira")
st.caption(f"Conectado como {st.session_state['gestor']}")

st.page_link("pages/1_A1_cadastros_por_promotora.py",
             label="A1 · Cadastros por promotora", icon="1️⃣")
st.page_link("pages/2_A2_ja_revendem.py",
             label="A2 · Quantas já revendem", icon="2️⃣")
st.page_link("pages/3_A3_marcas.py",
             label="A3 · Marcas revendidas", icon="3️⃣")
st.page_link("pages/4_A4_interesse_produtos.py",
             label="A4 · Interesse em produtos", icon="4️⃣")

with st.sidebar:
    if st.button("Sair"):
        del st.session_state["gestor"]
        st.rerun()

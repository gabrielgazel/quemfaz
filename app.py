import streamlit as st

from db import init_responsaveis, init_observacoes_column, init_avisos

st.set_page_config(page_title="Tabela TUSS", page_icon=":material/table_rows:", layout="wide")

# ── Inicialização do banco (idempotente) ─────────────────────────────────────
init_responsaveis()
init_observacoes_column()
init_avisos()

# ── Navegação ─────────────────────────────────────────────────────────────────
inicio = st.Page(
    "pages/inicio.py",
    title="Início",
    icon=":material/campaign:",
    url_path="inicio",
    default=True,
)
consulta = st.Page(
    "pages/consulta.py",
    title="Consulta",
    icon=":material/table_rows:",
    url_path="consulta",
)
responsaveis = st.Page(
    "pages/responsaveis.py",
    title="Responsáveis",
    icon=":material/person_text:",
    url_path="responsaveis",
)

pg = st.navigation([inicio, consulta, responsaveis], position="top")
pg.run()
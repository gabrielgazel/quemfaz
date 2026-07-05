import streamlit as st

from db import init_responsaveis, init_observacoes_column

st.set_page_config(page_title="Tabela TUSS", page_icon=":material/table_rows:", layout="wide")

# ── Inicialização do banco (idempotente) ─────────────────────────────────────
init_responsaveis()
init_observacoes_column()

# ── Navegação ─────────────────────────────────────────────────────────────────
consulta = st.Page(
    "pages/consulta.py",
    title="Consulta",
    icon=":material/table_rows:",
    url_path="consulta",
    default=True,
)
responsaveis = st.Page(
    "pages/responsaveis.py",
    title="Responsáveis",
    icon=":material/person_text:",
    url_path="responsaveis",
)

pg = st.navigation([consulta, responsaveis], position="top")
pg.run()
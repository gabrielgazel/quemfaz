import streamlit as st

st.set_page_config(page_title="Tabela TUSS", page_icon=":material/table_rows:", layout="wide")

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
medicos = st.Page(
    "pages/medicos.py",
    title="Médicos",
    icon=":material/stethoscope:",
    url_path="medicos",
)

pg = st.navigation([inicio, consulta, medicos], position="sidebar")
pg.run()
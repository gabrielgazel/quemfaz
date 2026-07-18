import streamlit as st

st.set_page_config(page_title="Tabela TUSS", page_icon=":material/table_rows:", layout="wide")


def checar_login():
    """Bloqueia o acesso ao app até a senha correta ser informada."""
    if st.session_state.get("autenticado"):
        return True

    st.title("Tabela TUSS")
    with st.form("login_form"):
        senha = st.text_input("Senha de acesso", type="password")
        entrar = st.form_submit_button("Entrar")

    if entrar:
        senha_correta = st.secrets.get("auth", {}).get("senha")
        if senha_correta is None:
            st.error("Senha de acesso não configurada nos secrets do app (seção [auth]).")
        elif senha == senha_correta:
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("Senha incorreta.")

    return False


if not checar_login():
    st.stop()

with st.sidebar:
    if st.button("Sair", icon=":material/logout:", use_container_width=True):
        st.session_state["autenticado"] = False
        st.rerun()

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
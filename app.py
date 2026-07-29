import streamlit as st

st.set_page_config(page_title="QuemFAZ", page_icon=":material/table_rows:", layout="wide")

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

# Definição das Páginas
login_page = st.Page("pages/login.py", title="Entrar no Sistema", icon=":material/lock:", url_path="login")
avisos = st.Page("pages/avisos.py", title="Avisos", icon=":material/campaign:", url_path="avisos", default=True)
consulta = st.Page("pages/consulta.py", title="Consulta", icon=":material/table_rows:", url_path="consulta")
medicos = st.Page("pages/medicos.py", title="Médicos", icon=":material/stethoscope:", url_path="medicos")

# Roteamento Dinâmico
if not st.session_state["autenticado"]:
    # Quando não autenticado, apenas a página de login existe
    pg = st.navigation([login_page], position="hidden")
else:
    # Sem sidebar: o menu fica no topo, então o botão "Sair" é realocado
    # para uma linha própria acima da navegação.
    col_espaco, col_sair = st.columns([9, 1])
    with col_sair:
        if st.button("Sair", icon=":material/logout:", use_container_width=True):
            st.session_state["autenticado"] = False
            st.rerun()

    pg = st.navigation([avisos, consulta, medicos], position="top")

# Executa o app
pg.run()
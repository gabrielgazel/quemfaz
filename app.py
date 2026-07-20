import streamlit as st

st.set_page_config(page_title="Tabela TUSS", page_icon=":material/table_rows:", layout="wide")

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

# Definição das Páginas
login_page = st.Page("pages/login.py", title="Entrar no Sistema", icon=":material/lock:", url_path="login")
inicio = st.Page("pages/inicio.py", title="Início", icon=":material/campaign:", url_path="inicio", default=True)
consulta = st.Page("pages/consulta.py", title="Consulta", icon=":material/table_rows:", url_path="consulta")
medicos = st.Page("pages/medicos.py", title="Médicos", icon=":material/stethoscope:", url_path="medicos")

# Roteamento Dinâmico (Corrigido e simplificado)
if not st.session_state["autenticado"]:
    # Quando não autenticado, apenas a página de login existe e a barra lateral é ESCONDIDA
    pg = st.navigation([login_page], position="hidden")
else:
    # Quando autenticado, as páginas reais aparecem na barra lateral
    pg = st.navigation([inicio, consulta, medicos], position="sidebar")
    
    # Renderiza o botão de Sair na sidebar
    with st.sidebar:
        if st.button("Sair", icon=":material/logout:", use_container_width=True):
            st.session_state["autenticado"] = False
            st.rerun() # Atualiza o app instantaneamente, aplicando o 'position="hidden"'

# Executa o app
pg.run()
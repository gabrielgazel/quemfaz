import streamlit as st

# Configuração inicial da página
st.set_page_config(page_title="QuemFAZ", page_icon=":material/table_rows:", layout="wide")

# Garante que o estado de autenticação exista
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

# 1. Definição de TODAS as páginas usando st.Page
login_page = st.Page("pages/login.py", title="Entrar no Sistema", icon=":material/lock:", url_path="login")
avisos = st.Page("pages/avisos.py", title="Avisos", icon=":material/campaign:", url_path="avisos", default=True)
consulta = st.Page("pages/consulta.py", title="Consulta", icon=":material/table_rows:", url_path="consulta")
medicos = st.Page("pages/medicos.py", title="Médicos", icon=":material/stethoscope:", url_path="medicos")
logout_page = st.Page("pages/logout.py", title="Sair do Sistema", icon=":material/logout:", url_path="logout")


# 2. Roteamento Dinâmico
if not st.session_state["autenticado"]:
    # Quando não autenticado, apenas a página de login existe e o menu é oculto
    pg = st.navigation([login_page], position="hidden")
else:
    # Quando autenticado, passamos uma LISTA de páginas em vez de um dicionário.
    # Isso garante que todos os botões fiquem lado a lado na navbar principal.
    pg = st.navigation([avisos, consulta, medicos, logout_page], position="top")

# 3. Executa o app
pg.run()
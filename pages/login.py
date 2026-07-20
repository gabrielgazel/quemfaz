import streamlit as st

# Título principal da página limpa
st.set_page_config(page_title="Login - QuemFAZ", page_icon=":material/lock:", layout="centered")
st.title("Login")
st.write("Bem-vindo ao sistema de gerenciamento e consulta de médicos que executam ou não determinados exames da tabela TUSS.")

# 1. Definição do Modal (Dialog) de Login
@st.dialog("🔒 Autenticação Necessária")
def modal_login():
    st.write("Insira a senha de acesso para liberar os recursos do sistema.")
    
    # Criamos o formulário dentro do modal para capturar o "Enter"
    with st.form("formulario_login_modal", clear_on_submit=False):
        senha = st.text_input("Senha de acesso", type="password", placeholder="Sua senha aqui...")
        
        # O botão PRECISA ser o submit do formulário
        confirmar = st.form_submit_button("Confirmar", use_container_width=True, type="primary")

        if confirmar:
            # Busca a senha configurada nos secrets
            senha_correta = st.secrets.get("auth", {}).get("senha")
            
            if senha_correta is None:
                st.error("Senha de acesso não configurada nos secrets do app (seção [auth]).")
            elif senha == senha_correta:
                st.session_state["autenticado"] = True
                st.success("Acesso liberado!")
                st.rerun()
            else:
                st.error("Senha incorreta. Tente novamente.")

# 2. Layout da página limpa com o botão para abrir o modal
st.divider()

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("Acessar o Sistema", icon=":material/login:", use_container_width=True, type="primary"):
        modal_login()
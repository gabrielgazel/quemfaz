import time

import streamlit as st

# Título principal da página limpa
st.title("Login")
st.write("Bem-vindo ao sistema de gerenciamento e consulta de médicos que executam ou não determinados exames da tabela TUSS.")

st.divider()

# Formulário de login direto na página (sem modal), reduz uma rodada de rerun
# em relação ao fluxo antigo com @st.dialog.
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.write("Insira a senha de acesso para liberar os recursos do sistema.")

    with st.form("formulario_login", clear_on_submit=False):
        senha = st.text_input("Senha de acesso", type="password", placeholder="Sua senha aqui...")
        confirmar = st.form_submit_button(
            "Acessar o Sistema", icon=":material/login:", use_container_width=True, type="primary"
        )

        if confirmar:
            senha_correta = st.secrets.get("auth", {}).get("senha")

            if senha_correta is None:
                st.error("Senha de acesso não configurada nos secrets do app (seção [auth]).")
            else:
                with st.spinner("Verificando credenciais..."):
                    time.sleep(1)  # simula o carregamento da autenticação

                if senha == senha_correta:
                    st.session_state["autenticado"] = True
                    st.rerun()
                else:
                    st.error("Senha incorreta. Tente novamente.")
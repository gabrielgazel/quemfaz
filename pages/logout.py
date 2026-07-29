import streamlit as st

# 1. Altera o status de autenticação para False
st.session_state["autenticado"] = False

# 2. Reinicia a aplicação imediatamente. 
# Isso fará com que o st.navigation principal avalie o if/else novamente 
# e mostre apenas a página de login.
st.rerun()
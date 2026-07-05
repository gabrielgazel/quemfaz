import streamlit as st

from db import get_responsaveis, add_responsavel, remove_responsavel

st.markdown("### :material/person_text: Responsáveis")
st.caption("Cadastre e gerencie a lista de pessoas que podem ser atribuídas como \"quem faz\" nos procedimentos.")

st.divider()

responsaveis = get_responsaveis()

col_form, col_lista = st.columns(2)

with col_form:
    st.markdown("**Adicionar**")
    novo = st.text_input("Nome", key="input_novo_resp", placeholder="Ex: Dr. João Silva")
    if st.button(" Adicionar", icon=":material/add_2:", use_container_width=True, key="btn_add"):
        ok, msg = add_responsavel(novo)
        st.success(msg) if ok else st.warning(msg)
        st.rerun()

    if responsaveis:
        st.markdown("**Remover**")
        remover = st.selectbox("", options=responsaveis, key="sel_remover", label_visibility="collapsed")
        if st.button(" Remover", icon=":material/delete:", use_container_width=True, key="btn_rem", type="primary"):
            remove_responsavel(remover)
            st.rerun()

with col_lista:
    st.markdown("**Lista atual**")
    if responsaveis:
        tags = "".join(f'<span class="resp-tag">{r}</span>' for r in responsaveis)
        st.markdown(tags, unsafe_allow_html=True)
    else:
        st.caption("Nenhum responsável cadastrado ainda.")
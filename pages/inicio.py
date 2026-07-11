import streamlit as st

from db import get_avisos, add_aviso, update_aviso, remove_aviso

# ── Header ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="tuss-header">
  <h1>Mural de Avisos</h1>
  <p>Informações e comunicados importantes sobre a gestão dos procedimentos TUSS</p>
</div>
""", unsafe_allow_html=True)

st.divider()

# ── Estado dos diálogos ───────────────────────────────────────────────────────
if "dialog_editar_aviso_id" not in st.session_state:
    st.session_state["dialog_editar_aviso_id"] = None

# ── Diálogo: novo aviso ───────────────────────────────────────────────────────
@st.dialog("Novo aviso", width="large")
def dialog_novo_aviso():
    titulo = st.text_input("Título", key="novo_aviso_titulo", placeholder="Ex: Atualização de escala")
    texto = st.text_area(
        "Mensagem", key="novo_aviso_texto", height=150,
        placeholder="Escreva o comunicado que aparecerá no mural...",
    )
    fixado = st.checkbox("Fixar no topo do mural", key="novo_aviso_fixado")

    col_ok, col_cancel = st.columns(2)
    with col_ok:
        if st.button("Publicar", icon=":material/send:", type="primary", use_container_width=True):
            ok, msg = add_aviso(titulo, texto, fixado)
            if ok:
                st.toast(msg, icon=":material/campaign:")
                st.rerun()
            else:
                st.warning(msg)
    with col_cancel:
        if st.button("Cancelar", use_container_width=True):
            st.rerun()

# ── Diálogo: editar/excluir aviso ────────────────────────────────────────────
@st.dialog("Editar aviso", width="large")
def dialog_editar_aviso(aviso: dict):
    titulo = st.text_input("Título", value=aviso["titulo"], key=f"edit_titulo_{aviso['id']}")
    texto = st.text_area(
        "Mensagem", value=aviso["texto"], height=150, key=f"edit_texto_{aviso['id']}"
    )
    fixado = st.checkbox("Fixar no topo do mural", value=aviso["fixado"], key=f"edit_fixado_{aviso['id']}")

    col_salvar, col_excluir, col_cancel = st.columns(3)
    with col_salvar:
        if st.button("Salvar", icon=":material/save:", type="primary", use_container_width=True):
            ok, msg = update_aviso(aviso["id"], titulo, texto, fixado)
            if ok:
                st.toast(msg, icon=":material/check_circle:")
                st.session_state["dialog_editar_aviso_id"] = None
                st.rerun()
            else:
                st.warning(msg)
    with col_excluir:
        if st.button("Excluir", icon=":material/delete:", use_container_width=True):
            remove_aviso(aviso["id"])
            st.toast("Aviso removido do mural.", icon=":material/delete:")
            st.session_state["dialog_editar_aviso_id"] = None
            st.rerun()
    with col_cancel:
        if st.button("Cancelar", use_container_width=True):
            st.session_state["dialog_editar_aviso_id"] = None
            st.rerun()

# ── Ação: novo aviso ──────────────────────────────────────────────────────────
col_espaco, col_botao = st.columns([5, 1])
with col_botao:
    if st.button("Novo aviso", icon=":material/add_circle:", use_container_width=True, type="primary"):
        dialog_novo_aviso()

# Reabre o diálogo de edição se um aviso estiver selecionado
if st.session_state["dialog_editar_aviso_id"] is not None:
    avisos_atuais = get_avisos()
    aviso_sel = next(
        (a for a in avisos_atuais if a["id"] == st.session_state["dialog_editar_aviso_id"]),
        None,
    )
    if aviso_sel:
        dialog_editar_aviso(aviso_sel)
    else:
        st.session_state["dialog_editar_aviso_id"] = None

st.write("")

# ── Mural ──────────────────────────────────────────────────────────────────
avisos = get_avisos()

if not avisos:
    st.info(
        "Nenhum aviso publicado ainda. Use o botão \"Novo aviso\" para começar o mural.",
        icon=":material/campaign:",
    )
else:
    for aviso in avisos:
        with st.container(border=True):
            col_texto, col_acao = st.columns([8, 1])

            with col_texto:
                if aviso["fixado"]:
                    st.markdown(f"##### :material/push_pin: {aviso['titulo']}")
                else:
                    st.markdown(f"##### {aviso['titulo']}")
                st.caption(aviso["criado_em"])
                st.write(aviso["texto"])

            with col_acao:
                if st.button(
                    "", icon=":material/edit:", key=f"btn_edit_aviso_{aviso['id']}",
                    use_container_width=True,
                ):
                    st.session_state["dialog_editar_aviso_id"] = aviso["id"]
                    st.rerun()
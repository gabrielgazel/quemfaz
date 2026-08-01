import streamlit as st

from db import (
    get_especialidades,
    get_fluxos,
    add_fluxo,
    update_fluxo,
    remove_fluxo,
    save_especialidade_fluxo,
)

st.title("Especialidades")
st.caption("Consulte para onde encaminhar cada demanda, de acordo com a especialidade.")
st.divider()


@st.dialog("Fluxo da especialidade")
def modal_especialidade(especialidade: dict):
    st.markdown(f"**{especialidade['nome']}**  ·  código {especialidade['codigo']}")

    fluxos = get_fluxos()
    opcoes = ["Sem fluxo definido"] + [f["nome"] for f in fluxos]
    indice_atual = 0
    if especialidade["fluxo_id"] is not None:
        for i, f in enumerate(fluxos):
            if f["id"] == especialidade["fluxo_id"]:
                indice_atual = i + 1
                break

    escolha = st.selectbox("Fluxo de trabalho", options=opcoes, index=indice_atual)

    if st.button("Salvar", type="primary", use_container_width=True):
        novo_fluxo_id = None
        if escolha != "Sem fluxo definido":
            novo_fluxo_id = next(f["id"] for f in fluxos if f["nome"] == escolha)
        ok, msg = save_especialidade_fluxo(especialidade["codigo"], novo_fluxo_id)
        if ok:
            st.rerun()
        else:
            st.error(msg)


@st.dialog("Fluxo de trabalho")
def modal_fluxo(fluxo: dict | None = None):
    nome = st.text_input("Nome", value=fluxo["nome"] if fluxo else "")
    descricao = st.text_area(
        "Descrição",
        value=fluxo["descricao"] if fluxo else "",
        placeholder="Ex: Agendar diretamente pelo sistema iClinic.",
    )

    col_salvar, col_excluir = st.columns([3, 1])
    with col_salvar:
        if st.button("Salvar", type="primary", use_container_width=True):
            if fluxo:
                ok, msg = update_fluxo(fluxo["id"], nome, descricao)
            else:
                ok, msg = add_fluxo(nome, descricao)
            if ok:
                st.rerun()
            else:
                st.error(msg)
    with col_excluir:
        if fluxo and st.button("Excluir", use_container_width=True):
            ok, msg = remove_fluxo(fluxo["id"])
            if ok:
                st.rerun()
            else:
                st.error(msg)


# ── Busca de especialidades ──────────────────────────────────────────────────

busca = st.text_input(
    "Buscar especialidade",
    placeholder="Digite o nome ou código da especialidade...",
    icon=":material/search:",
)

especialidades = get_especialidades(busca)

if not especialidades:
    if busca:
        st.info("Nenhuma especialidade encontrada para essa busca.")
    else:
        st.info("Nenhuma especialidade cadastrada ainda.")
else:
    colunas = st.columns(3)
    for i, esp in enumerate(especialidades):
        with colunas[i % 3]:
            with st.container(border=True):
                st.markdown(f"### {esp['nome']}")
                st.caption(f"Código {esp['codigo']}")
                if esp["fluxo_nome"]:
                    st.markdown(f":material/alt_route: **Fluxo:** {esp['fluxo_nome']}")
                    if esp["fluxo_descricao"]:
                        st.caption(esp["fluxo_descricao"])
                else:
                    st.markdown(":material/alt_route: **Fluxo:** _sem fluxo definido_")

                if st.button("Editar fluxo", key=f"editar_esp_{esp['codigo']}", use_container_width=True):
                    modal_especialidade(esp)

st.divider()

# ── Gestão de fluxos de trabalho ─────────────────────────────────────────────

with st.expander(":material/alt_route: Gerenciar fluxos de trabalho"):
    if st.button("Novo fluxo", icon=":material/add:"):
        modal_fluxo()

    fluxos = get_fluxos()
    if not fluxos:
        st.info("Nenhum fluxo de trabalho cadastrado ainda.")
    else:
        for fluxo in fluxos:
            col_info, col_editar = st.columns([5, 1])
            with col_info:
                st.markdown(f"**{fluxo['nome']}**")
                if fluxo["descricao"]:
                    st.caption(fluxo["descricao"])
            with col_editar:
                if st.button("Editar", key=f"editar_fluxo_{fluxo['id']}", use_container_width=True):
                    modal_fluxo(fluxo)
            st.divider()
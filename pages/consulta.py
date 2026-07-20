import streamlit as st

from db import get_nomes_medicos, fetch_all, save_quem_faz, save_observacoes, save_tem_preparo

# ── Header ──────────────────────────────────────────────────────────────────
st.title("Consultar exames")
st.write("Pesquise por nome, código TUSS, preparo ou médico responsável")

st.divider()

# ── Filtros (embutidos na página) ────────────────────────────────────────────
with st.container(border=True):
    st.markdown("### :material/filter_list: Filtros")
    st.divider()

    col_busca, col_prep, col_quem = st.columns([2, 1, 2])

    with col_busca:
        search = st.text_input("Nome ou Código TUSS", placeholder="Ex: Ressonância, 41101227...")

    with col_prep:
        filtro_prep = st.selectbox("Preparo", ["Todos", "Com preparo", "Sem preparo"])

    with col_quem:
        nomes_medicos = get_nomes_medicos()

        st.markdown("**Quem faz**")
        if nomes_medicos:
            filtro_quem = st.multiselect(
                "Quem faz",
                options=nomes_medicos,
                default=[],
                placeholder="Todos os médicos",
                label_visibility="collapsed",
            )
        else:
            st.caption("Nenhum médico cadastrado ainda.")
            st.page_link("pages/medicos.py", label="Cadastrar médicos", icon=":material/person_add:")
            filtro_quem = []

st.write("")

# ── Só busca/exibe algo se algum filtro foi de fato aplicado ────────────────
algum_filtro_aplicado = bool(search) or filtro_prep != "Todos" or bool(filtro_quem)

if not algum_filtro_aplicado:
    st.info(
        "Use os filtros acima para pesquisar por nome, código TUSS, "
        "preparo ou médico responsável.",
        icon=":material/search:",
    )
    st.stop()

df = fetch_all(search, filtro_prep, filtro_quem if filtro_quem else None)

if df.empty:
    st.warning("Nenhum resultado encontrado para os filtros aplicados.")
    st.stop()

st.markdown(f"**{len(df)} procedimento(s) encontrado(s)**")
st.write("")

# ── Modal de edição ───────────────────────────────────────────────────────────
@st.dialog("Editar procedimento")
def modal_editar(row, nomes_medicos):
    st.caption(row["codigo"])
    st.markdown(f"**{row['nome']}**")

    quem_faz_atual = [q.strip() for q in (row["quem_faz"] or "").split(",") if q.strip()]
    # Garante que nomes já salvos, mas removidos da página Médicos, continuem
    # aparecendo como opção (para não perder o dado silenciosamente).
    opcoes = sorted(set(nomes_medicos) | set(quem_faz_atual))

    if not opcoes:
        st.caption("Nenhum médico cadastrado ainda.")
        st.page_link("pages/medicos.py", label="Cadastrar médicos", icon=":material/person_add:")

    medicos_selecionados = st.multiselect(
        "Quem faz",
        options=opcoes,
        default=quem_faz_atual,
        placeholder="Selecione o(s) médico(s) responsável(is)",
    )
    tem_preparo = st.checkbox("Tem preparo", value=bool(row["tem_preparo"]))
    observacoes = st.text_area("Observações", value=row["observacoes"] or "", height=100)

    if st.button("Salvar", type="primary", use_container_width=True, icon=":material/save:"):
        save_quem_faz(row["codigo"], medicos_selecionados)
        save_tem_preparo(row["codigo"], tem_preparo)
        save_observacoes(row["codigo"], observacoes)
        st.toast("Procedimento atualizado.", icon=":material/check_circle:")
        st.rerun()

# ── Exibição do resultado em cards (sem tabela/dataframe) ────────────────────
for _, row in df.iterrows():
    with st.container(border=True):
        col_cod, col_nome, col_prep = st.columns([1, 4, 1])

        with col_cod:
            st.caption("Código TUSS")
            st.markdown(f"**{row['codigo']}**")

        with col_nome:
            st.caption("Procedimento")
            st.markdown(f"**{row['nome']}**")

        with col_prep:
            if row["tem_preparo"]:
                st.markdown(":material/error: **Tem preparo**")
            else:
                st.markdown(":material/check_circle: Sem preparo")

        quem_faz = [q.strip() for q in (row["quem_faz"] or "").split(",") if q.strip()]
        if quem_faz:
            st.markdown(":material/person: **Quem faz:** " + ", ".join(quem_faz))
        else:
            st.caption(":material/person_off: Nenhum médico definido")

        if row["observacoes"]:
            st.markdown(f":material/edit_note: **Observações:** {row['observacoes']}")

        st.write("")
        if st.button(
            "Editar", key=f"editar_{row['codigo']}", icon=":material/edit:",
            use_container_width=True,
        ):
            modal_editar(row, nomes_medicos)
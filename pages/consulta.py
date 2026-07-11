import streamlit as st

from db import get_responsaveis, fetch_all

# ── Header ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="tuss-header">
  <h1>Tabela TUSS — Gestão de Exames</h1>
  <p>Pesquise um procedimento para ver preparo, responsável e observações</p>
</div>
""", unsafe_allow_html=True)

st.divider()

# ── Sidebar: filtros ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### :material/filter_list: Filtros")
    st.divider()

    search      = st.text_input("Nome ou Código TUSS", placeholder="Ex: Ressonância, 41101227...")
    filtro_prep = st.selectbox("Preparo", ["Todos", "Com preparo", "Sem preparo"])

    responsaveis = get_responsaveis()

    st.markdown("**Quem faz**")
    if responsaveis:
        filtro_quem = st.multiselect(
            "Quem faz",
            options=responsaveis,
            default=[],
            placeholder="Todos os responsáveis",
            label_visibility="collapsed",
        )
    else:
        st.caption("Nenhum responsável cadastrado ainda.")
        st.page_link("pages/responsaveis.py", label="Cadastrar responsáveis", icon=":material/person_add:")
        filtro_quem = []

# ── Só busca/exibe algo se algum filtro foi de fato aplicado ────────────────
algum_filtro_aplicado = bool(search) or filtro_prep != "Todos" or bool(filtro_quem)

if not algum_filtro_aplicado:
    st.info(
        "Use os filtros na barra lateral para pesquisar por nome, código TUSS, "
        "preparo ou responsável.",
        icon=":material/search:",
    )
    st.stop()

df = fetch_all(search, filtro_prep, filtro_quem if filtro_quem else None)

if df.empty:
    st.warning("Nenhum resultado encontrado para os filtros aplicados.")
    st.stop()

st.markdown(f"**{len(df)} procedimento(s) encontrado(s)**")
st.write("")

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
            st.caption(":material/person_off: Nenhum responsável definido")

        if row["observacoes"]:
            st.markdown(f":material/edit_note: **Observações:** {row['observacoes']}")
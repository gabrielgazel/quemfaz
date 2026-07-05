import streamlit as st

from db import get_conn, get_responsaveis, fetch_all, save_quem_faz, save_observacoes, count_stats

# ── Modal de edição (st.dialog) ──────────────────────────────────────────────

@st.dialog("Editar procedimento", width="large")
def abrir_dialogo_edicao(row):
    """Modal para editar 'Quem faz', 'Tem preparo' e 'Observações' de um procedimento."""
    codigo    = row["codigo"]
    nome_proc = row["nome"]

    atuais_str = row["quem_faz"] or ""
    atuais     = [r.strip() for r in atuais_str.split(",") if r.strip()]

    st.caption(f"Código TUSS: **{codigo}**")
    st.markdown(f"#### {nome_proc}")

    responsaveis = get_responsaveis()

    col_quem, col_prep = st.columns([3, 1])

    with col_quem:
        if not responsaveis:
            st.warning("Cadastre responsáveis na página **Responsáveis** antes de atribuí-los.")
            selecionados = atuais
        else:
            selecionados = st.multiselect(
                ":material/person: Quem faz",
                options=responsaveis,
                default=[r for r in atuais if r in responsaveis],
                placeholder="Selecione um ou mais responsáveis...",
                key=f"multi_quem_{codigo}",
            )

    with col_prep:
        tem_preparo = st.checkbox(
            ":material/error: Tem preparo?",
            value=bool(row["tem_preparo"]),
            key=f"chk_prep_{codigo}",
        )

    observacoes_texto = st.text_area(
        ":material/edit_note: Observações",
        value=row["observacoes"] or "",
        placeholder="Anotações sobre este exame...",
        key=f"obs_{codigo}",
        height=100,
    )

    col_ap, col_lp, col_fe = st.columns(3)
    with col_ap:
        if st.button("Salvar", type="primary", use_container_width=True, key="btn_aplicar_dialog"):
            save_quem_faz(codigo, selecionados)
            save_observacoes(codigo, observacoes_texto)
            with get_conn() as conn:
                conn.execute("UPDATE tuss_exames SET tem_preparo=? WHERE codigo=?",
                             (int(tem_preparo), codigo))
                conn.commit()
            st.toast("Alterações salvas!", icon=":material/check:")
            st.rerun()
    with col_lp:
        if st.button("Limpar quem faz", use_container_width=True, key="btn_limpar_dialog"):
            save_quem_faz(codigo, [])
            st.rerun()
    with col_fe:
        if st.button("Fechar", use_container_width=True, key="btn_fechar_dialog"):
            st.rerun()

# ── Header ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="tuss-header">
  <h1>Tabela TUSS — Gestão de Exames</h1>
  <p>Consulte e edite as informações de preparo e responsável pelos procedimentos</p>
</div>
""", unsafe_allow_html=True)

st.divider()

# ── Sidebar ──────────────────────────────────────────────────────────────────
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

# ── Métricas ─────────────────────────────────────────────────────────────────
total, c_prep, c_quem_stat = count_stats()
c1, c2, c3, c4 = st.columns(4)
c1.metric(":material/assignment: Total de procedimentos", total)
c2.metric(":material/check_alert: Com preparo definido", c_prep)
c3.metric(":material/person_check: Com responsável definido", c_quem_stat)
c4.metric(":material/hourglass_top: Pendentes de revisão", total - max(c_prep, c_quem_stat))

st.divider()

# ── Tabela ───────────────────────────────────────────────────────────────────
df = fetch_all(search, filtro_prep, filtro_quem if filtro_quem else None)

if df.empty:
    st.warning("Nenhum resultado encontrado para os filtros aplicados.")
    st.stop()

st.markdown(
    f"**{len(df)} procedimento(s) encontrado(s)** — "
    "clique em uma linha para editar *Quem faz* e *Tem preparo*."
)

# Formata tem_preparo para exibição
df_display = df.copy()
df_display["tem_preparo"] = df_display["tem_preparo"].map({True: "Sim", False: "—"})

event = st.dataframe(
    df_display,
    use_container_width=True,
    height=480,
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row",
    column_config={
        "codigo":      st.column_config.TextColumn("Código TUSS",         width="small"),
        "nome":        st.column_config.TextColumn("Nome do Procedimento", width="large"),
        "quem_faz":    st.column_config.TextColumn("Quem faz",         width="medium"),
        "tem_preparo": st.column_config.TextColumn("Tem preparo?",      width="small"),
        "observacoes": st.column_config.TextColumn("Observações",      width="large"),
    },
    key="tuss_table",
)

st.divider()

# ── Painel de edição (abre modal via st.dialog) ──────────────────────────────
if "dialog_last_codigo" not in st.session_state:
    st.session_state.dialog_last_codigo = None

selection = event.selection.rows if event and event.selection else []

if not selection:
    st.session_state.dialog_last_codigo = None
    st.info("Selecione uma linha na tabela para editar o procedimento.", icon=":material/info:")
else:
    idx       = selection[0]
    row       = df.iloc[idx]
    codigo    = row["codigo"]
    nome_proc = row["nome"]

    col_info, col_btn = st.columns([4, 1])
    with col_info:
        st.success(f"Selecionado: **{nome_proc}** ({codigo})", icon=":material/check_circle:")
    with col_btn:
        reabrir = st.button(
            "Editar",
            icon=":material/edit:",
            use_container_width=True,
            key="btn_reabrir_dialog",
        )

    # Abre o modal automaticamente ao selecionar uma nova linha, ou quando o
    # botão "Editar" é clicado (ex.: reabrir após fechar/dispensar o modal).
    if reabrir or codigo != st.session_state.dialog_last_codigo:
        st.session_state.dialog_last_codigo = codigo
        abrir_dialogo_edicao(row)
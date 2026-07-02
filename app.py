import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="Tabela TUSS", page_icon=":material/table_rows:", layout="wide")



DB_PATH = "tuss.db"

# ── Banco de dados ──────────────────────────────────────────────────────────

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_responsaveis():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS responsaveis (
                id   INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE
            )
        """)
        conn.commit()

def init_observacoes_column():
    """Garante que a coluna 'observacoes' exista na tabela tuss_exames."""
    with get_conn() as conn:
        cols = [c[1] for c in conn.execute("PRAGMA table_info(tuss_exames)").fetchall()]
        if "observacoes" not in cols:
            conn.execute("ALTER TABLE tuss_exames ADD COLUMN observacoes TEXT DEFAULT ''")
            conn.commit()

def get_responsaveis() -> list[str]:
    with get_conn() as conn:
        rows = conn.execute("SELECT nome FROM responsaveis ORDER BY nome").fetchall()
    return [r[0] for r in rows]

def add_responsavel(nome: str):
    nome = nome.strip()
    if not nome:
        return False, "Nome não pode ser vazio."
    with get_conn() as conn:
        try:
            conn.execute("INSERT INTO responsaveis (nome) VALUES (?)", (nome,))
            conn.commit()
            return True, f'"{nome}" adicionado.'
        except sqlite3.IntegrityError:
            return False, f'"{nome}" já existe na lista.'

def remove_responsavel(nome: str):
    with get_conn() as conn:
        conn.execute("DELETE FROM responsaveis WHERE nome = ?", (nome,))
        conn.commit()

def fetch_all(search="", filtro_preparo="Todos", filtro_quem=None):
    query = "SELECT codigo, nome, quem_faz, tem_preparo, observacoes FROM tuss_exames WHERE 1=1"
    params = []
    if search:
        query += " AND (codigo LIKE ? OR nome LIKE ?)"
        params += [f"%{search}%", f"%{search}%"]
    if filtro_preparo == "Com preparo":
        query += " AND tem_preparo = 1"
    elif filtro_preparo == "Sem preparo":
        query += " AND tem_preparo = 0"
    if filtro_quem:
        # Filtra linhas que contenham QUALQUER um dos responsáveis selecionados
        cond = " OR ".join(["quem_faz LIKE ?" for _ in filtro_quem])
        query += f" AND ({cond})"
        params += [f"%{r}%" for r in filtro_quem]
    query += " ORDER BY nome"
    with get_conn() as conn:
        df = pd.read_sql_query(query, conn, params=params)
    df["tem_preparo"] = df["tem_preparo"].astype(bool)
    df["observacoes"] = df["observacoes"].fillna("")
    return df


def save_quem_faz(codigo: str, responsaveis_selecionados: list[str]):
    """Salva a lista de responsáveis de um procedimento (separados por vírgula)."""
    valor = ", ".join(responsaveis_selecionados)
    with get_conn() as conn:
        conn.execute(
            "UPDATE tuss_exames SET quem_faz=? WHERE codigo=?",
            (valor, codigo),
        )
        conn.commit()

def save_observacoes(codigo: str, texto: str):
    """Salva o texto de observações de um procedimento."""
    with get_conn() as conn:
        conn.execute(
            "UPDATE tuss_exames SET observacoes=? WHERE codigo=?",
            (texto, codigo),
        )
        conn.commit()

def count_stats():
    with get_conn() as conn:
        total     = conn.execute("SELECT COUNT(*) FROM tuss_exames").fetchone()[0]
        c_preparo = conn.execute("SELECT COUNT(*) FROM tuss_exames WHERE tem_preparo=1").fetchone()[0]
        c_quem    = conn.execute("SELECT COUNT(*) FROM tuss_exames WHERE quem_faz != '' AND quem_faz IS NOT NULL").fetchone()[0]
    return total, c_preparo, c_quem

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
            st.warning("Cadastre responsáveis no menu lateral antes de atribuí-los.")
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

# ── Inicialização ───────────────────────────────────────────────────────────
init_responsaveis()
init_observacoes_column()

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
        filtro_quem = []

    st.divider()
    st.markdown("### :material/person_text: Responsáveis")

    with st.expander("Gerenciar lista", expanded=False):
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

            st.markdown("**Lista atual**")
            tags = "".join(f'<span class="resp-tag">{r}</span>' for r in responsaveis)
            st.markdown(tags, unsafe_allow_html=True)

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
import sqlite3
import pandas as pd

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

def init_avisos():
    """Cria a tabela do mural de avisos, se ainda não existir."""
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS avisos (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo    TEXT NOT NULL,
                texto     TEXT NOT NULL,
                fixado    INTEGER NOT NULL DEFAULT 0,
                criado_em TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
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


# ── Mural de avisos ──────────────────────────────────────────────────────────

def get_avisos() -> list[dict]:
    """Retorna todos os avisos, fixados primeiro e depois por data (mais recente primeiro)."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, titulo, texto, fixado, criado_em FROM avisos "
            "ORDER BY fixado DESC, criado_em DESC, id DESC"
        ).fetchall()
    return [
        {"id": r[0], "titulo": r[1], "texto": r[2], "fixado": bool(r[3]), "criado_em": r[4]}
        for r in rows
    ]

def add_aviso(titulo: str, texto: str, fixado: bool = False):
    titulo = titulo.strip()
    texto = texto.strip()
    if not titulo or not texto:
        return False, "Título e mensagem são obrigatórios."
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO avisos (titulo, texto, fixado) VALUES (?, ?, ?)",
            (titulo, texto, int(fixado)),
        )
        conn.commit()
    return True, "Aviso publicado no mural."

def update_aviso(aviso_id: int, titulo: str, texto: str, fixado: bool):
    titulo = titulo.strip()
    texto = texto.strip()
    if not titulo or not texto:
        return False, "Título e mensagem são obrigatórios."
    with get_conn() as conn:
        conn.execute(
            "UPDATE avisos SET titulo=?, texto=?, fixado=? WHERE id=?",
            (titulo, texto, int(fixado), aviso_id),
        )
        conn.commit()
    return True, "Aviso atualizado."

def remove_aviso(aviso_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM avisos WHERE id=?", (aviso_id,))
        conn.commit()

# ── Médicos ──────────────────────────────────────────────────────────────────

def init_medicos():
    """Cria a tabela de médicos, se ainda não existir."""
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS medicos (
                id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                nome               TEXT NOT NULL,
                local_atendimento  TEXT,
                horario            TEXT,
                ordem_atendimento  TEXT NOT NULL DEFAULT 'Ordem de chegada',
                idade_minima       INTEGER NOT NULL DEFAULT 0,
                exames_por_dia     INTEGER,
                observacoes        TEXT DEFAULT ''
            )
        """)
        conn.commit()

def get_medicos() -> list[dict]:
    """Retorna todos os médicos cadastrados, ordenados por nome."""
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT id, nome, local_atendimento, horario, ordem_atendimento,
                   idade_minima, exames_por_dia, observacoes
            FROM medicos
            ORDER BY nome
        """).fetchall()
    return [
        {
            "id": r[0],
            "nome": r[1],
            "local_atendimento": r[2] or "",
            "horario": r[3] or "",
            "ordem_atendimento": r[4],
            "idade_minima": r[5],
            "exames_por_dia": r[6],
            "observacoes": r[7] or "",
        }
        for r in rows
    ]

def add_medico(nome: str, local_atendimento: str, horario: str, ordem_atendimento: str,
               idade_minima: int, exames_por_dia: int | None, observacoes: str = ""):
    nome = nome.strip()
    if not nome:
        return False, "Nome não pode ser vazio."
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO medicos
                (nome, local_atendimento, horario, ordem_atendimento,
                 idade_minima, exames_por_dia, observacoes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (nome, local_atendimento.strip(), horario.strip(), ordem_atendimento,
              idade_minima, exames_por_dia, observacoes.strip()))
        conn.commit()
    return True, f'Dr(a). "{nome}" cadastrado(a).'

def update_medico(medico_id: int, nome: str, local_atendimento: str, horario: str,
                   ordem_atendimento: str, idade_minima: int,
                   exames_por_dia: int | None, observacoes: str = ""):
    nome = nome.strip()
    if not nome:
        return False, "Nome não pode ser vazio."
    with get_conn() as conn:
        conn.execute("""
            UPDATE medicos
            SET nome=?, local_atendimento=?, horario=?, ordem_atendimento=?,
                idade_minima=?, exames_por_dia=?, observacoes=?
            WHERE id=?
        """, (nome, local_atendimento.strip(), horario.strip(), ordem_atendimento,
              idade_minima, exames_por_dia, observacoes.strip(), medico_id))
        conn.commit()
    return True, "Dados atualizados."

def remove_medico(medico_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM medicos WHERE id=?", (medico_id,))
        conn.commit()
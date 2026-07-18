"""
Migração one-time: SQLite (tuss.db) -> Supabase (Postgres)

Lê as tabelas 'tuss_exames', 'medicos' e 'avisos' do banco SQLite local e
insere no Supabase, já normalizando a antiga coluna 'quem_faz' (string tipo
"Dr. A, Dr. B") em linhas na tabela de junção 'exame_medico'.

Pré-requisitos:
  - O schema já deve ter sido criado no Supabase (supabase/schema.sql)
  - Credenciais em .streamlit/secrets.toml no formato:

        [supabase]
        url = "https://xxxxx.supabase.co"
        key = "sua_anon_key"

Uso:
  python supabase/migrate_data.py            # roda a migração
  python supabase/migrate_data.py --dry-run  # só mostra o que seria migrado
"""

import sqlite3
import sys
import tomllib
from pathlib import Path

from supabase import create_client, Client

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "tuss.db"
SECRETS_PATH = ROOT / ".streamlit" / "secrets.toml"

DRY_RUN = "--dry-run" in sys.argv


def carregar_credenciais() -> tuple[str, str]:
    if not SECRETS_PATH.exists():
        sys.exit(
            f"Arquivo não encontrado: {SECRETS_PATH}\n"
            "Crie .streamlit/secrets.toml com [supabase] url e key antes de rodar a migração."
        )
    with open(SECRETS_PATH, "rb") as f:
        secrets = tomllib.load(f)
    try:
        return secrets["supabase"]["url"], secrets["supabase"]["key"]
    except KeyError:
        sys.exit("Seção [supabase] com 'url' e 'key' não encontrada em secrets.toml.")


def conectar_sqlite() -> sqlite3.Connection:
    if not DB_PATH.exists():
        sys.exit(f"Banco SQLite não encontrado em: {DB_PATH}")
    return sqlite3.connect(DB_PATH)


def migrar_medicos(sqlite_conn: sqlite3.Connection, sb: Client) -> dict[str, int]:
    """Migra médicos e retorna um mapa {nome_lower: novo_id_supabase}."""
    rows = sqlite_conn.execute("""
        SELECT nome, local_atendimento, horario, ordem_atendimento,
               idade_minima, exames_por_dia, observacoes
        FROM medicos
    """).fetchall()

    print(f"→ {len(rows)} médico(s) encontrado(s) no SQLite")

    nome_para_id: dict[str, int] = {}

    for r in rows:
        payload = {
            "nome": r[0],
            "local_atendimento": r[1] or "",
            "horario": r[2] or "",
            "ordem_atendimento": r[3],
            "idade_minima": r[4],
            "exames_por_dia": r[5],
            "observacoes": r[6] or "",
        }
        if DRY_RUN:
            print(f"  [dry-run] inseriria médico: {payload['nome']}")
            continue
        resp = sb.table("medicos").insert(payload).execute()
        novo_id = resp.data[0]["id"]
        nome_para_id[r[0].strip().lower()] = novo_id
        print(f"  ✓ {r[0]} -> id {novo_id}")

    return nome_para_id


def migrar_exames_e_vinculos(
    sqlite_conn: sqlite3.Connection, sb: Client, nome_para_id: dict[str, int]
) -> None:
    rows = sqlite_conn.execute("""
        SELECT codigo, nome, tem_preparo, observacoes, quem_faz
        FROM tuss_exames
    """).fetchall()

    print(f"→ {len(rows)} exame(s) encontrado(s) no SQLite")

    vinculos_pendentes: list[dict] = []
    nomes_nao_encontrados: set[str] = set()

    for codigo, nome, tem_preparo, observacoes, quem_faz in rows:
        payload = {
            "codigo": codigo,
            "nome": nome,
            "tem_preparo": bool(tem_preparo),
            "observacoes": observacoes or "",
        }
        if DRY_RUN:
            print(f"  [dry-run] inseriria exame: {codigo} - {nome}")
        else:
            sb.table("tuss_exames").insert(payload).execute()

        # Parse do quem_faz (string "Dr. A, Dr. B") -> vínculos individuais
        nomes = [n.strip() for n in (quem_faz or "").split(",") if n.strip()]
        for nome_medico in nomes:
            medico_id = nome_para_id.get(nome_medico.lower())
            if medico_id is None:
                nomes_nao_encontrados.add(nome_medico)
                continue
            vinculos_pendentes.append({"exame_codigo": codigo, "medico_id": medico_id})

    print(f"→ {len(vinculos_pendentes)} vínculo(s) exame-médico a inserir")

    if not DRY_RUN and vinculos_pendentes:
        # Insere em lotes de 500 para não estourar o limite de payload
        for i in range(0, len(vinculos_pendentes), 500):
            lote = vinculos_pendentes[i : i + 500]
            sb.table("exame_medico").insert(lote).execute()
        print("  ✓ vínculos inseridos")
    elif DRY_RUN:
        for v in vinculos_pendentes[:10]:
            print(f"  [dry-run] vincularia: {v}")
        if len(vinculos_pendentes) > 10:
            print(f"  [dry-run] ... e mais {len(vinculos_pendentes) - 10}")

    if nomes_nao_encontrados:
        print("\n⚠ ATENÇÃO — nomes em 'quem_faz' sem médico correspondente cadastrado:")
        for n in sorted(nomes_nao_encontrados):
            print(f"    - {n!r}")
        print(
            "  Esses vínculos NÃO foram migrados. Cadastre esses médicos manualmente\n"
            "  depois, ou corrija o nome na página Médicos e rode a migração de novo."
        )


def migrar_avisos(sqlite_conn: sqlite3.Connection, sb: Client) -> None:
    rows = sqlite_conn.execute("""
        SELECT titulo, texto, fixado, criado_em FROM avisos
    """).fetchall()

    print(f"→ {len(rows)} aviso(s) encontrado(s) no SQLite")

    for titulo, texto, fixado, criado_em in rows:
        payload = {
            "titulo": titulo,
            "texto": texto,
            "fixado": bool(fixado),
            "criado_em": criado_em,
        }
        if DRY_RUN:
            print(f"  [dry-run] inseriria aviso: {titulo}")
        else:
            sb.table("avisos").insert(payload).execute()
            print(f"  ✓ {titulo}")


def main() -> None:
    if DRY_RUN:
        print("=== MODO DRY-RUN: nada será gravado no Supabase ===\n")

    url, key = carregar_credenciais()
    sb = create_client(url, key)
    sqlite_conn = conectar_sqlite()

    print("=== 1/3 Migrando médicos ===")
    nome_para_id = migrar_medicos(sqlite_conn, sb)

    print("\n=== 2/3 Migrando exames e vínculos exame-médico ===")
    migrar_exames_e_vinculos(sqlite_conn, sb, nome_para_id)

    print("\n=== 3/3 Migrando avisos ===")
    migrar_avisos(sqlite_conn, sb)

    sqlite_conn.close()
    print("\n✓ Migração concluída." if not DRY_RUN else "\n✓ Dry-run concluído, nada foi gravado.")


if __name__ == "__main__":
    main()
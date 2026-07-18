import streamlit as st
import pandas as pd
from supabase import create_client, Client

# ── Cliente Supabase ──────────────────────────────────────────────────────────

@st.cache_resource
def get_client() -> Client:
    """Cliente Supabase, reaproveitado entre reruns via cache_resource."""
    return create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])


def get_nomes_medicos() -> list[str]:
    """Retorna os nomes dos médicos cadastrados, usados no filtro 'Quem faz'."""
    sb = get_client()
    resp = sb.table("medicos").select("nome").order("nome").execute()
    return [r["nome"] for r in resp.data]


def _mapa_medicos_por_exame() -> dict[str, list[str]]:
    """Constrói {codigo_exame: [nomes_medicos]} em uma única query (join embutido)."""
    sb = get_client()
    resp = sb.table("exame_medico").select("exame_codigo, medicos(nome)").execute()
    mapa: dict[str, list[str]] = {}
    for row in resp.data:
        medico = row.get("medicos")
        if medico and medico.get("nome"):
            mapa.setdefault(row["exame_codigo"], []).append(medico["nome"])
    return mapa


def fetch_all(search="", filtro_preparo="Todos", filtro_quem=None) -> pd.DataFrame:
    sb = get_client()
    colunas = ["codigo", "nome", "tem_preparo", "observacoes"]
    query = sb.table("tuss_exames").select(", ".join(colunas))

    if search:
        termo = search.replace("%", "").replace(",", "")
        query = query.or_(f"codigo.ilike.%{termo}%,nome.ilike.%{termo}%")

    if filtro_preparo == "Com preparo":
        query = query.eq("tem_preparo", True)
    elif filtro_preparo == "Sem preparo":
        query = query.eq("tem_preparo", False)

    if filtro_quem:
        medicos_resp = sb.table("medicos").select("id").in_("nome", filtro_quem).execute()
        medico_ids = [m["id"] for m in medicos_resp.data]
        if not medico_ids:
            return pd.DataFrame(columns=["codigo", "nome", "quem_faz", "tem_preparo", "observacoes"])

        vinculos_resp = (
            sb.table("exame_medico").select("exame_codigo").in_("medico_id", medico_ids).execute()
        )
        codigos_permitidos = list({v["exame_codigo"] for v in vinculos_resp.data})
        if not codigos_permitidos:
            return pd.DataFrame(columns=["codigo", "nome", "quem_faz", "tem_preparo", "observacoes"])
        query = query.in_("codigo", codigos_permitidos)

    resp = query.order("nome").execute()
    df = pd.DataFrame(resp.data, columns=colunas)

    if df.empty:
        return pd.DataFrame(columns=["codigo", "nome", "quem_faz", "tem_preparo", "observacoes"])

    mapa = _mapa_medicos_por_exame()
    df["quem_faz"] = df["codigo"].apply(lambda c: ", ".join(sorted(mapa.get(c, []))))
    df["tem_preparo"] = df["tem_preparo"].astype(bool)
    df["observacoes"] = df["observacoes"].fillna("")
    return df[["codigo", "nome", "quem_faz", "tem_preparo", "observacoes"]]


def save_quem_faz(codigo: str, medicos_selecionados: list[str]):
    """Substitui os vínculos exame-médico de um procedimento pelos nomes selecionados."""
    sb = get_client()
    sb.table("exame_medico").delete().eq("exame_codigo", codigo).execute()
    if not medicos_selecionados:
        return
    medicos_resp = sb.table("medicos").select("id").in_("nome", medicos_selecionados).execute()
    ids = [m["id"] for m in medicos_resp.data]
    if ids:
        sb.table("exame_medico").insert(
            [{"exame_codigo": codigo, "medico_id": i} for i in ids]
        ).execute()


def save_observacoes(codigo: str, texto: str):
    """Salva o texto de observações de um procedimento."""
    sb = get_client()
    sb.table("tuss_exames").update({"observacoes": texto}).eq("codigo", codigo).execute()


def save_tem_preparo(codigo: str, tem_preparo: bool):
    """Salva se o procedimento exige preparo."""
    sb = get_client()
    sb.table("tuss_exames").update({"tem_preparo": tem_preparo}).eq("codigo", codigo).execute()


def count_stats():
    sb = get_client()
    total = sb.table("tuss_exames").select("codigo", count="exact").execute().count or 0
    c_preparo = (
        sb.table("tuss_exames").select("codigo", count="exact").eq("tem_preparo", True).execute().count or 0
    )
    vinculos = sb.table("exame_medico").select("exame_codigo").execute()
    c_quem = len({v["exame_codigo"] for v in vinculos.data})
    return total, c_preparo, c_quem


# ── Mural de avisos ──────────────────────────────────────────────────────────

def get_avisos() -> list[dict]:
    """Retorna todos os avisos, fixados primeiro e depois por data (mais recente primeiro)."""
    sb = get_client()
    resp = (
        sb.table("avisos")
        .select("id, titulo, texto, fixado, criado_em")
        .order("fixado", desc=True)
        .order("criado_em", desc=True)
        .order("id", desc=True)
        .execute()
    )
    return resp.data


def add_aviso(titulo: str, texto: str, fixado: bool = False):
    titulo = titulo.strip()
    texto = texto.strip()
    if not titulo or not texto:
        return False, "Título e mensagem são obrigatórios."
    sb = get_client()
    try:
        sb.table("avisos").insert({"titulo": titulo, "texto": texto, "fixado": fixado}).execute()
    except Exception as e:
        return False, f"Erro ao publicar aviso: {e}"
    return True, "Aviso publicado no mural."


def update_aviso(aviso_id: int, titulo: str, texto: str, fixado: bool):
    titulo = titulo.strip()
    texto = texto.strip()
    if not titulo or not texto:
        return False, "Título e mensagem são obrigatórios."
    sb = get_client()
    try:
        sb.table("avisos").update(
            {"titulo": titulo, "texto": texto, "fixado": fixado}
        ).eq("id", aviso_id).execute()
    except Exception as e:
        return False, f"Erro ao atualizar aviso: {e}"
    return True, "Aviso atualizado."


def remove_aviso(aviso_id: int):
    sb = get_client()
    sb.table("avisos").delete().eq("id", aviso_id).execute()


# ── Médicos ──────────────────────────────────────────────────────────────────

def get_medicos() -> list[dict]:
    """Retorna todos os médicos cadastrados, ordenados por nome."""
    sb = get_client()
    resp = (
        sb.table("medicos")
        .select("id, nome, local_atendimento, horario, ordem_atendimento, idade_minima, exames_por_dia, observacoes")
        .order("nome")
        .execute()
    )
    medicos = resp.data
    for m in medicos:
        m["local_atendimento"] = m.get("local_atendimento") or ""
        m["horario"] = m.get("horario") or ""
        m["observacoes"] = m.get("observacoes") or ""
    return medicos


def add_medico(nome: str, local_atendimento: str, horario: str, ordem_atendimento: str,
               idade_minima: int, exames_por_dia: int | None, observacoes: str = ""):
    nome = nome.strip()
    if not nome:
        return False, "Nome não pode ser vazio."
    sb = get_client()
    try:
        sb.table("medicos").insert({
            "nome": nome,
            "local_atendimento": local_atendimento.strip(),
            "horario": horario.strip(),
            "ordem_atendimento": ordem_atendimento,
            "idade_minima": idade_minima,
            "exames_por_dia": exames_por_dia,
            "observacoes": observacoes.strip(),
        }).execute()
    except Exception as e:
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            return False, f'Já existe um médico chamado "{nome}".'
        return False, f"Erro ao cadastrar: {e}"
    return True, f'Dr(a). "{nome}" cadastrado(a).'


def update_medico(medico_id: int, nome: str, local_atendimento: str, horario: str,
                   ordem_atendimento: str, idade_minima: int,
                   exames_por_dia: int | None, observacoes: str = ""):
    nome = nome.strip()
    if not nome:
        return False, "Nome não pode ser vazio."
    sb = get_client()
    try:
        sb.table("medicos").update({
            "nome": nome,
            "local_atendimento": local_atendimento.strip(),
            "horario": horario.strip(),
            "ordem_atendimento": ordem_atendimento,
            "idade_minima": idade_minima,
            "exames_por_dia": exames_por_dia,
            "observacoes": observacoes.strip(),
        }).eq("id", medico_id).execute()
    except Exception as e:
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            return False, f'Já existe um médico chamado "{nome}".'
        return False, f"Erro ao atualizar: {e}"
    return True, "Dados atualizados."


def remove_medico(medico_id: int):
    """Remove o médico; vínculos em exame_medico são removidos em cascata (ON DELETE CASCADE)."""
    sb = get_client()
    sb.table("medicos").delete().eq("id", medico_id).execute()
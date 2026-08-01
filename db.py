from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st
import pandas as pd
from supabase import create_client, Client

FUSO_BR = ZoneInfo("America/Sao_Paulo")

# ── Cliente Supabase ──────────────────────────────────────────────────────────

@st.cache_resource
def get_client() -> Client:
    """Cliente Supabase, reaproveitado entre reruns via cache_resource."""
    return create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])


@st.cache_data(ttl=300)
def get_nomes_medicos() -> list[str]:
    """Retorna os nomes dos médicos cadastrados, usados no filtro 'Quem faz'."""
    sb = get_client()
    resp = sb.table("medicos").select("nome").order("nome").execute()
    return [r["nome"] for r in resp.data]


@st.cache_data(ttl=300)
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


@st.cache_data(ttl=300)
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
    try:
        sb.table("exame_medico").delete().eq("exame_codigo", codigo).execute()
        if not medicos_selecionados:
            _mapa_medicos_por_exame.clear()
            fetch_all.clear()
            count_stats.clear()
            return True, None
        medicos_resp = sb.table("medicos").select("id").in_("nome", medicos_selecionados).execute()
        ids = [m["id"] for m in medicos_resp.data]
        if ids:
            sb.table("exame_medico").insert(
                [{"exame_codigo": codigo, "medico_id": i} for i in ids]
            ).execute()
    except Exception as e:
        return False, f"Erro ao salvar os médicos responsáveis: {e}"
    _mapa_medicos_por_exame.clear()
    fetch_all.clear()
    count_stats.clear()
    return True, None


def save_observacoes(codigo: str, texto: str):
    """Salva o texto de observações de um procedimento."""
    sb = get_client()
    try:
        sb.table("tuss_exames").update({"observacoes": texto}).eq("codigo", codigo).execute()
    except Exception as e:
        return False, f"Erro ao salvar observações: {e}"
    fetch_all.clear()
    return True, None


def save_tem_preparo(codigo: str, tem_preparo: bool):
    """Salva se o procedimento exige preparo."""
    sb = get_client()
    try:
        sb.table("tuss_exames").update({"tem_preparo": tem_preparo}).eq("codigo", codigo).execute()
    except Exception as e:
        return False, f"Erro ao salvar preparo: {e}"
    fetch_all.clear()
    count_stats.clear()
    return True, None


@st.cache_data(ttl=300)
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

def formatar_data_br(timestamp_iso: str) -> str:
    """Converte um timestamp ISO (UTC) do Supabase para 'dd/mm/AAAA às HH:MM' no horário de Brasília."""
    if not timestamp_iso:
        return ""
    try:
        dt = datetime.fromisoformat(timestamp_iso.replace("Z", "+00:00"))
        return dt.astimezone(FUSO_BR).strftime("%d/%m/%Y às %H:%M")
    except (ValueError, TypeError):
        return timestamp_iso


@st.cache_data(ttl=300)
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
    get_avisos.clear()
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
    get_avisos.clear()
    return True, "Aviso atualizado."


def remove_aviso(aviso_id: int):
    sb = get_client()
    try:
        sb.table("avisos").delete().eq("id", aviso_id).execute()
    except Exception as e:
        return False, f"Erro ao remover aviso: {e}"
    get_avisos.clear()
    return True, None


# ── Médicos ──────────────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def get_medicos() -> list[dict]:
    """Retorna todos os médicos cadastrados, ordenados por nome."""
    sb = get_client()
    resp = (
        sb.table("medicos")
        .select(
            "id, nome, local_atendimento, horario, ordem_atendimento, "
            "idade_minima, exames_por_dia, observacoes, agenda"
        )
        .order("nome")
        .execute()
    )
    medicos = resp.data
    for m in medicos:
        m["local_atendimento"] = m.get("local_atendimento") or ""
        m["horario"] = m.get("horario") or ""
        m["observacoes"] = m.get("observacoes") or ""
        m["agenda"] = m.get("agenda") or []
    return medicos


def add_medico(nome: str, local_atendimento: str, horario: str, ordem_atendimento: str,
               idade_minima: int, exames_por_dia: int | None, observacoes: str = "",
               agenda: list[str] | None = None):
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
            "agenda": agenda or [],
        }).execute()
    except Exception as e:
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            return False, f'Já existe um médico chamado "{nome}".'
        return False, f"Erro ao cadastrar: {e}"
    get_medicos.clear()
    get_nomes_medicos.clear()
    return True, f'Dr(a). "{nome}" cadastrado(a).'


def update_medico(medico_id: int, nome: str, local_atendimento: str, horario: str,
                   ordem_atendimento: str, idade_minima: int,
                   exames_por_dia: int | None, observacoes: str = "",
                   agenda: list[str] | None = None):
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
            "agenda": agenda or [],
        }).eq("id", medico_id).execute()
    except Exception as e:
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            return False, f'Já existe um médico chamado "{nome}".'
        return False, f"Erro ao atualizar: {e}"
    get_medicos.clear()
    get_nomes_medicos.clear()
    fetch_all.clear()
    return True, "Dados atualizados."


def remove_medico(medico_id: int):
    """Remove o médico; vínculos em exame_medico são removidos em cascata (ON DELETE CASCADE)."""
    sb = get_client()
    try:
        sb.table("medicos").delete().eq("id", medico_id).execute()
    except Exception as e:
        return False, f"Erro ao remover médico: {e}"
    get_medicos.clear()
    get_nomes_medicos.clear()
    fetch_all.clear()
    _mapa_medicos_por_exame.clear()
    count_stats.clear()
    return True, None


# ── Fluxos de trabalho ───────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def get_fluxos() -> list[dict]:
    """Retorna todos os fluxos de trabalho cadastrados, ordenados por nome."""
    sb = get_client()
    resp = sb.table("fluxos_trabalho").select("id, nome, descricao").order("nome").execute()
    fluxos = resp.data
    for f in fluxos:
        f["descricao"] = f.get("descricao") or ""
    return fluxos


def add_fluxo(nome: str, descricao: str = ""):
    nome = nome.strip()
    if not nome:
        return False, "Nome do fluxo não pode ser vazio."
    sb = get_client()
    try:
        sb.table("fluxos_trabalho").insert({"nome": nome, "descricao": descricao.strip()}).execute()
    except Exception as e:
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            return False, f'Já existe um fluxo chamado "{nome}".'
        return False, f"Erro ao cadastrar fluxo: {e}"
    get_fluxos.clear()
    return True, f'Fluxo "{nome}" cadastrado.'


def update_fluxo(fluxo_id: int, nome: str, descricao: str = ""):
    nome = nome.strip()
    if not nome:
        return False, "Nome do fluxo não pode ser vazio."
    sb = get_client()
    try:
        sb.table("fluxos_trabalho").update(
            {"nome": nome, "descricao": descricao.strip()}
        ).eq("id", fluxo_id).execute()
    except Exception as e:
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            return False, f'Já existe um fluxo chamado "{nome}".'
        return False, f"Erro ao atualizar fluxo: {e}"
    get_fluxos.clear()
    get_especialidades.clear()
    return True, "Fluxo atualizado."


def remove_fluxo(fluxo_id: int):
    """Remove o fluxo; especialidades vinculadas ficam com fluxo_id nulo (ON DELETE SET NULL)."""
    sb = get_client()
    try:
        sb.table("fluxos_trabalho").delete().eq("id", fluxo_id).execute()
    except Exception as e:
        return False, f"Erro ao remover fluxo: {e}"
    get_fluxos.clear()
    get_especialidades.clear()
    return True, None


# ── Especialidades ───────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def get_especialidades(search: str = "") -> list[dict]:
    """Busca especialidades por nome ou código, já com o fluxo vinculado (se houver)."""
    sb = get_client()
    query = sb.table("especialidades").select(
        "codigo, nome, fluxo_id, fluxos_trabalho(id, nome, descricao)"
    )
    if search:
        termo = search.replace("%", "").replace(",", "")
        query = query.or_(f"codigo.ilike.%{termo}%,nome.ilike.%{termo}%")
    resp = query.order("nome").execute()

    especialidades = []
    for row in resp.data:
        fluxo = row.get("fluxos_trabalho")
        especialidades.append({
            "codigo": row["codigo"],
            "nome": row["nome"],
            "fluxo_id": row.get("fluxo_id"),
            "fluxo_nome": fluxo["nome"] if fluxo else None,
            "fluxo_descricao": fluxo["descricao"] if fluxo else None,
        })
    return especialidades


def add_especialidade(codigo: str, nome: str, fluxo_id: int | None = None):
    codigo = codigo.strip()
    nome = nome.strip()
    if not codigo or not nome:
        return False, "Código e nome são obrigatórios."
    sb = get_client()
    try:
        sb.table("especialidades").insert(
            {"codigo": codigo, "nome": nome, "fluxo_id": fluxo_id}
        ).execute()
    except Exception as e:
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            return False, f'Já existe uma especialidade com o código "{codigo}".'
        return False, f"Erro ao cadastrar especialidade: {e}"
    get_especialidades.clear()
    return True, f'Especialidade "{nome}" cadastrada.'


def save_especialidade_fluxo(codigo: str, fluxo_id: int | None):
    """Atribui (ou remove, se fluxo_id=None) o fluxo de trabalho de uma especialidade."""
    sb = get_client()
    try:
        sb.table("especialidades").update({"fluxo_id": fluxo_id}).eq("codigo", codigo).execute()
    except Exception as e:
        return False, f"Erro ao salvar fluxo da especialidade: {e}"
    get_especialidades.clear()
    return True, None


def remove_especialidade(codigo: str):
    sb = get_client()
    try:
        sb.table("especialidades").delete().eq("codigo", codigo).execute()
    except Exception as e:
        return False, f"Erro ao remover especialidade: {e}"
    get_especialidades.clear()
    return True, None
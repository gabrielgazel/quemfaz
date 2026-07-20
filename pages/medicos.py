import streamlit as st

from db import get_medicos, add_medico, update_medico, remove_medico

st.title("Médicos")
st.caption("Gerencie os médicos que realizam os exames.")
st.divider()

ORDENS = ["Hora marcada", "Ordem de chegada"]


@st.dialog("Médico")
def modal_medico(medico: dict | None = None):
    nome = st.text_input("Nome", value=medico["nome"] if medico else "")
    local_atendimento = st.text_input(
        "Local de atendimento",
        value=medico["local_atendimento"] if medico else "",
    )
    horario = st.text_input(
        "Horário de atendimento",
        value=medico["horario"] if medico else "",
        placeholder="Ex: 08:00 às 12:00",
    )
    ordem_atendimento = st.radio(
        "Ordem de atendimento",
        options=ORDENS,
        index=ORDENS.index(medico["ordem_atendimento"]) if medico else 1,
        horizontal=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        idade_minima = st.number_input(
            "Idade mínima (anos)",
            min_value=0, max_value=120, step=1,
            value=medico["idade_minima"] if medico else 0,
        )
    with col2:
        exames_por_dia = st.number_input(
            "Exames por dia (0 = sem limite)",
            min_value=0, step=1,
            value=medico["exames_por_dia"] if medico and medico["exames_por_dia"] else 0,
        )

    observacoes = st.text_area(
        "Observações",
        value=medico["observacoes"] if medico else "",
    )

    col_salvar, col_excluir = st.columns([3, 1])
    with col_salvar:
        if st.button("Salvar", type="primary", use_container_width=True):
            exames_valor = exames_por_dia if exames_por_dia > 0 else None
            if medico:
                ok, msg = update_medico(
                    medico["id"], nome, local_atendimento, horario,
                    ordem_atendimento, idade_minima, exames_valor, observacoes,
                )
            else:
                ok, msg = add_medico(
                    nome, local_atendimento, horario, ordem_atendimento,
                    idade_minima, exames_valor, observacoes,
                )
            if ok:
                st.rerun()
            else:
                st.error(msg)
    with col_excluir:
        if medico and st.button("Excluir", use_container_width=True):
            remove_medico(medico["id"])
            st.rerun()


if st.button("Novo médico", icon=":material/add:"):
    modal_medico()

medicos = get_medicos()

if not medicos:
    st.info("Nenhum médico cadastrado ainda.")
else:
    colunas = st.columns(3)
    for i, medico in enumerate(medicos):
        with colunas[i % 3]:
            with st.container(border=True):
                st.markdown(f"### {medico['nome']}")
                st.markdown(f":material/location_on: **Local:** {medico['local_atendimento'] or '—'}")
                st.markdown(f":material/schedule: **Horário:** {medico['horario'] or '—'}")

                icone_ordem = (
                    ":material/event_available:"
                    if medico["ordem_atendimento"] == "Hora marcada"
                    else ":material/groups:"
                )
                st.markdown(f"{icone_ordem} **Atendimento:** {medico['ordem_atendimento']}")
                st.markdown(f":material/child_care: **Idade mínima:** {medico['idade_minima']} anos")
                st.markdown(
                    f":material/event_repeat: **Exames/dia:** "
                    f"{medico['exames_por_dia'] if medico['exames_por_dia'] else 'sem limite'}"
                )

                if medico["observacoes"]:
                    st.caption(medico["observacoes"])

                if st.button("Editar", key=f"editar_{medico['id']}", use_container_width=True):
                    modal_medico(medico)
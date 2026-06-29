import streamlit as st
import pandas as pd
import funcoes

menu = st.sidebar.selectbox("Opções", ["Adicionar exame", "Listar exames"])

if menu == "Adicionar exame":
    st.title("Adicione um exame")
    medicos = ["Dr. Daniel",
           "Dr. Fernando",
           "Dr. Gustavo",
           "Dr. Luiz Otavio",
           "Dra. Nathalia",
           "Dra. Sabrina"]
    with st.form("formulario_usg"):
        cod_tuss = st.text_input("Código TUSS")
        nome_exame = st.text_input("Nome do exame")
        quem_faz = st.selectbox(label="Quem faz?",
                                options=medicos,
                                placeholder="Selecione um médico")
        tem_preparo = st.radio(label="Tem preparo?",
                            options=["Sim", "Não"])
        botao_add = st.form_submit_button("Adicionar",
                                        type="primary",
                                        use_container_width=True)
        
    if botao_add:
        funcoes.inserir_dados(cod_tuss, nome_exame, quem_faz, tem_preparo)
        st.success("Exame adicionado com sucesso!")

elif menu == "Listar exames":
    st.title("Lista de exames")
    dados = funcoes.listar_dados()
    tb = pd.DataFrame(dados, columns=["ID","Código TUSS", "Nome do exame", "Quem faz", "Tem preparo"])
    st.dataframe(tb)
# QuemFaz

Aplicação Streamlit para gestão de códigos de procedimentos TUSS, permitindo indicar qual médico realiza cada exame, necessidade de preparo e observações.

Base de dados filtrada para códigos TUSS iniciados em `4090`, `4100` e `4110` (~210 registros).

## Funcionalidades

- **Início**: mural de avisos e comunicados
- **Consulta**: tabela com todos os procedimentos, filtro por nome/código, preparo e médico responsável ("Quem faz")
- **Médicos**: cadastro dos médicos (local e horário de atendimento, ordem de atendimento, idade mínima, limite de exames/dia). Os nomes cadastrados aqui alimentam o filtro "Quem faz" da página Consulta
- Persistência em SQLite

## Estrutura

```
quemfaz/
├── app.py                  # Entrypoint (st.navigation)
├── db.py                   # Acesso e migração do banco
├── pages/
│   ├── inicio.py           # Mural de avisos
│   ├── consulta.py         # Tabela principal + filtros
│   └── medicos.py          # Cadastro de médicos (fonte do filtro "Quem faz")
├── tuss.db                 # Banco SQLite
├── .streamlit/config.toml  # Tema
├── pyproject.toml / uv.lock
└── requirements.txt        # Necessário para deploy no Streamlit Cloud
```

## Como rodar

```bash
git clone https://github.com/gabrielgazel/quemfaz.git
cd quemfaz
uv sync
streamlit run app.py
```

## Deploy

Feito via [Streamlit Community Cloud](https://share.streamlit.io). Requer `requirements.txt` e `tuss.db` versionados no repositório.

## Commits

Padrão [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `refactor:`).
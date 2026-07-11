# QuemFaz

Aplicação Streamlit para gestão de códigos de procedimentos TUSS, permitindo definir responsáveis, indicar necessidade de preparo e registrar observações para cada procedimento.

Base de dados filtrada para códigos TUSS iniciados em `4090`, `4100` e `4110` (~210 registros).

## Funcionalidades

- **Consulta**: tabela com todos os procedimentos, edição via modal
- **Responsáveis**: gestão dos responsáveis, usados como seleção (multiselect) na edição
- Persistência em SQLite

## Estrutura

```
quemfaz/
├── app.py                  # Entrypoint (st.navigation)
├── db.py                   # Acesso e migração do banco
├── pages/
│   ├── consulta.py         # Tabela principal + edição
│   └── responsaveis.py     # Gestão de responsáveis
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
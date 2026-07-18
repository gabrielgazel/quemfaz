# QuemFaz

Aplicação Streamlit para gestão de códigos de procedimentos TUSS, permitindo indicar qual médico realiza cada exame, necessidade de preparo e observações.

Base de dados filtrada para códigos TUSS iniciados em `4090`, `4100` e `4110` (~210 registros).

## Funcionalidades

- **Login**: acesso protegido por senha única (ver [Secrets](#secrets))
- **Início**: mural de avisos e comunicados
- **Consulta**: tabela com todos os procedimentos, filtro por nome/código, preparo e médico responsável ("Quem faz")
- **Médicos**: cadastro dos médicos (local e horário de atendimento, ordem de atendimento, idade mínima, limite de exames/dia). Os nomes cadastrados aqui alimentam o filtro "Quem faz" da página Consulta
- Persistência em **Supabase (Postgres)**

## Arquitetura de dados

O banco é normalizado em 4 tabelas (schema completo em [`supabase_setup/schema.sql`](supabase_setup/schema.sql)):

- `tuss_exames` — catálogo de procedimentos TUSS (`codigo`, `nome`, `tem_preparo`, `observacoes`)
- `medicos` — cadastro de médicos (nome único, case-insensitive)
- `exame_medico` — tabela de junção N:N entre exames e médicos (`ON DELETE CASCADE`), substitui a antiga coluna de texto `quem_faz`
- `avisos` — mural de comunicados

RLS (Row Level Security) fica **desligado** de propósito: o controle de acesso acontece na camada do app (login por senha), não no banco. Detalhes no comentário final do `schema.sql`.

> O projeto rodou em SQLite até meados de 2026, quando foi migrado para Supabase. O script usado na migração one-time (SQLite → Supabase, incluindo o parse do antigo `quem_faz`) está em [`supabase_setup/migrate_data.py`](supabase_setup/migrate_data.py), preservado como referência histórica — não precisa ser executado de novo.

## Estrutura

```
quemfaz/
├── app.py                        # Entrypoint: login + navegação (st.navigation)
├── db.py                         # Acesso a dados via supabase-py
├── pages/
│   ├── inicio.py                 # Mural de avisos
│   ├── consulta.py               # Tabela principal + filtros
│   └── medicos.py                # Cadastro de médicos (fonte do filtro "Quem faz")
├── supabase_setup/
│   ├── schema.sql                # Schema Postgres (rodar no SQL Editor do Supabase)
│   └── migrate_data.py           # Script histórico de migração SQLite -> Supabase
├── .streamlit/
│   ├── config.toml               # Tema (paleta clara, verde escuro, fonte Fira Code)
│   └── secrets.toml              # Credenciais locais (NÃO versionado — ver Secrets)
├── pyproject.toml / uv.lock       # Dependências (fonte usada no deploy)
└── requirements.txt               # Mantido por compatibilidade, uv.lock é o que vale no deploy
```

## Secrets

O app precisa de um `.streamlit/secrets.toml` (nunca commitado — está no `.gitignore`) com:

```toml
[supabase]
url = "https://xxxxx.supabase.co"
key = "sua_anon_key"

[auth]
senha = "senha-de-acesso-ao-app"
```

Em produção, as mesmas chaves precisam estar cadastradas em **Streamlit Cloud → Manage app → Settings → Secrets**.

## Como rodar

```bash
git clone https://github.com/gabrielgazel/quemfaz.git
cd quemfaz
uv sync
# criar .streamlit/secrets.toml com as credenciais acima
streamlit run app.py
```

## Deploy

Feito via [Streamlit Community Cloud](https://share.streamlit.io), branch `main`, deploy automático a cada push.

⚠️ O Streamlit Cloud usa **`uv.lock`** para instalar dependências (não `requirements.txt`, que é mantido só por compatibilidade). Ao adicionar uma dependência nova, use `uv add <pacote>` para manter `pyproject.toml` e `uv.lock` sincronizados — editar esses arquivos manualmente pode causar `ImportError` silencioso em produção.

Depois de qualquer mudança em dependências ou secrets, é necessário **Reboot app** no painel do Streamlit Cloud para forçar a reinstalação/releitura.

## Commits

Padrão [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `refactor:`, `chore:`).
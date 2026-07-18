-- ============================================================================
-- QuemFaz — Schema Supabase (Postgres)
-- Rodar no SQL Editor do projeto Supabase (Project → SQL Editor → New query)
-- ============================================================================

-- ── tuss_exames ───────────────────────────────────────────────────────────
-- Catálogo de procedimentos TUSS. Sem a coluna 'quem_faz' (agora normalizada
-- na tabela exame_medico abaixo).
create table if not exists tuss_exames (
    codigo       text primary key,
    nome         text not null,
    tem_preparo  boolean not null default false,
    observacoes  text not null default ''
);

create index if not exists idx_tuss_exames_nome on tuss_exames (nome);

-- ── medicos ───────────────────────────────────────────────────────────────
create table if not exists medicos (
    id                 bigint generated always as identity primary key,
    nome               text not null,
    local_atendimento  text default '',
    horario            text default '',
    ordem_atendimento  text not null default 'Ordem de chegada',
    idade_minima       integer not null default 0,
    exames_por_dia     integer,
    observacoes        text default ''
);

-- Evita dois médicos com o mesmo nome (case-insensitive)
create unique index if not exists idx_medicos_nome_unique
    on medicos (lower(nome));

-- ── exame_medico ──────────────────────────────────────────────────────────
-- Junção N:N entre exames e médicos, substitui a antiga string 'quem_faz'.
-- ON DELETE CASCADE: remover um médico ou exame limpa o vínculo automaticamente
-- (em vez de deixar nome "preso" em texto solto, como acontecia antes).
create table if not exists exame_medico (
    exame_codigo  text not null references tuss_exames (codigo) on delete cascade,
    medico_id     bigint not null references medicos (id) on delete cascade,
    primary key (exame_codigo, medico_id)
);

create index if not exists idx_exame_medico_medico on exame_medico (medico_id);

-- ── avisos ────────────────────────────────────────────────────────────────
create table if not exists avisos (
    id         bigint generated always as identity primary key,
    titulo     text not null,
    texto      text not null,
    fixado     boolean not null default false,
    criado_em  timestamptz not null default now()
);

create index if not exists idx_avisos_fixado_criado on avisos (fixado desc, criado_em desc);

-- ============================================================================
-- Row Level Security
--
-- O app usa login caseiro (senha via st.secrets), não o Supabase Auth — a
-- autenticação acontece no Streamlit, e o backend (db.py) usa a mesma
-- anon key para todas as operações. Por isso, deixamos RLS DESLIGADO aqui:
-- o controle de acesso é 100% responsabilidade da camada do app.
--
-- Isso é seguro NESTE cenário porque a anon key fica em .streamlit/secrets.toml
-- (nunca exposta ao navegador do usuário final) — mas se algum dia o app for
-- reescrito em algo client-side (JS puro, por exemplo), isso precisa mudar
-- para políticas de RLS antes de expor a key no cliente.
-- ============================================================================
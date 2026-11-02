-- =============================================================
-- BarberAgenda - Script de criação do banco de dados (SQLite)
-- Entidades: USUARIO, CLIENTE, PROFISSIONAL, SERVICO, AGENDAMENTO
-- =============================================================

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS usuario (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nome        TEXT    NOT NULL,
    login       TEXT    NOT NULL UNIQUE,
    senha_hash  TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS cliente (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nome        TEXT    NOT NULL,
    telefone    TEXT    NOT NULL UNIQUE,
    criado_em   TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS profissional (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nome        TEXT    NOT NULL,
    ativo       INTEGER NOT NULL DEFAULT 1 CHECK (ativo IN (0, 1))
);

CREATE TABLE IF NOT EXISTS servico (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    nome             TEXT    NOT NULL UNIQUE,
    duracao_minutos  INTEGER NOT NULL CHECK (duracao_minutos > 0),
    preco            REAL    NOT NULL CHECK (preco >= 0)
);

CREATE TABLE IF NOT EXISTS agendamento (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id       INTEGER NOT NULL REFERENCES cliente (id),
    profissional_id  INTEGER NOT NULL REFERENCES profissional (id),
    servico_id       INTEGER NOT NULL REFERENCES servico (id),
    usuario_id       INTEGER NOT NULL REFERENCES usuario (id),
    data             TEXT    NOT NULL,              -- formato AAAA-MM-DD
    hora_inicio      TEXT    NOT NULL,              -- formato HH:MM
    hora_fim         TEXT    NOT NULL,              -- calculada pela duração do serviço
    status           TEXT    NOT NULL DEFAULT 'AGENDADO'
                             CHECK (status IN ('AGENDADO', 'CANCELADO')),
    criado_em        TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_agendamento_data_profissional
    ON agendamento (data, profissional_id);

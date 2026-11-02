"""Conexão com o banco de dados SQLite e criação das tabelas."""
import os
import sqlite3

from flask import current_app, g
from werkzeug.security import generate_password_hash

PASTA = os.path.dirname(os.path.abspath(__file__))


def conectar(caminho):
    """Abre uma conexão com o SQLite, com chaves estrangeiras ativas."""
    conexao = sqlite3.connect(caminho)
    conexao.row_factory = sqlite3.Row          # acesso às colunas pelo nome
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def obter_conexao():
    """Retorna a conexão da requisição atual (uma por requisição)."""
    if "db" not in g:
        g.db = conectar(current_app.config["DATABASE"])
    return g.db


def fechar_conexao(_erro=None):
    conexao = g.pop("db", None)
    if conexao is not None:
        conexao.close()


def inicializar_banco(caminho):
    """Cria as tabelas (se não existirem) e insere os dados iniciais."""
    conexao = conectar(caminho)
    with open(os.path.join(PASTA, "schema.sql"), encoding="utf-8") as arquivo:
        conexao.executescript(arquivo.read())

    if conexao.execute("SELECT COUNT(*) FROM usuario").fetchone()[0] == 0:
        conexao.execute(
            "INSERT INTO usuario (nome, login, senha_hash) VALUES (?, ?, ?)",
            ("Atendente", "atendente", generate_password_hash("barbearia123")),
        )
    if conexao.execute("SELECT COUNT(*) FROM profissional").fetchone()[0] == 0:
        conexao.executemany(
            "INSERT INTO profissional (nome) VALUES (?)",
            [("Carlos Silva",), ("Marcos Souza",)],
        )
    if conexao.execute("SELECT COUNT(*) FROM servico").fetchone()[0] == 0:
        conexao.executemany(
            "INSERT INTO servico (nome, duracao_minutos, preco) VALUES (?, ?, ?)",
            [
                ("Corte de cabelo", 30, 35.00),
                ("Barba", 30, 25.00),
                ("Corte + barba", 60, 55.00),
                ("Sobrancelha", 15, 15.00),
            ],
        )
    conexao.commit()
    conexao.close()


def registrar(app):
    """Liga o ciclo de vida da conexão ao Flask e prepara o banco."""
    app.teardown_appcontext(fechar_conexao)
    inicializar_banco(app.config["DATABASE"])

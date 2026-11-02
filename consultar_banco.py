"""Mostra no terminal os dados gravados no banco barbearia.db.
Uso:  python consultar_banco.py
"""
import os
import sqlite3

CAMINHO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "barbearia.db")

CONSULTAS = [
    ("Clientes cadastrados",
     "SELECT id, nome, telefone FROM cliente ORDER BY id",
     ["id", "nome", "telefone"]),
    ("Agendamentos",
     """SELECT a.id, c.nome, s.nome, p.nome, a.data, a.hora_inicio, a.hora_fim, a.status
        FROM agendamento a
        JOIN cliente c      ON c.id = a.cliente_id
        JOIN servico s      ON s.id = a.servico_id
        JOIN profissional p ON p.id = a.profissional_id
        ORDER BY a.data, a.hora_inicio""",
     ["id", "cliente", "servico", "profissional", "data", "inicio", "fim", "status"]),
]


def imprimir_tabela(cabecalho, linhas):
    larguras = [max(len(str(v)) for v in [h] + [l[i] for l in linhas])
                for i, h in enumerate(cabecalho)]
    print(" | ".join(h.ljust(larguras[i]) for i, h in enumerate(cabecalho)))
    print("-+-".join("-" * l for l in larguras))
    for linha in linhas:
        print(" | ".join(str(v).ljust(larguras[i]) for i, v in enumerate(linha)))
    print(f"({len(linhas)} linhas)\n")


if __name__ == "__main__":
    conexao = sqlite3.connect(CAMINHO)
    for titulo, sql, cabecalho in CONSULTAS:
        print(f"== {titulo} ==")
        print("SQL> " + "\n     ".join(l.strip() for l in sql.strip().splitlines()))
        print()
        imprimir_tabela(cabecalho, conexao.execute(sql).fetchall())
    conexao.close()

"""Acesso ao banco de dados. Todas as consultas usam parâmetros (?),
o que evita SQL Injection (RNF05)."""
from models import Cliente, Profissional, Servico, Usuario


class UsuarioRepositorio:
    def __init__(self, conexao):
        self.conexao = conexao

    def buscar_por_login(self, login):
        linha = self.conexao.execute(
            "SELECT id, nome, login, senha_hash FROM usuario WHERE login = ?",
            ((login or "").strip(),),
        ).fetchone()
        return Usuario(**dict(linha)) if linha else None


class ClienteRepositorio:
    def __init__(self, conexao):
        self.conexao = conexao

    def salvar(self, cliente: Cliente):
        cursor = self.conexao.execute(
            "INSERT INTO cliente (nome, telefone) VALUES (?, ?)",
            (cliente.nome, cliente.telefone),
        )
        self.conexao.commit()
        cliente.id = cursor.lastrowid
        return cliente

    def existe_telefone(self, telefone):
        return self.conexao.execute(
            "SELECT 1 FROM cliente WHERE telefone = ?", (telefone,)
        ).fetchone() is not None

    def listar(self, busca=""):
        return self.conexao.execute(
            """SELECT id, nome, telefone, criado_em FROM cliente
               WHERE nome LIKE ? ORDER BY nome COLLATE NOCASE""",
            (f"%{busca.strip()}%",),
        ).fetchall()

    def buscar_por_id(self, cliente_id):
        linha = self.conexao.execute(
            "SELECT id, nome, telefone, criado_em FROM cliente WHERE id = ?", (cliente_id,)
        ).fetchone()
        return Cliente(**dict(linha)) if linha else None


class ProfissionalRepositorio:
    def __init__(self, conexao):
        self.conexao = conexao

    def listar_ativos(self):
        linhas = self.conexao.execute(
            "SELECT id, nome, ativo FROM profissional WHERE ativo = 1 ORDER BY nome"
        ).fetchall()
        return [Profissional(**dict(l)) for l in linhas]

    def buscar_por_id(self, profissional_id):
        linha = self.conexao.execute(
            "SELECT id, nome, ativo FROM profissional WHERE id = ? AND ativo = 1",
            (profissional_id,),
        ).fetchone()
        return Profissional(**dict(linha)) if linha else None


class ServicoRepositorio:
    def __init__(self, conexao):
        self.conexao = conexao

    def listar(self):
        linhas = self.conexao.execute(
            "SELECT id, nome, duracao_minutos, preco FROM servico ORDER BY nome"
        ).fetchall()
        return [Servico(**dict(l)) for l in linhas]

    def buscar_por_id(self, servico_id):
        linha = self.conexao.execute(
            "SELECT id, nome, duracao_minutos, preco FROM servico WHERE id = ?",
            (servico_id,),
        ).fetchone()
        return Servico(**dict(linha)) if linha else None


class AgendamentoRepositorio:
    def __init__(self, conexao):
        self.conexao = conexao

    def buscar_conflito(self, ag):
        """Procura um agendamento ativo do mesmo profissional cujo intervalo
        se sobreponha ao novo: inicio_existente < fim_novo E fim_existente > inicio_novo."""
        return self.conexao.execute(
            """SELECT a.hora_inicio, a.hora_fim, c.nome AS cliente
               FROM agendamento a JOIN cliente c ON c.id = a.cliente_id
               WHERE a.profissional_id = ? AND a.data = ? AND a.status = 'AGENDADO'
                 AND a.hora_inicio < ? AND a.hora_fim > ?
               LIMIT 1""",
            (ag.profissional_id, ag.data, ag.hora_fim, ag.hora_inicio),
        ).fetchone()

    def salvar_se_disponivel(self, ag):
        """Verifica o conflito e grava na MESMA transação (BEGIN IMMEDIATE),
        impedindo que dois atendentes reservem o mesmo horário ao mesmo tempo.
        Retorna None em caso de sucesso ou a linha do agendamento em conflito."""
        try:
            self.conexao.execute("BEGIN IMMEDIATE")
            conflito = self.buscar_conflito(ag)
            if conflito:
                self.conexao.rollback()
                return conflito
            cursor = self.conexao.execute(
                """INSERT INTO agendamento
                   (cliente_id, profissional_id, servico_id, usuario_id,
                    data, hora_inicio, hora_fim, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 'AGENDADO')""",
                (ag.cliente_id, ag.profissional_id, ag.servico_id, ag.usuario_id,
                 ag.data, ag.hora_inicio, ag.hora_fim),
            )
            self.conexao.commit()
            ag.id = cursor.lastrowid
            return None
        except Exception:
            self.conexao.rollback()
            raise

    def listar_por_data(self, data, profissional_id=None):
        sql = """SELECT a.id, a.data, a.hora_inicio, a.hora_fim, a.status,
                        c.nome AS cliente, c.telefone,
                        s.nome AS servico, s.preco,
                        p.nome AS profissional
                 FROM agendamento a
                 JOIN cliente c      ON c.id = a.cliente_id
                 JOIN servico s      ON s.id = a.servico_id
                 JOIN profissional p ON p.id = a.profissional_id
                 WHERE a.data = ?"""
        parametros = [data]
        if profissional_id:
            sql += " AND a.profissional_id = ?"
            parametros.append(profissional_id)
        sql += " ORDER BY a.hora_inicio, p.nome"
        return self.conexao.execute(sql, parametros).fetchall()

    def buscar_por_id(self, agendamento_id):
        return self.conexao.execute(
            "SELECT id, data, status FROM agendamento WHERE id = ?", (agendamento_id,)
        ).fetchone()

    def cancelar(self, agendamento_id):
        cursor = self.conexao.execute(
            "UPDATE agendamento SET status = 'CANCELADO' WHERE id = ? AND status = 'AGENDADO'",
            (agendamento_id,),
        )
        self.conexao.commit()
        return cursor.rowcount == 1

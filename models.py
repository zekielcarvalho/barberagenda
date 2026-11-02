"""Classes de domínio do sistema (correspondem ao Diagrama de Classes)."""
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional

from werkzeug.security import check_password_hash

HORA_ABERTURA = "09:00"
HORA_FECHAMENTO = "19:00"


def somente_digitos(texto):
    return re.sub(r"\D", "", texto or "")


def formatar_telefone(numero):
    numero = somente_digitos(numero)
    if len(numero) == 11:
        return f"({numero[:2]}) {numero[2:7]}-{numero[7:]}"
    if len(numero) == 10:
        return f"({numero[:2]}) {numero[2:6]}-{numero[6:]}"
    return numero


def normalizar_hora(texto):
    """Aceita 'HH:MM' ou 'HH:MM:SS' e devolve 'HH:MM' (ou None se inválida)."""
    try:
        return datetime.strptime((texto or "").strip()[:5], "%H:%M").strftime("%H:%M")
    except ValueError:
        return None


@dataclass
class Usuario:
    id: int
    nome: str
    login: str
    senha_hash: str

    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha or "")


@dataclass
class Cliente:
    nome: str
    telefone: str
    id: Optional[int] = None
    criado_em: Optional[str] = None

    def __post_init__(self):
        self.nome = " ".join((self.nome or "").split())   # remove espaços extras
        self.telefone = somente_digitos(self.telefone)

    def validar(self):
        erros = []
        if not self.nome:
            erros.append("O nome do cliente é obrigatório.")
        elif len(self.nome) < 3:
            erros.append("O nome deve ter pelo menos 3 caracteres.")
        elif len(self.nome) > 100:
            erros.append("O nome deve ter no máximo 100 caracteres.")
        if not self.telefone:
            erros.append("O telefone é obrigatório.")
        elif len(self.telefone) not in (10, 11):
            erros.append("Informe um telefone válido com DDD (10 ou 11 dígitos).")
        return erros


@dataclass
class Profissional:
    id: int
    nome: str
    ativo: bool = True


@dataclass
class Servico:
    id: int
    nome: str
    duracao_minutos: int
    preco: float


@dataclass
class Agendamento:
    cliente_id: Optional[int]
    profissional_id: Optional[int]
    servico_id: Optional[int]
    data: str
    hora_inicio: Optional[str]
    usuario_id: Optional[int] = None
    hora_fim: Optional[str] = None
    status: str = "AGENDADO"
    id: Optional[int] = None

    def calcular_hora_fim(self, duracao_minutos):
        inicio = datetime.strptime(self.hora_inicio, "%H:%M")
        self.hora_fim = (inicio + timedelta(minutes=duracao_minutos)).strftime("%H:%M")
        return self.hora_fim

    def validar(self, hoje: date):
        erros = []
        if not self.cliente_id:
            erros.append("Selecione o cliente.")
        if not self.servico_id:
            erros.append("Selecione o serviço.")
        if not self.profissional_id:
            erros.append("Selecione o profissional.")
        try:
            dia = date.fromisoformat(self.data or "")
            if dia < hoje:
                erros.append("Não é possível agendar em uma data passada.")
        except ValueError:
            erros.append("Informe uma data válida.")
        if not self.hora_inicio:
            erros.append("Informe um horário válido.")
        elif self.hora_inicio < HORA_ABERTURA or (self.hora_fim and self.hora_fim > HORA_FECHAMENTO):
            erros.append(f"O atendimento deve ocorrer entre {HORA_ABERTURA} e {HORA_FECHAMENTO}.")
        return erros

    def cancelar(self):
        self.status = "CANCELADO"

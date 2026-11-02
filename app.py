"""BarberAgenda - Sistema de agendamento para barbearia.

Executar:  python app.py   e abrir  http://127.0.0.1:5000
Usuário de demonstração: atendente / barbearia123
"""
import os
from datetime import date
from functools import wraps

from flask import (Flask, abort, flash, redirect, render_template, request,
                   session, url_for)

import database
from models import Agendamento, Cliente, formatar_telefone, normalizar_hora
from repositorio import (AgendamentoRepositorio, ClienteRepositorio,
                         ProfissionalRepositorio, ServicoRepositorio,
                         UsuarioRepositorio)


def para_inteiro(valor):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def login_obrigatorio(rota):
    """RNF01: só usuários autenticados acessam as telas do sistema."""
    @wraps(rota)
    def verificar(*args, **kwargs):
        if "usuario_id" not in session:
            flash("Faça login para acessar o sistema.", "erro")
            return redirect(url_for("login", proximo=request.path))
        return rota(*args, **kwargs)
    return verificar


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "troque-esta-chave-em-producao"),
        DATABASE=os.path.join(database.PASTA, "barbearia.db"),
    )
    if config:
        app.config.update(config)
    database.registrar(app)

    # ---------- filtros usados nos templates ----------
    app.add_template_filter(formatar_telefone, "telefone")

    @app.template_filter("data_br")
    def data_br(valor):
        try:
            return date.fromisoformat(valor[:10]).strftime("%d/%m/%Y")
        except (TypeError, ValueError):
            return valor

    @app.template_filter("moeda")
    def moeda(valor):
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    # ---------- RF01 - Autenticar atendente ----------
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            usuario = UsuarioRepositorio(database.obter_conexao()).buscar_por_login(
                request.form.get("login"))
            if usuario and usuario.verificar_senha(request.form.get("senha")):
                session.clear()
                session["usuario_id"] = usuario.id
                session["usuario_nome"] = usuario.nome
                proximo = request.args.get("proximo", "")
                return redirect(proximo if proximo.startswith("/") else url_for("agenda"))
            flash("Usuário ou senha inválidos.", "erro")
            return render_template("login.html", login=request.form.get("login", "")), 401
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        flash("Você saiu do sistema.", "sucesso")
        return redirect(url_for("login"))

    @app.route("/")
    @login_obrigatorio
    def inicio():
        return redirect(url_for("agenda"))

    # ---------- RF02 - Cadastrar cliente ----------
    @app.route("/clientes/novo", methods=["GET", "POST"])
    @login_obrigatorio
    def novo_cliente():
        if request.method == "POST":
            cliente = Cliente(nome=request.form.get("nome"),
                              telefone=request.form.get("telefone"))
            repositorio = ClienteRepositorio(database.obter_conexao())
            erros = cliente.validar()
            if not erros and repositorio.existe_telefone(cliente.telefone):
                erros.append("Já existe um cliente cadastrado com este telefone.")
            if erros:
                for erro in erros:
                    flash(erro, "erro")
                return render_template("cliente_form.html", form=request.form), 400
            repositorio.salvar(cliente)
            flash(f"Cliente {cliente.nome} cadastrado com sucesso!", "sucesso")
            return redirect(url_for("clientes"))
        return render_template("cliente_form.html", form={})

    # ---------- RF03 - Consultar clientes ----------
    @app.route("/clientes")
    @login_obrigatorio
    def clientes():
        busca = request.args.get("busca", "")
        lista = ClienteRepositorio(database.obter_conexao()).listar(busca)
        return render_template("clientes.html", clientes=lista, busca=busca)

    # ---------- RF04 - Agendar horário ----------
    @app.route("/agendamentos/novo", methods=["GET", "POST"])
    @login_obrigatorio
    def novo_agendamento():
        conexao = database.obter_conexao()
        clientes_repo = ClienteRepositorio(conexao)
        servicos_repo = ServicoRepositorio(conexao)
        profissionais_repo = ProfissionalRepositorio(conexao)
        contexto = dict(clientes=clientes_repo.listar(),
                        servicos=servicos_repo.listar(),
                        profissionais=profissionais_repo.listar_ativos(),
                        hoje=date.today().isoformat())

        if request.method == "POST":
            agendamento = Agendamento(
                cliente_id=para_inteiro(request.form.get("cliente_id")),
                profissional_id=para_inteiro(request.form.get("profissional_id")),
                servico_id=para_inteiro(request.form.get("servico_id")),
                data=request.form.get("data", ""),
                hora_inicio=normalizar_hora(request.form.get("hora")),
                usuario_id=session["usuario_id"],
            )
            servico = servicos_repo.buscar_por_id(agendamento.servico_id)
            profissional = profissionais_repo.buscar_por_id(agendamento.profissional_id)
            cliente = clientes_repo.buscar_por_id(agendamento.cliente_id)
            if servico and agendamento.hora_inicio:
                agendamento.calcular_hora_fim(servico.duracao_minutos)

            erros = agendamento.validar(date.today())
            if agendamento.cliente_id and not cliente:
                erros.append("Cliente não encontrado.")
            if agendamento.servico_id and not servico:
                erros.append("Serviço não encontrado.")
            if agendamento.profissional_id and not profissional:
                erros.append("Profissional não encontrado.")

            if not erros:
                conflito = AgendamentoRepositorio(conexao).salvar_se_disponivel(agendamento)
                if conflito:
                    erros.append(
                        f"Horário indisponível: {profissional.nome} já tem atendimento "
                        f"das {conflito['hora_inicio']} às {conflito['hora_fim']} nesta data. "
                        "Escolha outro horário ou profissional.")
            if erros:
                for erro in erros:
                    flash(erro, "erro")
                return render_template("agendamento_form.html", form=request.form, **contexto), 400

            flash(f"Agendamento confirmado: {cliente.nome} - {servico.nome} com "
                  f"{profissional.nome} em {data_br(agendamento.data)} às "
                  f"{agendamento.hora_inicio}.", "sucesso")
            return redirect(url_for("agenda", data=agendamento.data))

        form = {"cliente_id": request.args.get("cliente_id", ""), "data": contexto["hoje"]}
        return render_template("agendamento_form.html", form=form, **contexto)

    # ---------- RF05 - Consultar agenda do dia ----------
    @app.route("/agenda")
    @login_obrigatorio
    def agenda():
        data = request.args.get("data") or date.today().isoformat()
        try:
            date.fromisoformat(data)
        except ValueError:
            flash("Data inválida. Exibindo a agenda de hoje.", "erro")
            data = date.today().isoformat()
        profissional_id = para_inteiro(request.args.get("profissional_id"))
        conexao = database.obter_conexao()
        itens = AgendamentoRepositorio(conexao).listar_por_data(data, profissional_id)
        ativos = [i for i in itens if i["status"] == "AGENDADO"]
        resumo = {"ativos": len(ativos),
                  "cancelados": len(itens) - len(ativos),
                  "previsto": sum(i["preco"] for i in ativos)}
        return render_template("agenda.html", itens=itens, data=data, resumo=resumo,
                               profissionais=ProfissionalRepositorio(conexao).listar_ativos(),
                               profissional_id=profissional_id)

    # ---------- RF06 - Cancelar agendamento ----------
    @app.route("/agendamentos/<int:agendamento_id>/cancelar", methods=["POST"])
    @login_obrigatorio
    def cancelar_agendamento(agendamento_id):
        repositorio = AgendamentoRepositorio(database.obter_conexao())
        agendamento = repositorio.buscar_por_id(agendamento_id)
        if agendamento is None:
            abort(404)
        if repositorio.cancelar(agendamento_id):
            flash("Agendamento cancelado. O horário foi liberado.", "sucesso")
        else:
            flash("Este agendamento já estava cancelado.", "erro")
        return redirect(url_for("agenda", data=agendamento["data"]))

    return app


if __name__ == "__main__":
    create_app().run(debug=True)

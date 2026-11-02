# BarberAgenda — Sistema de agendamento para barbearia

Projeto Integrado Interdisciplinar. Sistema web simples para o atendente de uma barbearia cadastrar clientes, agendar horários sem conflito, consultar a agenda do dia e cancelar atendimentos.

## Funcionalidades

| Código | Funcionalidade | Usa o banco |
|---|---|---|
| RF01 | Login e logout do atendente | Sim (tabela `usuario`, senha com hash) |
| RF02 | Cadastro de cliente com validação | Sim (INSERT em `cliente`) |
| RF03 | Lista e busca de clientes | Sim (SELECT em `cliente`) |
| RF04 | Agendamento com verificação de disponibilidade | Sim (SELECT de conflito + INSERT em `agendamento`) |
| RF05 | Agenda do dia com filtro e resumo | Sim (SELECT com JOIN) |
| RF06 | Cancelamento de agendamento | Sim (UPDATE do status) |

## Tecnologias

Python 3.10+, Flask 3, SQLite 3, HTML/CSS (Jinja2) e pytest.

## Como executar

```bash
pip install -r requirements.txt
python app.py
```

Abra `http://127.0.0.1:5000` e entre com **usuário** `atendente` e **senha** `barbearia123`.

O arquivo `barbearia.db` é criado automaticamente na primeira execução, já com o usuário de demonstração, dois profissionais e quatro serviços.

## Testes automatizados

```bash
python -m pytest -v
```

São 15 testes, um para cada caso do plano de testes (CT01 a CT15). Cada teste usa um banco temporário e não altera os dados reais.

## Ver os dados gravados no banco

```bash
python consultar_banco.py
```

## Estrutura

```
app.py              rotas e controle (Flask)
models.py           classes de domínio e validações
repositorio.py      acesso ao banco com SQL parametrizado
database.py         conexão, criação das tabelas e dados iniciais
schema.sql          script das tabelas (MER)
consultar_banco.py  exibe os dados gravados
templates/          telas HTML
static/style.css    estilo responsivo
tests/              testes automatizados (pytest)
```

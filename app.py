"""Aplicação web Avenzi (Flask).

Cada função abaixo é uma ROTA: responde a um endereço do site.
As rotas só leem o formulário, chamam a Loja e mostram uma página.
Os erros são tratados em um só lugar (no final do arquivo).
"""
import os

from flask import Flask, flash, redirect, render_template, request, session
from werkzeug.exceptions import HTTPException

from excecoes import DadosInvalidosError, NegocioError
from loja import Loja
from repositorio import Repositorio

app = Flask(__name__)
app.secret_key = "avenzi-trabalho-poo"

PASTA = os.path.dirname(os.path.abspath(__file__))
loja = Loja(Repositorio(os.path.join(PASTA, "dados.json")))


# ---------------- FUNÇÕES AUXILIARES ----------------
def usuario_logado():
    id = session.get("usuario_id")
    return loja.buscar_usuario(id) if id else None


def converter_inteiro(valor, nome):
    try:
        return int(valor)
    except (TypeError, ValueError):
        raise DadosInvalidosError(f'O campo "{nome}" deve ser um número inteiro.')


def numero_inteiro(campo, nome):
    return converter_inteiro(request.form.get(campo, ""), nome)


def numero_decimal(campo, nome):
    try:
        return float(request.form.get(campo, "").replace(",", "."))
    except ValueError:
        raise DadosInvalidosError(f'O campo "{nome}" deve ser um número (ex.: 39,90).')


@app.context_processor
def variaveis_das_paginas():
    """Deixa o usuário logado disponível em todas as páginas."""
    return {"usuario": usuario_logado()}


@app.template_filter("dinheiro")
def formatar_dinheiro(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ---------------- LOGIN E CADASTRO ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = loja.autenticar(request.form["email"], request.form["senha"])
        session["usuario_id"] = usuario.id
        flash(f"Bem-vindo(a), {usuario.nome}!", "sucesso")
        return redirect("/admin/pedidos" if usuario.eh_administrador() else "/")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        f = request.form
        cliente = loja.cadastrar_cliente(f["nome"], f["email"], f["senha"],
                                         f["cpf"], f["telefone"], f["endereco"])
        session["usuario_id"] = cliente.id
        flash("Cadastro realizado com sucesso!", "sucesso")
        return redirect("/")
    return render_template("cadastro.html")


@app.route("/meus-dados", methods=["GET", "POST"])
def meus_dados():
    usuario = usuario_logado()
    loja.exigir_permissao(usuario, "GERENCIAR_PROPRIOS_DADOS")
    if request.method == "POST":
        loja.atualizar_meus_dados(usuario, request.form["nome"], request.form["email"],
                                  request.form.get("nova_senha", ""))
        flash("Dados atualizados.", "sucesso")
        return redirect("/meus-dados")
    return render_template("meus_dados.html")


# ---------------- LOJA (CLIENTE) ----------------
@app.route("/")
def vitrine():
    termo = request.args.get("busca", "")
    return render_template("vitrine.html", produtos=loja.pesquisar_produtos(termo), busca=termo)


@app.route("/carrinho")
def carrinho():
    cliente = usuario_logado()
    loja.exigir_permissao(cliente, "ADICIONAR_AO_CARRINHO")
    return render_template("carrinho.html", carrinho=cliente.obter_carrinho())


@app.route("/carrinho/adicionar", methods=["POST"])
def adicionar_ao_carrinho():
    loja.adicionar_ao_carrinho(usuario_logado(), numero_inteiro("produto_id", "Produto"),
                               numero_inteiro("quantidade", "Quantidade"))
    flash("Produto adicionado ao carrinho.", "sucesso")
    return redirect("/carrinho")


@app.route("/carrinho/remover", methods=["POST"])
def remover_do_carrinho():
    loja.remover_do_carrinho(usuario_logado(), numero_inteiro("produto_id", "Produto"))
    flash("Produto removido do carrinho.", "sucesso")
    return redirect("/carrinho")


@app.route("/pedido/finalizar", methods=["POST"])
def finalizar_pedido():
    pedido = loja.finalizar_pedido(usuario_logado())
    flash(f"Pedido nº {pedido.id} realizado! Aguardando pagamento.", "sucesso")
    return redirect("/meus-pedidos")


@app.route("/meus-pedidos")
def meus_pedidos():
    cliente = usuario_logado()
    loja.exigir_permissao(cliente, "CONSULTAR_PROPRIOS_PEDIDOS")
    pedidos = sorted(cliente.consultar_pedidos(), key=lambda p: p.id, reverse=True)
    return render_template("meus_pedidos.html", pedidos=pedidos)


@app.route("/pedido/cancelar", methods=["POST"])
def cancelar_meu_pedido():
    loja.cancelar_pedido_do_cliente(usuario_logado(), numero_inteiro("pedido_id", "Pedido"))
    flash("Pedido cancelado.", "sucesso")
    return redirect("/meus-pedidos")


# ---------------- ADMINISTRAÇÃO: PRODUTOS E ESTOQUE ----------------
@app.route("/admin/produtos")
def admin_produtos():
    loja.exigir_permissao(usuario_logado(), "GERENCIAR_PRODUTOS")
    termo = request.args.get("busca", "")
    produtos = loja.pesquisar_produtos(termo, somente_ativos=False)
    return render_template("admin_produtos.html", produtos=produtos, busca=termo)


@app.route("/admin/produto")
def admin_produto_form():
    loja.exigir_permissao(usuario_logado(), "GERENCIAR_PRODUTOS")
    id = request.args.get("id")
    produto = loja.buscar_produto(converter_inteiro(id, "Produto")) if id else None
    return render_template("admin_produto_form.html", produto=produto)


@app.route("/admin/produto/salvar", methods=["POST"])
def admin_produto_salvar():
    usuario = usuario_logado()
    f = request.form
    preco = numero_decimal("preco", "Preço")
    quantidade = numero_inteiro("quantidade", "Quantidade em estoque")
    if f.get("id"):
        loja.alterar_produto(usuario, numero_inteiro("id", "Produto"), f["nome"], f["descricao"], preco, quantidade)
        flash("Produto alterado.", "sucesso")
    else:
        loja.cadastrar_produto(usuario, f["nome"], f["descricao"], preco, quantidade)
        flash("Produto cadastrado.", "sucesso")
    return redirect("/admin/produtos")


@app.route("/admin/produto/inativar", methods=["POST"])
def admin_produto_inativar():
    loja.inativar_produto(usuario_logado(), numero_inteiro("produto_id", "Produto"))
    flash("Produto inativado.", "sucesso")
    return redirect("/admin/produtos")


@app.route("/admin/produto/ativar", methods=["POST"])
def admin_produto_ativar():
    loja.ativar_produto(usuario_logado(), numero_inteiro("produto_id", "Produto"))
    flash("Produto reativado.", "sucesso")
    return redirect("/admin/produtos")


# ---------------- ADMINISTRAÇÃO: PEDIDOS, PAGAMENTOS E ENTREGAS ----------------
@app.route("/admin/pedidos")
def admin_pedidos():
    pedidos = loja.listar_pedidos(usuario_logado())
    status = request.args.get("status", "")
    if status:
        pedidos = [p for p in pedidos if p.status == status]
    return render_template("admin_pedidos.html", pedidos=pedidos, filtro=status)


@app.route("/admin/pedido/<acao>", methods=["POST"])
def admin_pedido_acao(acao):
    admin = usuario_logado()
    pedido_id = numero_inteiro("pedido_id", "Pedido")
    if acao == "pagamento":
        loja.registrar_pagamento(admin, pedido_id, numero_decimal("valor", "Valor pago"))
        flash(f"Pagamento do pedido nº {pedido_id} registrado.", "sucesso")
    elif acao == "preparar":
        loja.preparar_pedido(admin, pedido_id)
        flash(f"Pedido nº {pedido_id} em preparação.", "sucesso")
    elif acao == "enviar":
        loja.enviar_pedido(admin, pedido_id, request.form.get("codigo_rastreio", ""))
        flash(f"Pedido nº {pedido_id} enviado.", "sucesso")
    elif acao == "concluir":
        loja.concluir_pedido(admin, pedido_id)
        flash(f"Pedido nº {pedido_id} concluído.", "sucesso")
    elif acao == "cancelar":
        loja.cancelar_pedido(admin, pedido_id)
        flash(f"Pedido nº {pedido_id} cancelado.", "sucesso")
    return redirect(request.referrer or "/admin/pedidos")


# ---------------- TRATAMENTO DE ERROS ----------------
@app.errorhandler(NegocioError)
def tratar_erro_de_negocio(erro):
    """Qualquer erro de regra de negócio vira uma mensagem amigável na tela."""
    flash(str(erro), "erro")
    if request.method == "POST":
        return redirect(request.referrer or "/")
    if usuario_logado() is None and request.path != "/login":
        return redirect("/login")
    return redirect("/")


@app.errorhandler(Exception)
def tratar_erro_inesperado(erro):
    """Erro não previsto: mostra mensagem genérica, sem detalhes técnicos."""
    if isinstance(erro, HTTPException):
        return erro  # ex.: página 404 normal
    app.logger.exception(erro)  # o detalhe técnico fica só no terminal
    return render_template("erro.html"), 500


if __name__ == "__main__":
    print("Acesse http://localhost:5000")
    app.run(debug=False)

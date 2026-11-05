"""Persistência em JSON: transforma os objetos em dicionários e grava no arquivo.

Ao carregar, faz o caminho inverso e religa os relacionamentos
(ex.: o item do pedido guarda só o id do produto, e aqui buscamos o objeto).
"""
import json
import os
from datetime import datetime

from excecoes import PersistenciaError
from modelo import (Administrador, Carrinho, Cliente, Entrega, ItemCarrinho, ItemPedido,
                    Pagamento, Pedido, Produto)


class Repositorio:

    def __init__(self, caminho_arquivo):
        self.caminho_arquivo = caminho_arquivo

    # ---------------- SALVAR ----------------
    def salvar(self, loja):
        dados = {
            "ultimo_id": loja.ultimo_id,
            "produtos": [self._produto_para_dict(p) for p in loja.produtos],
            "usuarios": [self._usuario_para_dict(u) for u in loja.usuarios],
            "pedidos": [self._pedido_para_dict(p) for p in loja.pedidos],
        }
        temporario = self.caminho_arquivo + ".tmp"
        try:
            # grava num arquivo temporário e depois troca, para não corromper o original
            with open(temporario, "w", encoding="utf-8") as arquivo:
                json.dump(dados, arquivo, ensure_ascii=False, indent=2)
            os.replace(temporario, self.caminho_arquivo)
        except OSError as erro:
            raise PersistenciaError("Não foi possível salvar os dados.") from erro

    def _produto_para_dict(self, p):
        return {"id": p.id, "nome": p.nome, "descricao": p.descricao, "preco": p.preco,
                "ativo": p.ativo, "quantidade": p.estoque.consultar_quantidade()}

    def _usuario_para_dict(self, u):
        dados = {"id": u.id, "nome": u.nome, "email": u.email, "senha": u.senha, "ativo": u.ativo}
        if isinstance(u, Cliente):
            dados["tipo"] = "cliente"
            dados["cpf"] = u.cpf
            dados["telefone"] = u.telefone
            dados["endereco"] = u.endereco
            if u.carrinho:
                dados["carrinho"] = [{"produto_id": i.produto.id, "quantidade": i.quantidade,
                                      "preco_unitario": i.preco_unitario} for i in u.carrinho.itens]
        else:
            dados["tipo"] = "administrador"
        return dados

    def _pedido_para_dict(self, p):
        dados = {
            "id": p.id, "cliente_id": p.cliente.id, "data": p.data.isoformat(),
            "valor_total": p.valor_total, "status": p.status,
            "itens": [{"produto_id": i.produto.id, "quantidade": i.quantidade,
                       "preco_unitario": i.preco_unitario} for i in p.itens],
            "pagamento": None, "entrega": None,
        }
        if p.pagamento:
            dados["pagamento"] = {"id": p.pagamento.id, "valor": p.pagamento.valor,
                                  "status": p.pagamento.status,
                                  "data": p.pagamento.data.isoformat() if p.pagamento.data else None}
        if p.entrega:
            dados["entrega"] = {"id": p.entrega.id, "endereco": p.entrega.endereco,
                                "codigo_rastreio": p.entrega.codigo_rastreio,
                                "status": p.entrega.status}
        return dados

    # ---------------- CARREGAR ----------------
    def carregar(self, loja):
        """Preenche a loja com os dados do arquivo. Retorna False se o arquivo não existe."""
        if not os.path.exists(self.caminho_arquivo):
            return False
        try:
            with open(self.caminho_arquivo, encoding="utf-8") as arquivo:
                dados = json.load(arquivo)

            loja.ultimo_id = dados["ultimo_id"]

            produtos = {}
            for d in dados["produtos"]:
                produto = Produto(d["id"], d["nome"], d["descricao"], d["preco"],
                                  d["quantidade"], d["ativo"])
                produtos[produto.id] = produto
            loja.produtos = list(produtos.values())

            clientes = {}
            loja.usuarios = []
            for d in dados["usuarios"]:
                if d["tipo"] == "cliente":
                    usuario = Cliente(d["id"], d["nome"], d["email"], d["senha"], d["cpf"],
                                      d["telefone"], d["endereco"], d["ativo"])
                    if "carrinho" in d:
                        carrinho = usuario.obter_carrinho()
                        for i in d["carrinho"]:
                            carrinho.itens.append(ItemCarrinho(produtos[i["produto_id"]],
                                                               i["quantidade"], i["preco_unitario"]))
                        carrinho.calcular_total()
                    clientes[usuario.id] = usuario
                else:
                    usuario = Administrador(d["id"], d["nome"], d["email"], d["senha"], d["ativo"])
                loja.usuarios.append(usuario)

            loja.pedidos = []
            for d in dados["pedidos"]:
                cliente = clientes[d["cliente_id"]]
                itens = [ItemPedido(produtos[i["produto_id"]], i["quantidade"], i["preco_unitario"])
                         for i in d["itens"]]
                pedido = Pedido(d["id"], cliente, itens)
                pedido.data = datetime.fromisoformat(d["data"])
                pedido.valor_total = d["valor_total"]
                pedido.status = d["status"]
                if d["pagamento"]:
                    pg = d["pagamento"]
                    data = datetime.fromisoformat(pg["data"]) if pg["data"] else None
                    pedido.pagamento = Pagamento(pg["id"], pg["valor"], data, pg["status"])
                if d["entrega"]:
                    en = d["entrega"]
                    pedido.entrega = Entrega(en["id"], en["endereco"], en["codigo_rastreio"], en["status"])
                cliente.pedidos.append(pedido)
                loja.pedidos.append(pedido)
            return True
        except (OSError, ValueError, KeyError) as erro:
            raise PersistenciaError("Não foi possível carregar os dados salvos.") from erro

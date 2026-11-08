from excecoes import DadosInvalidosError, OperacaoNaoPermitidaError, RegistroNaoEncontradoError


class ItemCarrinho:
    """Um produto dentro do carrinho (COMPOSIÇÃO: só existe dentro do Carrinho)."""

    def __init__(self, produto, quantidade, preco_unitario=None):
        self.produto = produto  # associação: o item refere-se a 1 produto
        self._quantidade = quantidade
        self._preco_unitario = produto.preco if preco_unitario is None else preco_unitario

    @property
    def quantidade(self):
        return self._quantidade

    @property
    def preco_unitario(self):
        return self._preco_unitario

    def alterar_quantidade(self, quantidade):
        if quantidade <= 0:
            raise DadosInvalidosError("A quantidade deve ser maior que zero.")
        self._quantidade = quantidade

    def calcular_subtotal(self):
        return self._quantidade * self._preco_unitario


class Carrinho:
    """Produtos escolhidos antes de fazer o pedido."""

    def __init__(self, id):
        self._id = id
        self._valor_total = 0.0
        self.itens = []  # COMPOSIÇÃO: os itens são criados aqui dentro

    @property
    def id(self):
        return self._id

    @property
    def valor_total(self):
        # somente leitura: o total é sempre calculado por calcular_total()
        return self._valor_total

    # SOBRECARGA (estilo Python): quantidade é opcional.
    #   adicionar_produto(produto)      -> adiciona 1 unidade
    #   adicionar_produto(produto, 3)   -> adiciona 3 unidades
    def adicionar_produto(self, produto, quantidade=1):
        if quantidade <= 0:
            raise DadosInvalidosError("A quantidade deve ser maior que zero.")
        produto.consultar()  # RN01 — lança erro se o produto estiver inativo

        item = self._buscar_item(produto)
        quantidade_final = (item.quantidade if item else 0) + quantidade

        # RN03 — não pode passar do estoque disponível
        disponivel = produto.estoque.consultar_quantidade()
        if quantidade_final > disponivel:
            raise OperacaoNaoPermitidaError(
                f'Estoque insuficiente para "{produto.nome}". Disponível: {disponivel}.')

        if item:
            item.alterar_quantidade(quantidade_final)
        else:
            self.itens.append(ItemCarrinho(produto, quantidade))
        self.calcular_total()

    def remover_produto(self, produto):
        item = self._buscar_item(produto)
        if item is None:
            raise RegistroNaoEncontradoError("Este produto não está no carrinho.")
        self.itens.remove(item)
        self.calcular_total()

    def calcular_total(self):
        self._valor_total = sum(item.calcular_subtotal() for item in self.itens)
        return self._valor_total

    def esvaziar(self):
        self.itens = []
        self._valor_total = 0.0

    def _buscar_item(self, produto):
        for item in self.itens:
            if item.produto == produto:  # usa o __eq__ sobrecarregado em Produto
                return item
        return None

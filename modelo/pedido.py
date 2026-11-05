from datetime import datetime

from excecoes import DadosInvalidosError, EstadoInvalidoError, OperacaoNaoPermitidaError
from modelo.validacao import obrigatorio


class ItemPedido:
    """Um produto comprado (COMPOSIÇÃO: só existe dentro do Pedido)."""

    def __init__(self, produto, quantidade, preco_unitario):
        self.produto = produto
        self.quantidade = quantidade
        self.preco_unitario = preco_unitario  # preço no momento da compra

    def calcular_subtotal(self):
        return self.quantidade * self.preco_unitario


class Pagamento:
    """Pagamento de um pedido (Pedido 1 — 0..1 Pagamento)."""

    PENDENTE = "Pendente"
    CONFIRMADO = "Confirmado"

    def __init__(self, id, valor, data=None, status=PENDENTE):
        self.id = id
        self.valor = valor
        self.data = data
        self.status = status

    def registrar(self):
        if self.valor <= 0:
            raise DadosInvalidosError("O valor do pagamento deve ser maior que zero.")
        if self.status == Pagamento.CONFIRMADO:
            raise EstadoInvalidoError("Este pagamento já foi registrado.")
        self.data = datetime.now()
        self.atualizar_status(Pagamento.CONFIRMADO)

    def atualizar_status(self, status):
        obrigatorio(status, "Status do pagamento")
        self.status = status

    def esta_confirmado(self):
        return self.status == Pagamento.CONFIRMADO


class Entrega:
    """Envio de um pedido (Pedido 1 — 0..1 Entrega)."""

    ENVIADA = "Enviada"
    ENTREGUE = "Entregue"

    def __init__(self, id, endereco, codigo_rastreio=None, status=None):
        self.id = id
        self.endereco = endereco
        self.codigo_rastreio = codigo_rastreio
        self.status = status

    def registrar_envio(self, codigo_rastreio):
        obrigatorio(codigo_rastreio, "Código de rastreio")
        obrigatorio(self.endereco, "Endereço de entrega")
        self.codigo_rastreio = codigo_rastreio.strip().upper()
        self.atualizar_status(Entrega.ENVIADA)

    def atualizar_status(self, status):
        obrigatorio(status, "Status da entrega")
        self.status = status


class Pedido:
    """Uma compra. Fluxo: Aguardando pagamento → Pago → Em preparação → Enviado → Concluído."""

    AGUARDANDO_PAGAMENTO = "Aguardando pagamento"
    PAGO = "Pago"
    EM_PREPARACAO = "Em preparação"
    ENVIADO = "Enviado"
    CONCLUIDO = "Concluído"
    CANCELADO = "Cancelado"

    def __init__(self, id, cliente, itens=None):
        self.id = id
        self.cliente = cliente        # cada pedido pertence a 1 cliente
        self.itens = itens or []      # COMPOSIÇÃO
        self.data = None
        self.valor_total = 0.0
        self.status = None
        self.pagamento = None         # 0..1
        self.entrega = None           # 0..1

    @staticmethod
    def a_partir_do_carrinho(id, cliente, carrinho):
        """Monta o pedido copiando os itens do carrinho."""
        itens = [ItemPedido(i.produto, i.quantidade, i.preco_unitario) for i in carrinho.itens]
        return Pedido(id, cliente, itens)

    def criar(self):
        """Valida e confirma o pedido. Aqui ficam várias regras de negócio."""
        # RN07 — o pedido deve estar associado a um cliente
        if self.cliente is None:
            raise DadosInvalidosError("O pedido deve estar associado a um cliente.")
        # RN02 — o pedido deve ter pelo menos um produto
        if not self.itens:
            raise DadosInvalidosError("O pedido deve possuir pelo menos um produto.")
        for item in self.itens:
            produto = item.produto.consultar()  # RN01 — produto ativo
            if item.quantidade <= 0:
                raise DadosInvalidosError(f'Quantidade inválida para "{produto.nome}".')
            # RN03 — quantidade não pode ser maior que o estoque
            if item.quantidade > produto.estoque.consultar_quantidade():
                raise OperacaoNaoPermitidaError(f'Estoque insuficiente para "{produto.nome}".')

        # RN04 — o estoque é atualizado após a confirmação do pedido
        for item in self.itens:
            estoque = item.produto.estoque
            estoque.atualizar_quantidade(estoque.consultar_quantidade() - item.quantidade)

        self.data = datetime.now()
        self.status = Pedido.AGUARDANDO_PAGAMENTO
        self.calcular_total()
        self.cliente.pedidos.append(self)

    def cancelar(self):
        if self.status == Pedido.CANCELADO:
            raise EstadoInvalidoError("Este pedido já está cancelado.")
        if self.status in (Pedido.ENVIADO, Pedido.CONCLUIDO):
            raise EstadoInvalidoError("Não é possível cancelar um pedido que já foi enviado.")
        for item in self.itens:  # devolve os produtos ao estoque
            estoque = item.produto.estoque
            estoque.atualizar_quantidade(estoque.consultar_quantidade() + item.quantidade)
        self.status = Pedido.CANCELADO

    def atualizar_status(self, novo_status):
        """Avança o pedido respeitando a ordem do processo."""
        # RN06 — pedidos cancelados não podem ser enviados (nem alterados)
        if self.status == Pedido.CANCELADO:
            raise EstadoInvalidoError("Pedidos cancelados não podem ser alterados nem enviados.")

        pagamento_ok = self.pagamento is not None and self.pagamento.esta_confirmado()

        if novo_status == Pedido.PAGO:
            self._exigir_status(Pedido.AGUARDANDO_PAGAMENTO)
            if not pagamento_ok:
                raise EstadoInvalidoError("O pagamento ainda não foi registrado.")
        elif novo_status == Pedido.EM_PREPARACAO:
            # RN05 — só vai para preparação após o pagamento confirmado
            if not pagamento_ok:
                raise EstadoInvalidoError(
                    "O pedido só pode ir para preparação após a confirmação do pagamento.")
            self._exigir_status(Pedido.PAGO)
        elif novo_status == Pedido.ENVIADO:
            self._exigir_status(Pedido.EM_PREPARACAO)
        elif novo_status == Pedido.CONCLUIDO:
            self._exigir_status(Pedido.ENVIADO)
        else:
            raise DadosInvalidosError(f"Status inválido: {novo_status}")

        self.status = novo_status

    def _exigir_status(self, esperado):
        if self.status != esperado:
            raise EstadoInvalidoError(
                f'Ação não permitida: o pedido está "{self.status}", mas deveria estar "{esperado}".')

    def calcular_total(self):
        self.valor_total = sum(item.calcular_subtotal() for item in self.itens)
        return self.valor_total

from excecoes import DadosInvalidosError, EstadoInvalidoError, OperacaoNaoPermitidaError
from modelo.validacao import obrigatorio


class Estoque:
    """Controla a quantidade de UM produto (Produto 1 — 1 Estoque)."""

    def __init__(self, id, quantidade_disponivel=0):
        self.id = id
        self.quantidade_disponivel = 0
        self.atualizar_quantidade(quantidade_disponivel)

    def consultar_quantidade(self):
        return self.quantidade_disponivel

    def atualizar_quantidade(self, quantidade):
        if quantidade < 0:
            raise DadosInvalidosError("A quantidade em estoque não pode ser negativa.")
        self.quantidade_disponivel = quantidade


class Produto:
    """Produto impresso em 3D. A quantidade fica no Estoque, não aqui."""

    def __init__(self, id, nome, descricao, preco, quantidade=0, ativo=True):
        self.id = id
        self.nome = nome
        self.descricao = descricao
        self.preco = preco
        self.ativo = ativo
        self.estoque = Estoque(id, quantidade)

    def cadastrar(self):
        """Valida os dados do produto (RF03)."""
        obrigatorio(self.nome, "Nome")
        if self.preco <= 0:
            raise DadosInvalidosError("O preço deve ser maior que zero.")

    def alterar_dados(self, nome, descricao, preco):
        obrigatorio(nome, "Nome")
        if preco <= 0:
            raise DadosInvalidosError("O preço deve ser maior que zero.")
        self.nome = nome.strip()
        self.descricao = descricao
        self.preco = preco

    def inativar(self):
        if not self.ativo:
            raise EstadoInvalidoError("O produto já está inativo.")
        self.ativo = False

    def ativar(self):
        if self.ativo:
            raise EstadoInvalidoError("O produto já está ativo.")
        self.ativo = True

    def consultar(self):
        """RN01 — produto inativo não pode ser comprado."""
        if not self.ativo:
            raise OperacaoNaoPermitidaError(f'O produto "{self.nome}" não está disponível para compra.')
        return self

    # SOBRECARGA DE OPERADOR: define o que "produto1 == produto2" significa.
    # Dois produtos são iguais quando têm o mesmo id.
    def __eq__(self, outro):
        return isinstance(outro, Produto) and self.id == outro.id

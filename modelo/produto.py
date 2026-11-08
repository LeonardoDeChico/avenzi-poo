from excecoes import DadosInvalidosError, EstadoInvalidoError, OperacaoNaoPermitidaError
from modelo.validacao import obrigatorio


class Estoque:
    """Controla a quantidade de UM produto (Produto 1 — 1 Estoque)."""

    def __init__(self, id, quantidade_disponivel=0):
        self._id = id
        self._quantidade_disponivel = 0
        self.atualizar_quantidade(quantidade_disponivel)  # valida já na criação

    @property
    def id(self):
        return self._id

    @property
    def quantidade_disponivel(self):
        # ENCAPSULAMENTO: dá para ler, mas não dá para fazer
        # "estoque.quantidade_disponivel = -5". Só atualizar_quantidade() muda o valor.
        return self._quantidade_disponivel

    def consultar_quantidade(self):
        return self._quantidade_disponivel

    def atualizar_quantidade(self, quantidade):
        if quantidade < 0:
            raise DadosInvalidosError("A quantidade em estoque não pode ser negativa.")
        self._quantidade_disponivel = quantidade


class Produto:
    """Produto impresso em 3D. A quantidade fica no Estoque, não aqui."""

    def __init__(self, id, nome, descricao, preco, quantidade=0, ativo=True):
        # ENCAPSULAMENTO: atributos privados; mudam só por alterar_dados(),
        # inativar() e ativar(), que conferem as regras.
        self._id = id
        self._nome = nome
        self._descricao = descricao
        self._preco = preco
        self._ativo = ativo
        self._estoque = Estoque(id, quantidade)

    # ---- leitura (getters) ----
    @property
    def id(self):
        return self._id

    @property
    def nome(self):
        return self._nome

    @property
    def descricao(self):
        return self._descricao

    @property
    def preco(self):
        return self._preco

    @property
    def ativo(self):
        return self._ativo

    @property
    def estoque(self):
        return self._estoque

    # ---- comportamentos ----
    def definir_id(self, id):
        """O id é dado pela Loja uma única vez, depois que os dados foram validados."""
        if self._id is not None:
            raise EstadoInvalidoError("Este produto já possui identificador.")
        self._id = id
        # o estoque usa o mesmo número do produto
        self._estoque = Estoque(id, self._estoque.consultar_quantidade())

    def cadastrar(self):
        """Valida os dados do produto (RF03)."""
        obrigatorio(self._nome, "Nome")
        if self._preco <= 0:
            raise DadosInvalidosError("O preço deve ser maior que zero.")

    def alterar_dados(self, nome, descricao, preco):
        obrigatorio(nome, "Nome")
        if preco <= 0:
            raise DadosInvalidosError("O preço deve ser maior que zero.")
        self._nome = nome.strip()
        self._descricao = descricao
        self._preco = preco

    def inativar(self):
        if not self._ativo:
            raise EstadoInvalidoError("O produto já está inativo.")
        self._ativo = False

    def ativar(self):
        if self._ativo:
            raise EstadoInvalidoError("O produto já está ativo.")
        self._ativo = True

    def consultar(self):
        """RN01 — produto inativo não pode ser comprado."""
        if not self._ativo:
            raise OperacaoNaoPermitidaError(f'O produto "{self._nome}" não está disponível para compra.')
        return self

    # SOBRECARGA DE OPERADOR: define o que "produto1 == produto2" significa.
    # Dois produtos são iguais quando têm o mesmo id.
    def __eq__(self, outro):
        return isinstance(outro, Produto) and self._id == outro._id

    def __hash__(self):
        # quem redefine __eq__ precisa redefinir __hash__ junto (regra do Python)
        return hash(self._id)

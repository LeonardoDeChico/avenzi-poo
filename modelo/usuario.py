from abc import ABC, abstractmethod

from excecoes import EstadoInvalidoError
from modelo.validacao import obrigatorio, validar_email, validar_senha, validar_cpf


class Usuario(ABC):
    """Classe ABSTRATA: só existem Clientes ou Administradores (generalização)."""

    def __init__(self, id, nome, email, senha, ativo=True):
        # ENCAPSULAMENTO: atributos privados (prefixo _), como o "-" do diagrama.
        # De fora da classe só dá para LER (pelas @property abaixo);
        # para MUDAR é preciso chamar um método, que valida antes.
        self._id = id
        self._nome = nome
        self._email = email
        self._senha = senha
        self._ativo = ativo

    # ---- leitura (getters) ----
    @property
    def id(self):
        return self._id

    @property
    def nome(self):
        return self._nome

    @property
    def email(self):
        return self._email

    @property
    def senha(self):
        # somente leitura: usada pelo Repositorio para salvar no JSON
        return self._senha

    @property
    def ativo(self):
        return self._ativo

    # ---- comportamentos ----
    def definir_id(self, id):
        """O id é dado pela Loja uma única vez, depois que os dados foram validados."""
        if self._id is not None:
            raise EstadoInvalidoError("Este usuário já possui identificador.")
        self._id = id

    def autenticar(self, email, senha):
        return self._ativo and self._email.lower() == email.lower() and self._senha == senha

    # SOBRECARGA (estilo Python): o mesmo método aceita 2 ou 3 argumentos.
    #   atualizar_dados(nome, email)            -> muda nome e e-mail
    #   atualizar_dados(nome, email, nova_senha) -> muda também a senha
    def atualizar_dados(self, nome, email, nova_senha=None):
        obrigatorio(nome, "Nome")
        email = (email or "").strip()
        validar_email(email)
        if nova_senha:
            validar_senha(nova_senha)
            self._senha = nova_senha
        self._nome = nome.strip()
        self._email = email

    # POLIMORFISMO: cada subclasse implementa do seu jeito.
    @abstractmethod
    def obter_permissoes(self):
        pass

    def possui_permissao(self, permissao):
        # funciona para qualquer tipo de usuário, sem precisar saber qual é
        return permissao in self.obter_permissoes()

    def eh_administrador(self):
        return "GERENCIAR_PRODUTOS" in self.obter_permissoes()


class Cliente(Usuario):
    """Cliente que compra na Avenzi. HERDA de Usuario."""

    def __init__(self, id, nome, email, senha, cpf, telefone, endereco, ativo=True):
        super().__init__(id, nome, email, senha, ativo)
        self._cpf = cpf
        self._telefone = telefone
        self._endereco = endereco
        self.carrinho = None   # associação 0..1 carrinho
        self.pedidos = []      # associação 0..* pedidos

    @property
    def cpf(self):
        return self._cpf

    @property
    def telefone(self):
        return self._telefone

    @property
    def endereco(self):
        return self._endereco

    def cadastrar(self):
        """Valida os dados do cliente (RF01)."""
        obrigatorio(self._nome, "Nome")
        validar_email(self._email)
        validar_senha(self._senha)
        validar_cpf(self._cpf)
        obrigatorio(self._telefone, "Telefone")
        obrigatorio(self._endereco, "Endereço")

    def consultar_pedidos(self):
        return self.pedidos

    def obter_carrinho(self):
        from modelo.carrinho import Carrinho
        if self.carrinho is None:
            self.carrinho = Carrinho(self._id)
        return self.carrinho

    # POLIMORFISMO: sobrescreve o método da classe pai
    def obter_permissoes(self):
        return ["CONSULTAR_PRODUTOS", "ADICIONAR_AO_CARRINHO", "REALIZAR_PEDIDOS",
                "CONSULTAR_PROPRIOS_PEDIDOS", "GERENCIAR_PROPRIOS_DADOS"]


class Administrador(Usuario):
    """Responsável pela operação da loja. HERDA de Usuario."""

    def consultar_pedidos(self, pedidos):
        # mais recentes primeiro
        return sorted(pedidos, key=lambda p: p.id, reverse=True)

    def consultar_estoque(self, produtos):
        return [produto.estoque for produto in produtos]

    # POLIMORFISMO: permissões diferentes das do cliente
    def obter_permissoes(self):
        return ["CONSULTAR_PRODUTOS", "GERENCIAR_PROPRIOS_DADOS", "GERENCIAR_PRODUTOS",
                "GERENCIAR_ESTOQUE", "GERENCIAR_PEDIDOS", "GERENCIAR_PAGAMENTOS",
                "GERENCIAR_ENTREGAS"]

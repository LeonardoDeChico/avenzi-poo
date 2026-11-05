from abc import ABC, abstractmethod

from modelo.validacao import obrigatorio, validar_email, validar_senha, validar_cpf


class Usuario(ABC):
    """Classe ABSTRATA: só existem Clientes ou Administradores (generalização)."""

    def __init__(self, id, nome, email, senha, ativo=True):
        self.id = id
        self.nome = nome
        self.email = email
        self.senha = senha
        self.ativo = ativo

    def autenticar(self, email, senha):
        return self.ativo and self.email.lower() == email.lower() and self.senha == senha

    # SOBRECARGA (estilo Python): o mesmo método aceita 2 ou 3 argumentos.
    #   atualizar_dados(nome, email)            -> muda nome e e-mail
    #   atualizar_dados(nome, email, nova_senha) -> muda também a senha
    def atualizar_dados(self, nome, email, nova_senha=None):
        obrigatorio(nome, "Nome")
        validar_email(email)
        if nova_senha:
            validar_senha(nova_senha)
            self.senha = nova_senha
        self.nome = nome.strip()
        self.email = email.strip()

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
        self.cpf = cpf
        self.telefone = telefone
        self.endereco = endereco
        self.carrinho = None   # 0..1 carrinho
        self.pedidos = []      # 0..* pedidos

    def cadastrar(self):
        """Valida os dados do cliente (RF01)."""
        obrigatorio(self.nome, "Nome")
        validar_email(self.email)
        validar_senha(self.senha)
        validar_cpf(self.cpf)
        obrigatorio(self.telefone, "Telefone")
        obrigatorio(self.endereco, "Endereço")

    def consultar_pedidos(self):
        return self.pedidos

    def obter_carrinho(self):
        from modelo.carrinho import Carrinho
        if self.carrinho is None:
            self.carrinho = Carrinho(self.id)
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

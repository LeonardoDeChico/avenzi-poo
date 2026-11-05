"""Classe Loja: guarda os objetos em memória e coordena as operações.

As regras de negócio ficam nas classes do modelo; a Loja chama essas
classes, confere permissões (RN08) e salva tudo depois de cada mudança.
"""
from excecoes import DadosInvalidosError, OperacaoNaoPermitidaError, RegistroNaoEncontradoError
from modelo import Administrador, Cliente, Entrega, Pagamento, Pedido, Produto


class Loja:

    def __init__(self, repositorio):
        self.repositorio = repositorio
        self.usuarios = []
        self.produtos = []
        self.pedidos = []
        self.ultimo_id = 0
        if not repositorio.carregar(self):
            self._dados_iniciais()

    def gerar_id(self):
        self.ultimo_id += 1
        return self.ultimo_id

    def salvar(self):
        self.repositorio.salvar(self)

    def _dados_iniciais(self):
        """Na primeira execução cria o administrador e alguns produtos de exemplo."""
        self.usuarios.append(Administrador(self.gerar_id(), "Administrador", "admin@avenzi.com", "admin123"))
        exemplos = [
            ("Vaso geométrico", "Vaso decorativo em PLA, 15 cm.", 39.90, 10),
            ("Suporte para headset", "Suporte de mesa para fones de ouvido.", 49.90, 5),
            ("Suporte para celular", "Suporte articulado para celular.", 24.90, 20),
            ("Chaveiro personalizado", "Chaveiro com nome em relevo.", 12.00, 30),
        ]
        for nome, descricao, preco, quantidade in exemplos:
            self.produtos.append(Produto(self.gerar_id(), nome, descricao, preco, quantidade))
        self.salvar()

    # ---------------- PERMISSÕES (RN08) ----------------
    def exigir_permissao(self, usuario, permissao):
        if usuario is None:
            raise OperacaoNaoPermitidaError("Faça login para continuar.")
        # POLIMORFISMO: não importa se é Cliente ou Administrador,
        # cada um responde obter_permissoes() do seu jeito.
        if not usuario.possui_permissao(permissao):
            raise OperacaoNaoPermitidaError("Você não tem permissão para esta operação.")

    # ---------------- USUÁRIOS ----------------
    def cadastrar_cliente(self, nome, email, senha, cpf, telefone, endereco):
        cliente = Cliente(None, nome.strip(), email.strip(), senha,
                          cpf.strip(), telefone.strip(), endereco.strip())
        cliente.cadastrar()  # valida os dados
        if any(u.email.lower() == email.strip().lower() for u in self.usuarios):
            raise DadosInvalidosError("Já existe um usuário com este e-mail.")
        cliente.id = self.gerar_id()  # só gera o número depois de validar
        self.usuarios.append(cliente)
        self.salvar()
        return cliente

    def autenticar(self, email, senha):
        for usuario in self.usuarios:
            if usuario.autenticar(email.strip(), senha):
                return usuario
        raise DadosInvalidosError("E-mail ou senha incorretos.")

    def buscar_usuario(self, id):
        for usuario in self.usuarios:
            if usuario.id == id:
                return usuario
        return None

    def atualizar_meus_dados(self, usuario, nome, email, nova_senha):
        self.exigir_permissao(usuario, "GERENCIAR_PROPRIOS_DADOS")
        if any(u.email.lower() == email.strip().lower() and u is not usuario for u in self.usuarios):
            raise DadosInvalidosError("Já existe um usuário com este e-mail.")
        if nova_senha:
            usuario.atualizar_dados(nome, email, nova_senha)  # versão com 3 argumentos
        else:
            usuario.atualizar_dados(nome, email)              # versão com 2 argumentos
        self.salvar()

    def listar_clientes(self):
        return [u for u in self.usuarios if isinstance(u, Cliente)]

    # ---------------- PRODUTOS ----------------
    def pesquisar_produtos(self, termo="", somente_ativos=True):
        termo = (termo or "").strip().lower()
        resultado = []
        for produto in self.produtos:
            if somente_ativos and not produto.ativo:
                continue  # RN01 — inativos não aparecem para o cliente
            if termo in produto.nome.lower() or termo in (produto.descricao or "").lower():
                resultado.append(produto)
        return resultado

    def buscar_produto(self, id):
        for produto in self.produtos:
            if produto.id == id:
                return produto
        raise RegistroNaoEncontradoError("Produto não encontrado.")

    def cadastrar_produto(self, usuario, nome, descricao, preco, quantidade):
        self.exigir_permissao(usuario, "GERENCIAR_PRODUTOS")
        produto = Produto(None, nome.strip(), descricao.strip(), preco, quantidade)
        produto.cadastrar()
        produto.id = produto.estoque.id = self.gerar_id()  # só gera o número depois de validar
        self.produtos.append(produto)
        self.salvar()

    def alterar_produto(self, usuario, id, nome, descricao, preco, quantidade):
        self.exigir_permissao(usuario, "GERENCIAR_PRODUTOS")
        self.exigir_permissao(usuario, "GERENCIAR_ESTOQUE")
        produto = self.buscar_produto(id)
        produto.alterar_dados(nome, descricao, preco)
        produto.estoque.atualizar_quantidade(quantidade)
        self.salvar()

    def inativar_produto(self, usuario, id):
        self.exigir_permissao(usuario, "GERENCIAR_PRODUTOS")
        self.buscar_produto(id).inativar()
        self.salvar()

    def ativar_produto(self, usuario, id):
        self.exigir_permissao(usuario, "GERENCIAR_PRODUTOS")
        self.buscar_produto(id).ativar()
        self.salvar()

    # ---------------- CARRINHO E PEDIDO (processo principal) ----------------
    def adicionar_ao_carrinho(self, cliente, produto_id, quantidade):
        self.exigir_permissao(cliente, "ADICIONAR_AO_CARRINHO")
        cliente.obter_carrinho().adicionar_produto(self.buscar_produto(produto_id), quantidade)
        self.salvar()

    def remover_do_carrinho(self, cliente, produto_id):
        self.exigir_permissao(cliente, "ADICIONAR_AO_CARRINHO")
        cliente.obter_carrinho().remover_produto(self.buscar_produto(produto_id))
        self.salvar()

    def finalizar_pedido(self, cliente):
        self.exigir_permissao(cliente, "REALIZAR_PEDIDOS")
        carrinho = cliente.obter_carrinho()
        pedido = Pedido.a_partir_do_carrinho(self.gerar_id(), cliente, carrinho)
        pedido.criar()  # valida RN01, RN02, RN03, RN07 e baixa o estoque (RN04)
        self.pedidos.append(pedido)
        carrinho.esvaziar()
        self.salvar()
        return pedido

    def buscar_pedido(self, id):
        for pedido in self.pedidos:
            if pedido.id == id:
                return pedido
        raise RegistroNaoEncontradoError("Pedido não encontrado.")

    def cancelar_pedido_do_cliente(self, cliente, pedido_id):
        self.exigir_permissao(cliente, "REALIZAR_PEDIDOS")
        pedido = self.buscar_pedido(pedido_id)
        if pedido.cliente is not cliente:
            raise OperacaoNaoPermitidaError("Este pedido não pertence a você.")
        if pedido.status != Pedido.AGUARDANDO_PAGAMENTO:
            raise OperacaoNaoPermitidaError("Só é possível cancelar pedidos que aguardam pagamento.")
        pedido.cancelar()
        self.salvar()

    # ---------------- GESTÃO DE PEDIDOS (administrador) ----------------
    def listar_pedidos(self, admin):
        self.exigir_permissao(admin, "GERENCIAR_PEDIDOS")
        return admin.consultar_pedidos(self.pedidos)

    def registrar_pagamento(self, admin, pedido_id, valor):
        self.exigir_permissao(admin, "GERENCIAR_PAGAMENTOS")
        pedido = self.buscar_pedido(pedido_id)
        if pedido.pagamento and pedido.pagamento.esta_confirmado():
            raise OperacaoNaoPermitidaError("Este pedido já possui pagamento registrado.")
        if round(valor, 2) != round(pedido.valor_total, 2):
            total = f"{pedido.valor_total:.2f}".replace(".", ",")
            raise DadosInvalidosError(f"O valor pago deve ser igual ao total do pedido (R$ {total}).")
        pagamento = Pagamento(self.gerar_id(), valor)
        pagamento.registrar()
        pedido.pagamento = pagamento
        pedido.atualizar_status(Pedido.PAGO)
        self.salvar()

    def preparar_pedido(self, admin, pedido_id):
        self.exigir_permissao(admin, "GERENCIAR_PEDIDOS")
        self.buscar_pedido(pedido_id).atualizar_status(Pedido.EM_PREPARACAO)
        self.salvar()

    def enviar_pedido(self, admin, pedido_id, codigo_rastreio):
        self.exigir_permissao(admin, "GERENCIAR_ENTREGAS")
        pedido = self.buscar_pedido(pedido_id)
        entrega = Entrega(self.gerar_id(), pedido.cliente.endereco)
        entrega.registrar_envio(codigo_rastreio)
        pedido.atualizar_status(Pedido.ENVIADO)  # RN06 — lança erro se estiver cancelado
        pedido.entrega = entrega
        self.salvar()

    def concluir_pedido(self, admin, pedido_id):
        self.exigir_permissao(admin, "GERENCIAR_PEDIDOS")
        pedido = self.buscar_pedido(pedido_id)
        pedido.atualizar_status(Pedido.CONCLUIDO)
        pedido.entrega.atualizar_status(Entrega.ENTREGUE)
        self.salvar()

    def cancelar_pedido(self, admin, pedido_id):
        self.exigir_permissao(admin, "GERENCIAR_PEDIDOS")
        self.buscar_pedido(pedido_id).cancelar()
        self.salvar()

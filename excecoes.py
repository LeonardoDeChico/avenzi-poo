"""Exceções do sistema Avenzi.

Todas herdam de NegocioError. Assim o app.py captura qualquer erro de
negócio em um único lugar e mostra uma mensagem amigável ao usuário.
"""


class NegocioError(Exception):
    """Erro base de regra de negócio."""


class DadosInvalidosError(NegocioError):
    """Dado obrigatório não informado ou informação inválida."""


class RegistroNaoEncontradoError(NegocioError):
    """Produto, pedido ou usuário não encontrado."""


class OperacaoNaoPermitidaError(NegocioError):
    """Usuário sem permissão, produto inativo, estoque insuficiente..."""


class EstadoInvalidoError(NegocioError):
    """Ação feita no estado errado (ex.: enviar pedido cancelado)."""


class PersistenciaError(NegocioError):
    """Falha ao salvar ou carregar os dados."""

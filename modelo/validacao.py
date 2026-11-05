"""Funções de validação usadas pelas classes."""
import re

from excecoes import DadosInvalidosError


def obrigatorio(valor, campo):
    if valor is None or str(valor).strip() == "":
        raise DadosInvalidosError(f'O campo "{campo}" é obrigatório.')


def validar_email(email):
    obrigatorio(email, "E-mail")
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        raise DadosInvalidosError("Informe um e-mail válido.")


def validar_senha(senha):
    obrigatorio(senha, "Senha")
    if len(senha) < 4:
        raise DadosInvalidosError("A senha deve ter pelo menos 4 caracteres.")


def validar_cpf(cpf):
    obrigatorio(cpf, "CPF")
    numeros = cpf.replace(".", "").replace("-", "")
    if not (numeros.isdigit() and len(numeros) == 11):
        raise DadosInvalidosError("O CPF deve ter 11 dígitos.")

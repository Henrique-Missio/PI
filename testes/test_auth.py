"""
Testes de autenticação — lógica de login na camada de dados/serviço.
Como o projeto usa SQLAlchemy puro, testamos a consulta de usuário
por e-mail e verificação de senha, não rotas HTTP.
"""
import pytest
from app.models import Pessoa, Email
from testes.conftest import make_pessoa, make_email


def buscar_pessoa_por_email(session, email_str: str):
    """Replica a lógica que o serviço de login deve usar."""
    email = session.query(Email).filter(
        (Email.email_pessoal == email_str) | (
            Email.email_juridico == email_str)
    ).first()
    return email.pessoa if email else None


def autenticar(session, email_str: str, senha: str):
    """Retorna a Pessoa se credenciais corretas, None caso contrário."""
    pessoa = buscar_pessoa_por_email(session, email_str)
    if not pessoa:
        return None
    if pessoa.senha != senha:
        return None
    return pessoa


class TestBuscarPessoaPorEmail:
    def test_encontra_por_email_pessoal(self, session):
        p = make_pessoa(session, nome="Email Pessoal")
        make_email(session, p, pessoal="pessoal@teste.com")

        resultado = buscar_pessoa_por_email(session, "pessoal@teste.com")
        assert resultado is not None
        assert resultado.id == p.id

    def test_encontra_por_email_juridico(self, session):
        p = make_pessoa(session, nome="Email Jurídico")
        email = Email(email_juridico="juridico@empresa.com", id_pessoa=p.id)
        session.add(email)
        session.flush()

        resultado = buscar_pessoa_por_email(session, "juridico@empresa.com")
        assert resultado is not None
        assert resultado.id == p.id

    def test_email_inexistente_retorna_none(self, session):
        resultado = buscar_pessoa_por_email(session, "naoexiste@teste.com")
        assert resultado is None

    def test_email_vazio_retorna_none(self, session):
        resultado = buscar_pessoa_por_email(session, "")
        assert resultado is None


class TestAutenticar:
    def test_credenciais_corretas_retornam_pessoa(self, session):
        p = make_pessoa(session, nome="Login OK", senha="senha123")
        make_email(session, p, pessoal="login@teste.com")

        resultado = autenticar(session, "login@teste.com", "senha123")
        assert resultado is not None
        assert resultado.nome_completo == "Login OK"

    def test_senha_errada_retorna_none(self, session):
        p = make_pessoa(session, nome="Senha Errada", senha="correta")
        make_email(session, p, pessoal="errada@teste.com")

        resultado = autenticar(session, "errada@teste.com", "errada")
        assert resultado is None

    def test_email_inexistente_retorna_none(self, session):
        resultado = autenticar(session, "fantasma@teste.com", "qualquer")
        assert resultado is None

    def test_admin_autentica(self, session):
        p = make_pessoa(session, nome="Admin", tipo="admin",
                        funcao="administrador", senha="admin123")
        make_email(session, p, pessoal="admin@pidstech.com")

        resultado = autenticar(session, "admin@pidstech.com", "admin123")
        assert resultado is not None
        assert resultado.tipo == "admin"

    def test_voluntario_autentica(self, session):
        p = make_pessoa(session, nome="Vol", tipo="voluntario", senha="vol123")
        make_email(session, p, pessoal="vol@teste.com")

        resultado = autenticar(session, "vol@teste.com", "vol123")
        assert resultado is not None
        assert resultado.tipo == "voluntario"


class TestTipoDePessoa:
    def test_admin_tem_tipo_admin(self, session):
        p = make_pessoa(session, tipo="admin", funcao="administrador")
        assert p.tipo == "admin"

    def test_voluntario_tem_tipo_voluntario(self, session):
        p = make_pessoa(session, tipo="voluntario")
        assert p.tipo == "voluntario"

    def test_tipo_diferente_de_admin_nao_e_admin(self, session):
        p = make_pessoa(session, tipo="voluntario")
        assert p.tipo != "admin"

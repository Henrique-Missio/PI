"""validar_senha_forte + integracao cadastrar_usuario/editar_perfil."""
import pytest
from app.servicos import cadastrar_usuario, editar_perfil, validar_senha_forte
from app.database import SessionLocal
from app.models import Pessoa, Pessoa_fisica, Endereco, Email, Telefone

USUARIO_BASE = {
    "nome_completo": "Senha Teste", "cpf": "52998224725", "funcao": "tecnico",
    "email_pessoal": "senha.teste@teste.com", "telefone_celular": "51988880000",
    "cep": "96810000", "rua": "Rua X", "numero": "1", "bairro": "Centro",
    "cidade": "Santa Cruz do Sul", "estado": "RS", "senha": "Senha@123",
    "data_nasc": "10-05-2000",
}

@pytest.fixture(autouse=True)
def limpar():
    def _limpar():
        s = SessionLocal()
        try:
            s.query(Telefone).delete(); s.query(Endereco).delete()
            s.query(Email).delete(); s.query(Pessoa_fisica).delete()
            s.query(Pessoa).delete(); s.commit()
        finally: s.close()
    _limpar(); yield; _limpar()


class TestValidarSenhaForteUnitario:
    def test_senha_forte_valida(self):
        assert validar_senha_forte("Senha@123") is True

    def test_curta_falha(self):
        assert validar_senha_forte("Ab@1") is False

    def test_sem_maiuscula_falha(self):
        assert validar_senha_forte("senha@123") is False

    def test_sem_numero_falha(self):
        assert validar_senha_forte("Senha@abc") is False

    def test_sem_especial_falha(self):
        assert validar_senha_forte("Senha1234") is False

    def test_vazia_falha(self):
        assert validar_senha_forte("") is False

    def test_none_falha(self):
        assert validar_senha_forte(None) is False

    def test_exatos_8_com_tudo_valida(self):
        assert validar_senha_forte("Abcd@123") is True


class TestCadastrarUsuarioSenhaForte:
    def test_senha_fraca_falha(self):
        dados = {**USUARIO_BASE, "senha": "fraca"}
        with pytest.raises(ValueError, match="[Ss]enha"):
            cadastrar_usuario(dados)

    def test_senha_forte_aceita(self):
        assert cadastrar_usuario(USUARIO_BASE) is not None


class TestEditarPerfilSenhaForte:
    def test_editar_senha_fraca_falha(self):
        u = cadastrar_usuario(USUARIO_BASE)
        with pytest.raises(ValueError, match="[Ss]enha"):
            editar_perfil(u["id"], {"senha": "fraca123"})

    def test_editar_senha_forte_aceita(self):
        u = cadastrar_usuario(USUARIO_BASE)
        r = editar_perfil(u["id"], {"senha": "NovaSenha@1"})
        assert r is not None

"""solicitar_recuperacao_senha, verificar_codigo_recuperacao, redefinir_senha_com_codigo."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from app.servicos import (
    cadastrar_usuario, login,
    solicitar_recuperacao_senha, verificar_codigo_recuperacao, redefinir_senha_com_codigo,
)
from app.database import SessionLocal
from app.models import Pessoa, Pessoa_fisica, Endereco, Email, Telefone, CodigoRecuperacao

USUARIO = {
    "nome_completo": "Recup Teste", "cpf": "52998224725", "funcao": "tecnico",
    "email_pessoal": "recup@teste.com", "telefone_celular": "51988880000",
    "cep": "96810000", "rua": "Rua X", "numero": "1", "bairro": "Centro",
    "cidade": "Santa Cruz do Sul", "estado": "RS", "senha": "Senha@123",
    "data_nasc": "10-05-2000",
}

@pytest.fixture(autouse=True)
def limpar():
    def _limpar():
        s = SessionLocal()
        try:
            s.query(CodigoRecuperacao).delete()
            s.query(Telefone).delete(); s.query(Endereco).delete()
            s.query(Email).delete(); s.query(Pessoa_fisica).delete()
            s.query(Pessoa).delete(); s.commit()
        finally: s.close()
    _limpar(); yield; _limpar()


def _codigo_gerado(email="recup@teste.com"):
    s = SessionLocal()
    try:
        e = s.scalars(select := __import__("sqlalchemy").select(Email).where(Email.email_pessoal == email)).first()
        reg = s.query(CodigoRecuperacao).filter_by(id_pessoa=e.id_pessoa).order_by(CodigoRecuperacao.id.desc()).first()
        return reg.codigo
    finally:
        s.close()


class TestSolicitarRecuperacao:
    @patch("app.servicos.enviar_codigo_recuperacao")
    def test_email_existente_gera_codigo(self, mock_envio):
        cadastrar_usuario(USUARIO)
        solicitar_recuperacao_senha("recup@teste.com")
        assert mock_envio.called

    @patch("app.servicos.enviar_codigo_recuperacao")
    def test_email_inexistente_nao_envia_mas_retorna_sucesso(self, mock_envio):
        r = solicitar_recuperacao_senha("naoexiste@teste.com")
        assert not mock_envio.called
        assert "mensagem" in r

    @patch("app.servicos.enviar_codigo_recuperacao")
    def test_email_existente_msg_igual_a_inexistente(self, mock_envio):
        cadastrar_usuario(USUARIO)
        r1 = solicitar_recuperacao_senha("recup@teste.com")
        r2 = solicitar_recuperacao_senha("naoexiste@teste.com")
        assert r1["mensagem"] == r2["mensagem"]

    @patch("app.servicos.enviar_codigo_recuperacao")
    def test_codigo_tem_6_digitos(self, mock_envio):
        cadastrar_usuario(USUARIO)
        solicitar_recuperacao_senha("recup@teste.com")
        codigo = mock_envio.call_args[0][1]
        assert len(codigo) == 6
        assert codigo.isdigit()

    def test_email_vazio_falha(self):
        with pytest.raises(ValueError):
            solicitar_recuperacao_senha("")


class TestVerificarCodigo:
    @patch("app.servicos.enviar_codigo_recuperacao")
    def test_codigo_correto_valido(self, mock_envio):
        cadastrar_usuario(USUARIO)
        solicitar_recuperacao_senha("recup@teste.com")
        codigo = mock_envio.call_args[0][1]
        assert verificar_codigo_recuperacao("recup@teste.com", codigo) is True

    @patch("app.servicos.enviar_codigo_recuperacao")
    def test_codigo_errado_invalido(self, mock_envio):
        cadastrar_usuario(USUARIO)
        solicitar_recuperacao_senha("recup@teste.com")
        assert verificar_codigo_recuperacao("recup@teste.com", "000000") is False

    def test_email_sem_solicitacao_invalido(self):
        cadastrar_usuario(USUARIO)
        assert verificar_codigo_recuperacao("recup@teste.com", "123456") is False

    @patch("app.servicos.enviar_codigo_recuperacao")
    def test_codigo_expirado_invalido(self, mock_envio):
        cadastrar_usuario(USUARIO)
        solicitar_recuperacao_senha("recup@teste.com")
        codigo = mock_envio.call_args[0][1]

        s = SessionLocal()
        reg = s.query(CodigoRecuperacao).order_by(CodigoRecuperacao.id.desc()).first()
        reg.expira_em = datetime.utcnow() - timedelta(minutes=1)
        s.commit(); s.close()

        assert verificar_codigo_recuperacao("recup@teste.com", codigo) is False

    @patch("app.servicos.enviar_codigo_recuperacao")
    def test_codigo_ja_usado_invalido(self, mock_envio):
        cadastrar_usuario(USUARIO)
        solicitar_recuperacao_senha("recup@teste.com")
        codigo = mock_envio.call_args[0][1]
        redefinir_senha_com_codigo("recup@teste.com", codigo, "NovaSenha@1")
        assert verificar_codigo_recuperacao("recup@teste.com", codigo) is False


class TestRedefinirSenha:
    @patch("app.servicos.enviar_codigo_recuperacao")
    def test_redefine_e_permite_login_com_nova_senha(self, mock_envio):
        cadastrar_usuario(USUARIO)
        solicitar_recuperacao_senha("recup@teste.com")
        codigo = mock_envio.call_args[0][1]
        redefinir_senha_com_codigo("recup@teste.com", codigo, "NovaSenha@1")

        resultado = login({"email": "recup@teste.com", "senha": "NovaSenha@1"})
        assert resultado is not None

    @patch("app.servicos.enviar_codigo_recuperacao")
    def test_senha_antiga_para_de_funcionar(self, mock_envio):
        cadastrar_usuario(USUARIO)
        solicitar_recuperacao_senha("recup@teste.com")
        codigo = mock_envio.call_args[0][1]
        redefinir_senha_com_codigo("recup@teste.com", codigo, "NovaSenha@1")

        with pytest.raises(ValueError, match="incorretos"):
            login({"email": "recup@teste.com", "senha": "Senha@123"})

    @patch("app.servicos.enviar_codigo_recuperacao")
    def test_codigo_invalido_falha(self, mock_envio):
        cadastrar_usuario(USUARIO)
        solicitar_recuperacao_senha("recup@teste.com")
        with pytest.raises(ValueError, match="[Cc]ódigo"):
            redefinir_senha_com_codigo("recup@teste.com", "000000", "NovaSenha@1")

    @patch("app.servicos.enviar_codigo_recuperacao")
    def test_nova_senha_fraca_falha(self, mock_envio):
        cadastrar_usuario(USUARIO)
        solicitar_recuperacao_senha("recup@teste.com")
        codigo = mock_envio.call_args[0][1]
        with pytest.raises(ValueError, match="[Ss]enha"):
            redefinir_senha_com_codigo("recup@teste.com", codigo, "fraca")

    @patch("app.servicos.enviar_codigo_recuperacao")
    def test_codigo_reusado_falha(self, mock_envio):
        cadastrar_usuario(USUARIO)
        solicitar_recuperacao_senha("recup@teste.com")
        codigo = mock_envio.call_args[0][1]
        redefinir_senha_com_codigo("recup@teste.com", codigo, "NovaSenha@1")
        with pytest.raises(ValueError, match="[Cc]ódigo"):
            redefinir_senha_com_codigo("recup@teste.com", codigo, "OutraSenha@2")

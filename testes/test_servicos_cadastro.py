"""
Testes da função cadastrar_usuario do servicos.py.
Testa validações, duplicatas, hash de senha e criação completa.
"""
import pytest
from werkzeug.security import check_password_hash
from app.servicos import cadastrar_usuario, login
from app.database import SessionLocal
from app.models import Pessoa, Pessoa_fisica, Endereco, Email, Telefone


# ── Payload base válido ───────────────────────────────────────────────────────

USUARIO_VALIDO = {
    "nome_completo":    "João da Silva",
    "cpf":              "52998224725",
    "funcao":           "tecnico",
    "email_pessoal":    "joao@teste.com",
    "telefone_celular": "51988880000",
    "cep":              "96810000",
    "rua":              "Rua Sinimbu",
    "numero":           "456",
    "bairro":           "Centro",
    "cidade":           "Santa Cruz do Sul",
    "estado":           "RS",
    "senha":            "senha123",
    "data_nasc":        "10-05-2000",
}


# ── Fixture de limpeza ────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def limpar_usuarios():
    """Limpa todos os usuários antes e depois de cada teste."""
    def _limpar():
        session = SessionLocal()
        try:
            session.query(Telefone).delete()
            session.query(Endereco).delete()
            session.query(Email).delete()
            session.query(Pessoa_fisica).delete()
            session.query(Pessoa).delete()
            session.commit()
        finally:
            session.close()

    _limpar()
    yield
    _limpar()


# ═════════════════════════════════════════════════════════════════════════════
# FLUXO FELIZ
# ═════════════════════════════════════════════════════════════════════════════

class TestCadastrarUsuarioFluxoCompleto:
    def test_retorna_dict(self):
        resultado = cadastrar_usuario(USUARIO_VALIDO)
        assert isinstance(resultado, dict)

    def test_retorna_campos_corretos(self):
        resultado = cadastrar_usuario(USUARIO_VALIDO)
        assert resultado["nome_completo"] == "João da Silva"
        assert resultado["tipo"] == "voluntario"
        assert resultado["funcao"] == "tecnico"

    def test_senha_nao_vaza_no_retorno(self):
        resultado = cadastrar_usuario(USUARIO_VALIDO)
        assert "senha" not in resultado

    def test_tipo_padrao_voluntario(self):
        resultado = cadastrar_usuario(USUARIO_VALIDO)
        assert resultado["tipo"] == "voluntario"

    def test_tipo_administrador(self):
        resultado = cadastrar_usuario(USUARIO_VALIDO, tipo="administrador")
        assert resultado["tipo"] == "administrador"

    def test_senha_e_hasheada_no_banco(self):
        cadastrar_usuario(USUARIO_VALIDO)
        session = SessionLocal()
        try:
            pessoa = session.query(Pessoa).filter_by(
                nome_completo="João da Silva"
            ).first()
            assert pessoa is not None
            assert pessoa.senha != "senha123"
            assert check_password_hash(pessoa.senha, "senha123")
        finally:
            session.close()

    def test_cria_pessoa_fisica_no_banco(self):
        cadastrar_usuario(USUARIO_VALIDO)
        session = SessionLocal()
        try:
            pf = session.query(Pessoa_fisica).filter_by(
                cpf="52998224725"
            ).first()
            assert pf is not None
        finally:
            session.close()

    def test_cria_email_no_banco(self):
        cadastrar_usuario(USUARIO_VALIDO)
        session = SessionLocal()
        try:
            email = session.query(Email).filter_by(
                email_pessoal="joao@teste.com"
            ).first()
            assert email is not None
        finally:
            session.close()

    def test_cria_telefone_no_banco(self):
        cadastrar_usuario(USUARIO_VALIDO)
        session = SessionLocal()
        try:
            pessoa = session.query(Pessoa).filter_by(
                nome_completo="João da Silva"
            ).first()
            tel = session.query(Telefone).filter_by(
                id_pessoa=pessoa.id
            ).first()
            assert tel is not None
            assert tel.telefone_celular == "51988880000"
        finally:
            session.close()

    def test_cria_endereco_no_banco(self):
        cadastrar_usuario(USUARIO_VALIDO)
        session = SessionLocal()
        try:
            pessoa = session.query(Pessoa).filter_by(
                nome_completo="João da Silva"
            ).first()
            end = session.query(Endereco).filter_by(
                id_pessoa=pessoa.id
            ).first()
            assert end is not None
            assert end.numero == "456"
            assert end.cidade == "Santa Cruz do Sul"
        finally:
            session.close()

    def test_complemento_opcional_aceito(self):
        dados = {**USUARIO_VALIDO, "complemento": "Apto 2"}
        resultado = cadastrar_usuario(dados)
        assert resultado is not None

    def test_complemento_ausente_aceito(self):
        resultado = cadastrar_usuario(USUARIO_VALIDO)
        assert resultado is not None

    def test_email_juridico_opcional(self):
        dados = {**USUARIO_VALIDO, "email_juridico": "joao@empresa.com"}
        resultado = cadastrar_usuario(dados)
        assert resultado is not None

    def test_usuario_pode_fazer_login_apos_cadastro(self):
        cadastrar_usuario(USUARIO_VALIDO)
        resultado = login({
            "email": "joao@teste.com",
            "senha": "senha123",
        })
        assert resultado["nome_completo"] == "João da Silva"


# ═════════════════════════════════════════════════════════════════════════════
# VALIDAÇÃO DE CPF
# ═════════════════════════════════════════════════════════════════════════════

class TestCadastrarUsuarioValidacaoCPF:
    def test_cpf_com_letras_falha(self):
        dados = {**USUARIO_VALIDO, "cpf": "abc.def.ghi-jk"}
        with pytest.raises(ValueError, match="CPF"):
            cadastrar_usuario(dados)

    def test_cpf_com_menos_de_11_digitos_falha(self):
        dados = {**USUARIO_VALIDO, "cpf": "1234567890"}
        with pytest.raises(ValueError, match="CPF"):
            cadastrar_usuario(dados)

    def test_cpf_com_mais_de_11_digitos_falha(self):
        dados = {**USUARIO_VALIDO, "cpf": "123456789012"}
        with pytest.raises(ValueError, match="CPF"):
            cadastrar_usuario(dados)

    def test_cpf_vazio_falha(self):
        dados = {**USUARIO_VALIDO, "cpf": ""}
        with pytest.raises(ValueError):
            cadastrar_usuario(dados)

    def test_cpf_duplicado_falha(self):
        cadastrar_usuario(USUARIO_VALIDO)
        dados = {**USUARIO_VALIDO, "email_pessoal": "outro@teste.com"}
        with pytest.raises(ValueError, match="CPF"):
            cadastrar_usuario(dados)

    def test_cpfs_diferentes_sao_aceitos(self):
        cadastrar_usuario(USUARIO_VALIDO)
        dados = {
            **USUARIO_VALIDO,
            "cpf": "11144477735",
            "email_pessoal": "outro@teste.com",
        }
        resultado = cadastrar_usuario(dados)
        assert resultado is not None


# ═════════════════════════════════════════════════════════════════════════════
# VALIDAÇÃO DE EMAIL
# ═════════════════════════════════════════════════════════════════════════════

class TestCadastrarUsuarioValidacaoEmail:
    def test_email_duplicado_falha(self):
        cadastrar_usuario(USUARIO_VALIDO)
        dados = {**USUARIO_VALIDO, "cpf": "11144477735"}
        with pytest.raises(ValueError, match="e-mail"):
            cadastrar_usuario(dados)

    def test_email_vazio_falha(self):
        dados = {**USUARIO_VALIDO, "email_pessoal": ""}
        with pytest.raises(ValueError):
            cadastrar_usuario(dados)

    def test_emails_diferentes_sao_aceitos(self):
        cadastrar_usuario(USUARIO_VALIDO)
        dados = {
            **USUARIO_VALIDO,
            "cpf": "11144477735",
            "email_pessoal": "outro@teste.com",
        }
        resultado = cadastrar_usuario(dados)
        assert resultado is not None


# ═════════════════════════════════════════════════════════════════════════════
# VALIDAÇÃO DE SENHA
# ═════════════════════════════════════════════════════════════════════════════

class TestCadastrarUsuarioValidacaoSenha:
    def test_senha_menor_que_6_caracteres_falha(self):
        dados = {**USUARIO_VALIDO, "senha": "abc"}
        with pytest.raises(ValueError, match="senha"):
            cadastrar_usuario(dados)

    def test_senha_vazia_falha(self):
        dados = {**USUARIO_VALIDO, "senha": ""}
        with pytest.raises(ValueError):
            cadastrar_usuario(dados)

    def test_senha_com_exatamente_6_caracteres_aceita(self):
        dados = {**USUARIO_VALIDO, "senha": "abc123"}
        resultado = cadastrar_usuario(dados)
        assert resultado is not None

    def test_senha_longa_aceita(self):
        dados = {**USUARIO_VALIDO, "senha": "senhamuitorande123!@#"}
        resultado = cadastrar_usuario(dados)
        assert resultado is not None


# ═════════════════════════════════════════════════════════════════════════════
# VALIDAÇÃO DE TELEFONE
# ═════════════════════════════════════════════════════════════════════════════

class TestCadastrarUsuarioValidacaoTelefone:
    def test_telefone_com_letras_falha(self):
        dados = {**USUARIO_VALIDO, "telefone_celular": "abc"}
        with pytest.raises(ValueError, match="[Tt]elefone"):
            cadastrar_usuario(dados)

    def test_telefone_curto_demais_falha(self):
        dados = {**USUARIO_VALIDO, "telefone_celular": "51999"}
        with pytest.raises(ValueError, match="[Tt]elefone"):
            cadastrar_usuario(dados)

    def test_telefone_vazio_falha(self):
        dados = {**USUARIO_VALIDO, "telefone_celular": ""}
        with pytest.raises(ValueError):
            cadastrar_usuario(dados)

    def test_telefone_com_10_digitos_aceito(self):
        dados = {**USUARIO_VALIDO, "telefone_celular": "5132221111"}
        resultado = cadastrar_usuario(dados)
        assert resultado is not None

    def test_telefone_com_11_digitos_aceito(self):
        resultado = cadastrar_usuario(USUARIO_VALIDO)
        assert resultado is not None


# ═════════════════════════════════════════════════════════════════════════════
# VALIDAÇÃO DE CEP
# ═════════════════════════════════════════════════════════════════════════════

class TestCadastrarUsuarioValidacaoCEP:
    def test_cep_com_letras_falha(self):
        dados = {**USUARIO_VALIDO, "cep": "abcdefgh"}
        with pytest.raises(ValueError, match="CEP"):
            cadastrar_usuario(dados)

    def test_cep_com_menos_de_8_digitos_falha(self):
        dados = {**USUARIO_VALIDO, "cep": "9681000"}
        with pytest.raises(ValueError, match="CEP"):
            cadastrar_usuario(dados)

    def test_cep_com_mais_de_8_digitos_falha(self):
        dados = {**USUARIO_VALIDO, "cep": "968100001"}
        with pytest.raises(ValueError, match="CEP"):
            cadastrar_usuario(dados)

    def test_cep_vazio_falha(self):
        dados = {**USUARIO_VALIDO, "cep": ""}
        with pytest.raises(ValueError):
            cadastrar_usuario(dados)

    def test_cep_valido_aceito(self):
        resultado = cadastrar_usuario(USUARIO_VALIDO)
        assert resultado is not None


# ═════════════════════════════════════════════════════════════════════════════
# VALIDAÇÃO DE TIPO
# ═════════════════════════════════════════════════════════════════════════════

class TestCadastrarUsuarioValidacaoTipo:
    def test_tipo_invalido_falha(self):
        with pytest.raises(ValueError, match="[Tt]ipo"):
            cadastrar_usuario(USUARIO_VALIDO, tipo="superadmin")

    def test_tipo_voluntario_aceito(self):
        resultado = cadastrar_usuario(USUARIO_VALIDO, tipo="voluntario")
        assert resultado["tipo"] == "voluntario"

    def test_tipo_administrador_aceito(self):
        resultado = cadastrar_usuario(USUARIO_VALIDO, tipo="administrador")
        assert resultado["tipo"] == "administrador"


# ═════════════════════════════════════════════════════════════════════════════
# VALIDAÇÃO DE DATA
# ═════════════════════════════════════════════════════════════════════════════

class TestCadastrarUsuarioValidacaoData:
    def test_data_nasc_formato_invalido_falha(self):
        dados = {**USUARIO_VALIDO, "data_nasc": "2000/05/10"}
        with pytest.raises(ValueError, match="data_nasc"):
            cadastrar_usuario(dados)

    def test_data_nasc_vazia_falha(self):
        dados = {**USUARIO_VALIDO, "data_nasc": ""}
        with pytest.raises(ValueError):
            cadastrar_usuario(dados)

    def test_data_nasc_formato_correto_aceito(self):
        resultado = cadastrar_usuario(USUARIO_VALIDO)
        assert resultado is not None

"""
Testes de validar_data_nascimento() e sua integração em cadastrar_usuario:
- data de nascimento no futuro deve ser rejeitada
- idade implausível (>120 anos) deve ser rejeitada
- datas normais devem ser aceitas
"""
import pytest
from datetime import date, timedelta
from app.servicos import cadastrar_usuario, validar_data_nascimento
from app.database import SessionLocal
from app.models import Pessoa, Pessoa_fisica, Endereco, Email, Telefone

USUARIO_BASE = {
    "nome_completo":    "Data Teste",
    "cpf":              "52998224725",
    "funcao":           "tecnico",
    "email_pessoal":    "data.teste@teste.com",
    "telefone_celular": "51988880000",
    "cep":              "96810000",
    "rua":              "Rua Sinimbu",
    "numero":           "100",
    "bairro":           "Centro",
    "cidade":           "Santa Cruz do Sul",
    "estado":           "RS",
    "senha":            "Senha@123",
    "data_nasc":        "10-05-2000",
}


@pytest.fixture(autouse=True)
def limpar_usuarios():
    def _limpar():
        s = SessionLocal()
        try:
            s.query(Telefone).delete()
            s.query(Endereco).delete()
            s.query(Email).delete()
            s.query(Pessoa_fisica).delete()
            s.query(Pessoa).delete()
            s.commit()
        finally:
            s.close()
    _limpar()
    yield
    _limpar()


# ═════════════════════════════════════════════════════════════════════════════
# validar_data_nascimento — função isolada
# ═════════════════════════════════════════════════════════════════════════════

class TestValidarDataNascimentoUnitario:
    def test_data_passada_normal_valida(self):
        assert validar_data_nascimento(date(2000, 5, 10)) is True

    def test_data_hoje_valida(self):
        assert validar_data_nascimento(date.today()) is True

    def test_data_futura_invalida(self):
        futura = date.today() + timedelta(days=1)
        assert validar_data_nascimento(futura) is False

    def test_data_futura_um_ano_invalida(self):
        futura = date.today() + timedelta(days=365)
        assert validar_data_nascimento(futura) is False

    def test_idade_119_anos_valida(self):
        quase_120 = date.today().replace(year=date.today().year - 119)
        assert validar_data_nascimento(quase_120) is True

    def test_idade_acima_de_120_anos_invalida(self):
        muito_velho = date.today().replace(year=date.today().year - 121)
        assert validar_data_nascimento(muito_velho) is False

    def test_recem_nascido_valido(self):
        assert validar_data_nascimento(date.today()) is True


# ═════════════════════════════════════════════════════════════════════════════
# Integração com cadastrar_usuario
# ═════════════════════════════════════════════════════════════════════════════

class TestCadastrarUsuarioDataNascimento:
    def test_data_nasc_futura_falha(self):
        futura = date.today() + timedelta(days=30)
        dados = {**USUARIO_BASE, "data_nasc": futura.strftime("%d-%m-%Y")}
        with pytest.raises(ValueError, match="[Dd]ata de nascimento"):
            cadastrar_usuario(dados)

    def test_data_nasc_amanha_falha(self):
        amanha = date.today() + timedelta(days=1)
        dados = {**USUARIO_BASE, "data_nasc": amanha.strftime("%d-%m-%Y")}
        with pytest.raises(ValueError, match="[Dd]ata de nascimento"):
            cadastrar_usuario(dados)

    def test_data_nasc_hoje_aceita(self):
        hoje = date.today()
        dados = {**USUARIO_BASE, "data_nasc": hoje.strftime("%d-%m-%Y")}
        resultado = cadastrar_usuario(dados)
        assert resultado is not None

    def test_data_nasc_normal_aceita(self):
        resultado = cadastrar_usuario(USUARIO_BASE)
        assert resultado is not None

    def test_idade_impossivel_falha(self):
        muito_velho = date.today().replace(year=date.today().year - 150)
        dados = {**USUARIO_BASE, "data_nasc": muito_velho.strftime("%d-%m-%Y")}
        with pytest.raises(ValueError, match="[Dd]ata de nascimento"):
            cadastrar_usuario(dados)

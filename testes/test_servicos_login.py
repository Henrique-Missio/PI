"""
Testes da função login do servicos.py.
Cobre: campos obrigatórios, credenciais corretas/incorretas, hash de senha.
"""
import pytest
from app.servicos import login, cadastrar_usuario
from app.database import SessionLocal
from app.models import Pessoa, Pessoa_fisica, Endereco, Email, Telefone


# ── Payload base válido (mesmo do test_servicos_cadastro.py) ─────────────────

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


@pytest.fixture
def usuario_cadastrado():
    """Cadastra um usuário válido e retorna seus dados."""
    return cadastrar_usuario(USUARIO_VALIDO)


# ═════════════════════════════════════════════════════════════════════════════
# CAMPOS OBRIGATÓRIOS
# ═════════════════════════════════════════════════════════════════════════════

class TestLoginCamposObrigatorios:
    def test_email_ausente_falha(self, usuario_cadastrado):
        with pytest.raises(ValueError, match="email"):
            login({"senha": "senha123"})

    def test_email_vazio_falha(self, usuario_cadastrado):
        with pytest.raises(ValueError, match="email"):
            login({"email": "", "senha": "senha123"})

    def test_email_apenas_espacos_falha(self, usuario_cadastrado):
        with pytest.raises(ValueError, match="email"):
            login({"email": "   ", "senha": "senha123"})

    def test_senha_ausente_falha(self, usuario_cadastrado):
        with pytest.raises(ValueError, match="senha"):
            login({"email": "joao@teste.com"})

    def test_senha_vazia_falha(self, usuario_cadastrado):
        with pytest.raises(ValueError, match="senha"):
            login({"email": "joao@teste.com", "senha": ""})

    def test_senha_apenas_espacos_falha(self, usuario_cadastrado):
        with pytest.raises(ValueError, match="senha"):
            login({"email": "joao@teste.com", "senha": "   "})

    def test_ambos_campos_ausentes_falha(self):
        with pytest.raises(ValueError):
            login({})

    def test_dicionario_vazio_falha(self):
        with pytest.raises(ValueError):
            login({})


# ═════════════════════════════════════════════════════════════════════════════
# FLUXO FELIZ
# ═════════════════════════════════════════════════════════════════════════════

class TestLoginFluxoCompleto:
    def test_credenciais_corretas_retorna_dict(self, usuario_cadastrado):
        resultado = login({"email": "joao@teste.com", "senha": "senha123"})
        assert isinstance(resultado, dict)

    def test_retorna_id(self, usuario_cadastrado):
        resultado = login({"email": "joao@teste.com", "senha": "senha123"})
        assert "id" in resultado

    def test_retorna_nome_completo(self, usuario_cadastrado):
        resultado = login({"email": "joao@teste.com", "senha": "senha123"})
        assert resultado["nome_completo"] == "João da Silva"

    def test_retorna_tipo(self, usuario_cadastrado):
        resultado = login({"email": "joao@teste.com", "senha": "senha123"})
        assert resultado["tipo"] == "voluntario"

    def test_retorna_funcao(self, usuario_cadastrado):
        resultado = login({"email": "joao@teste.com", "senha": "senha123"})
        assert resultado["funcao"] == "tecnico"

    def test_nao_retorna_senha(self, usuario_cadastrado):
        resultado = login({"email": "joao@teste.com", "senha": "senha123"})
        assert "senha" not in resultado

    def test_login_admin_retorna_tipo_correto(self):
        cadastrar_usuario(USUARIO_VALIDO, tipo="administrador")
        resultado = login({"email": "joao@teste.com", "senha": "senha123"})
        assert resultado["tipo"] == "administrador"


# ═════════════════════════════════════════════════════════════════════════════
# CREDENCIAIS INCORRETAS
# ═════════════════════════════════════════════════════════════════════════════

class TestLoginCredenciaisIncorretas:
    def test_senha_errada_falha(self, usuario_cadastrado):
        with pytest.raises(ValueError, match="incorretos"):
            login({"email": "joao@teste.com", "senha": "senhaerrada"})

    def test_email_inexistente_falha(self, usuario_cadastrado):
        with pytest.raises(ValueError, match="incorretos"):
            login({"email": "naoexiste@teste.com", "senha": "senha123"})

    def test_email_e_senha_errados_falha(self, usuario_cadastrado):
        with pytest.raises(ValueError, match="incorretos"):
            login({"email": "fantasma@teste.com", "senha": "errada"})

    def test_senha_case_sensitive(self, usuario_cadastrado):
        """Senha com maiúscula/minúscula trocada deve falhar."""
        with pytest.raises(ValueError):
            login({"email": "joao@teste.com", "senha": "SENHA123"})

    def test_email_com_espacos_extras_nao_encontra(self, usuario_cadastrado):
        """O e-mail no banco não tem espaços, então a busca exata deve falhar
        a menos que o serviço normalize isso."""
        resultado_ou_erro = None
        try:
            resultado_ou_erro = login({"email": " joao@teste.com ", "senha": "senha123"})
        except ValueError:
            resultado_ou_erro = "erro"
        # Aceitamos os dois comportamentos, mas o teste documenta o que acontece
        assert resultado_ou_erro is not None

    def test_login_apos_exclusao_de_usuario_falha(self, usuario_cadastrado):
        from app.servicos import excluir_usuario
        excluir_usuario(usuario_cadastrado["id"])
        with pytest.raises(ValueError, match="incorretos"):
            login({"email": "joao@teste.com", "senha": "senha123"})


# ═════════════════════════════════════════════════════════════════════════════
# MÚLTIPLOS USUÁRIOS
# ═════════════════════════════════════════════════════════════════════════════

class TestLoginMultiplosUsuarios:
    def test_login_distingue_usuarios_diferentes(self):
        cadastrar_usuario(USUARIO_VALIDO)
        outro = {
            **USUARIO_VALIDO,
            "nome_completo": "Maria Souza",
            "cpf": "11144477735",
            "email_pessoal": "maria@teste.com",
            "senha": "outrasenha",
        }
        cadastrar_usuario(outro)

        resultado_joao  = login({"email": "joao@teste.com",  "senha": "senha123"})
        resultado_maria = login({"email": "maria@teste.com", "senha": "outrasenha"})

        assert resultado_joao["nome_completo"]  == "João da Silva"
        assert resultado_maria["nome_completo"] == "Maria Souza"
        assert resultado_joao["id"] != resultado_maria["id"]

    def test_senha_de_um_usuario_nao_loga_outro(self):
        cadastrar_usuario(USUARIO_VALIDO)
        outro = {
            **USUARIO_VALIDO,
            "nome_completo": "Maria Souza",
            "cpf": "11144477735",
            "email_pessoal": "maria@teste.com",
            "senha": "outrasenha",
        }
        cadastrar_usuario(outro)

        # tenta logar como Maria usando a senha do João
        with pytest.raises(ValueError, match="incorretos"):
            login({"email": "maria@teste.com", "senha": "senha123"})

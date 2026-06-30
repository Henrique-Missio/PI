"""
Testes das funções:
- listar_usuarios
- excluir_usuario
- buscar_perfil
- editar_perfil
"""
import pytest
from app.servicos import (
    cadastrar_usuario, listar_usuarios, excluir_usuario,
    buscar_perfil, editar_perfil,
)
from app.database import SessionLocal
from app.models import Pessoa, Pessoa_fisica, Endereco, Email, Telefone


# ── Payload base ──────────────────────────────────────────────────────────────

USUARIO_BASE = {
    "nome_completo":    "Ana Souza",
    "cpf":              "52998224725",
    "funcao":           "tecnico",
    "email_pessoal":    "ana@teste.com",
    "telefone_celular": "51988880000",
    "cep":              "96810000",
    "rua":              "Rua Sinimbu",
    "numero":           "100",
    "bairro":           "Centro",
    "cidade":           "Santa Cruz do Sul",
    "estado":           "RS",
    "senha":            "senha123",
    "data_nasc":        "15-03-1995",
}

USUARIO_B = {
    **USUARIO_BASE,
    "nome_completo":    "Carlos Lima",
    "cpf":              "11144477735",
    "email_pessoal":    "carlos@teste.com",
}


# ── Fixture de limpeza ────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def limpar_usuarios():
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
def usuario_a():
    return cadastrar_usuario(USUARIO_BASE)


@pytest.fixture
def usuario_b():
    return cadastrar_usuario(USUARIO_B)


# ═════════════════════════════════════════════════════════════════════════════
# LISTAR USUÁRIOS
# ═════════════════════════════════════════════════════════════════════════════

class TestListarUsuarios:
    def test_retorna_lista(self):
        assert isinstance(listar_usuarios(), list)

    def test_lista_vazia_sem_usuarios(self):
        assert listar_usuarios() == []

    def test_lista_um_usuario(self, usuario_a):
        resultado = listar_usuarios()
        assert len(resultado) == 1

    def test_lista_multiplos_usuarios(self, usuario_a, usuario_b):
        resultado = listar_usuarios()
        assert len(resultado) == 2

    def test_retorna_dicts(self, usuario_a):
        resultado = listar_usuarios()
        assert isinstance(resultado[0], dict)

    def test_campos_presentes(self, usuario_a):
        resultado = listar_usuarios()
        u = resultado[0]
        assert "id" in u
        assert "nome_completo" in u
        assert "tipo" in u
        assert "funcao" in u

    def test_senha_nao_vaza(self, usuario_a):
        resultado = listar_usuarios()
        assert "senha" not in resultado[0]

    def test_ordenado_por_id(self, usuario_a, usuario_b):
        resultado = listar_usuarios()
        ids = [u["id"] for u in resultado]
        assert ids == sorted(ids)


# ═════════════════════════════════════════════════════════════════════════════
# EXCLUIR USUÁRIO
# ═════════════════════════════════════════════════════════════════════════════

class TestExcluirUsuario:
    def test_retorna_mensagem(self, usuario_a):
        resultado = excluir_usuario(usuario_a["id"])
        assert "mensagem" in resultado

    def test_remove_do_banco(self, usuario_a):
        excluir_usuario(usuario_a["id"])
        assert listar_usuarios() == []

    def test_id_inexistente_levanta_erro(self):
        with pytest.raises(ValueError, match="não encontrado"):
            excluir_usuario(99999)

    def test_nao_afeta_outro_usuario(self, usuario_a, usuario_b):
        excluir_usuario(usuario_a["id"])
        restantes = listar_usuarios()
        assert len(restantes) == 1
        assert restantes[0]["id"] == usuario_b["id"]

    def test_excluir_mesmo_usuario_duas_vezes_falha(self, usuario_a):
        excluir_usuario(usuario_a["id"])
        with pytest.raises(ValueError, match="não encontrado"):
            excluir_usuario(usuario_a["id"])

    def test_excluir_remove_dados_relacionados(self, usuario_a):
        pid = usuario_a["id"]
        excluir_usuario(pid)
        session = SessionLocal()
        try:
            assert session.query(Email).filter_by(id_pessoa=pid).first() is None
            assert session.query(Telefone).filter_by(id_pessoa=pid).first() is None
            assert session.query(Endereco).filter_by(id_pessoa=pid).first() is None
            assert session.query(Pessoa_fisica).filter_by(id_pessoa=pid).first() is None
        finally:
            session.close()


# ═════════════════════════════════════════════════════════════════════════════
# BUSCAR PERFIL
# ═════════════════════════════════════════════════════════════════════════════

class TestBuscarPerfil:
    def test_retorna_dict(self, usuario_a):
        resultado = buscar_perfil(usuario_a["id"])
        assert isinstance(resultado, dict)

    def test_contem_nome_completo(self, usuario_a):
        resultado = buscar_perfil(usuario_a["id"])
        assert resultado["nome_completo"] == "Ana Souza"

    def test_contem_cpf(self, usuario_a):
        resultado = buscar_perfil(usuario_a["id"])
        assert resultado["cpf"] == "52998224725"

    def test_contem_email_pessoal(self, usuario_a):
        resultado = buscar_perfil(usuario_a["id"])
        assert resultado["email_pessoal"] == "ana@teste.com"

    def test_contem_telefone_celular(self, usuario_a):
        resultado = buscar_perfil(usuario_a["id"])
        assert resultado["telefone_celular"] == "51988880000"

    def test_contem_campos_de_endereco(self, usuario_a):
        resultado = buscar_perfil(usuario_a["id"])
        assert resultado["cep"] == "96810000"
        assert resultado["cidade"] == "Santa Cruz do Sul"
        assert resultado["estado"] == "RS"

    def test_senha_nao_vaza(self, usuario_a):
        resultado = buscar_perfil(usuario_a["id"])
        assert "senha" not in resultado

    def test_id_inexistente_levanta_erro(self):
        with pytest.raises(ValueError, match="não encontrado"):
            buscar_perfil(99999)

    def test_tipo_correto(self, usuario_a):
        resultado = buscar_perfil(usuario_a["id"])
        assert resultado["tipo"] == "voluntario"

    def test_data_nasc_presente(self, usuario_a):
        resultado = buscar_perfil(usuario_a["id"])
        assert resultado["data_nasc"] is not None


# ═════════════════════════════════════════════════════════════════════════════
# EDITAR PERFIL
# ═════════════════════════════════════════════════════════════════════════════

class TestEditarPerfil:
    def test_editar_nome_completo(self, usuario_a):
        resultado = editar_perfil(usuario_a["id"], {"nome_completo": "Ana Lima"})
        assert resultado["nome_completo"] == "Ana Lima"

    def test_editar_funcao(self, usuario_a):
        resultado = editar_perfil(usuario_a["id"], {"funcao": "coordenador"})
        assert resultado["funcao"] == "coordenador"

    def test_editar_data_nasc(self, usuario_a):
        editar_perfil(usuario_a["id"], {"data_nasc": "20-07-1990"})
        perfil = buscar_perfil(usuario_a["id"])
        assert "1990" in str(perfil["data_nasc"])

    def test_editar_cpf(self, usuario_a):
        editar_perfil(usuario_a["id"], {"cpf": "11144477735"})
        perfil = buscar_perfil(usuario_a["id"])
        assert perfil["cpf"] == "11144477735"

    def test_editar_email(self, usuario_a):
        editar_perfil(usuario_a["id"], {"email_pessoal": "novo@teste.com"})
        perfil = buscar_perfil(usuario_a["id"])
        assert perfil["email_pessoal"] == "novo@teste.com"

    def test_editar_telefone(self, usuario_a):
        editar_perfil(usuario_a["id"], {"telefone_celular": "51977770000"})
        perfil = buscar_perfil(usuario_a["id"])
        assert perfil["telefone_celular"] == "51977770000"

    def test_editar_endereco(self, usuario_a):
        editar_perfil(usuario_a["id"], {"cep": "01310100", "cidade": "São Paulo", "estado": "SP"})
        perfil = buscar_perfil(usuario_a["id"])
        assert perfil["cidade"] == "São Paulo"
        assert perfil["estado"] == "SP"

    def test_editar_senha_permite_novo_login(self, usuario_a):
        from app.servicos import login
        editar_perfil(usuario_a["id"], {"senha": "novasenha456"})
        resultado = login({"email": "ana@teste.com", "senha": "novasenha456"})
        assert resultado["id"] == usuario_a["id"]

    def test_editar_senha_curta_falha(self, usuario_a):
        with pytest.raises(ValueError, match="senha"):
            editar_perfil(usuario_a["id"], {"senha": "abc"})

    def test_editar_cpf_duplicado_falha(self, usuario_a, usuario_b):
        with pytest.raises(ValueError, match="CPF"):
            editar_perfil(usuario_a["id"], {"cpf": "11144477735"})

    def test_editar_email_duplicado_falha(self, usuario_a, usuario_b):
        with pytest.raises(ValueError, match="e-mail"):
            editar_perfil(usuario_a["id"], {"email_pessoal": "carlos@teste.com"})

    def test_editar_cpf_invalido_falha(self, usuario_a):
        with pytest.raises(ValueError, match="CPF"):
            editar_perfil(usuario_a["id"], {"cpf": "123"})

    def test_editar_nome_vazio_falha(self, usuario_a):
        with pytest.raises(ValueError, match="nome_completo"):
            editar_perfil(usuario_a["id"], {"nome_completo": ""})

    def test_campo_nao_enviado_nao_muda(self, usuario_a):
        editar_perfil(usuario_a["id"], {"funcao": "coordenador"})
        perfil = buscar_perfil(usuario_a["id"])
        assert perfil["nome_completo"] == "Ana Souza"

    def test_id_inexistente_levanta_erro(self):
        with pytest.raises(ValueError, match="não encontrado"):
            editar_perfil(99999, {"funcao": "tecnico"})

    def test_editar_mesmo_cpf_do_proprio_usuario_aceita(self, usuario_a):
        resultado = editar_perfil(usuario_a["id"], {"cpf": "52998224725"})
        assert resultado is not None

    def test_editar_mesmo_email_do_proprio_usuario_aceita(self, usuario_a):
        resultado = editar_perfil(usuario_a["id"], {"email_pessoal": "ana@teste.com"})
        assert resultado is not None

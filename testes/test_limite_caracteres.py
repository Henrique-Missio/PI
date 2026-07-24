"""
Testes do limite de caracteres (item 4 da pesquisa de UX) aplicado em
cadastrar_aparelho, cadastrar_peca e cadastrar_usuario.
"""
import pytest
from app.servicos import cadastrar_aparelho, cadastrar_peca, cadastrar_usuario, editar_aparelho
from app.database import SessionLocal
from app.models import Aparelhos, Pecas, Estoque, Pessoa, Pessoa_fisica, Endereco, Email, Telefone

APARELHO_BASE = {
    "nome": "Notebook", "marca": "Dell", "informacoes": "Info",
    "problema": "Nenhum", "status": "Funcional",
}
PECA_BASE = {
    "nome": "Placa", "marca": "NVIDIA", "informacoes": "Info", "status": "Funcional",
}
USUARIO_BASE = {
    "nome_completo": "Usuario Teste", "cpf": "52998224725", "funcao": "tecnico",
    "email_pessoal": "limite@teste.com", "telefone_celular": "51988880000",
    "cep": "96810000", "rua": "Rua X", "numero": "1", "bairro": "Centro",
    "cidade": "Santa Cruz do Sul", "estado": "RS", "senha": "Senha@123",
    "data_nasc": "10-05-2000",
}


@pytest.fixture(autouse=True)
def limpar_tudo():
    def _limpar():
        s = SessionLocal()
        try:
            s.query(Estoque).delete()
            s.query(Aparelhos).delete()
            s.query(Pecas).delete()
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


class TestLimiteAparelho:
    def test_nome_no_limite_120_aceito(self):
        r = cadastrar_aparelho({**APARELHO_BASE, "nome": "A" * 120})
        assert len(r["nome"]) == 120

    def test_nome_acima_de_120_falha(self):
        with pytest.raises(ValueError, match="120"):
            cadastrar_aparelho({**APARELHO_BASE, "nome": "A" * 121})

    def test_marca_acima_de_40_falha(self):
        with pytest.raises(ValueError, match="40"):
            cadastrar_aparelho({**APARELHO_BASE, "marca": "A" * 41})

    def test_informacoes_acima_de_1500_falha(self):
        with pytest.raises(ValueError, match="1500"):
            cadastrar_aparelho({**APARELHO_BASE, "informacoes": "A" * 1501})

    def test_problema_acima_de_500_falha(self):
        with pytest.raises(ValueError, match="500"):
            cadastrar_aparelho({**APARELHO_BASE, "problema": "A" * 501})

    def test_editar_nome_acima_do_limite_falha(self):
        ap = cadastrar_aparelho(APARELHO_BASE)
        with pytest.raises(ValueError, match="120"):
            editar_aparelho(ap["id"], {"nome": "A" * 121})


class TestLimitePeca:
    def test_nome_acima_de_120_falha(self):
        with pytest.raises(ValueError, match="120"):
            cadastrar_peca({**PECA_BASE, "nome": "A" * 121})

    def test_informacoes_acima_de_1500_falha(self):
        with pytest.raises(ValueError, match="1500"):
            cadastrar_peca({**PECA_BASE, "informacoes": "A" * 1501})

    def test_problema_opcional_acima_de_500_falha(self):
        with pytest.raises(ValueError, match="500"):
            cadastrar_peca({**PECA_BASE, "problema": "A" * 501})


class TestLimiteUsuario:
    def test_nome_completo_acima_de_60_falha(self):
        with pytest.raises(ValueError, match="60"):
            cadastrar_usuario({**USUARIO_BASE, "nome_completo": "A" * 61})

    def test_funcao_acima_de_20_falha(self):
        with pytest.raises(ValueError, match="20"):
            cadastrar_usuario({**USUARIO_BASE, "funcao": "A" * 21})

    def test_email_acima_de_40_falha(self):
        email_longo = "A" * 35 + "@a.com"  # > 40 chars
        with pytest.raises(ValueError, match="40"):
            cadastrar_usuario({**USUARIO_BASE, "email_pessoal": email_longo})

    def test_rua_acima_de_60_falha(self):
        with pytest.raises(ValueError, match="60"):
            cadastrar_usuario({**USUARIO_BASE, "rua": "A" * 61})

    def test_bairro_acima_de_30_falha(self):
        with pytest.raises(ValueError, match="30"):
            cadastrar_usuario({**USUARIO_BASE, "bairro": "A" * 31})

    def test_cidade_no_limite_30_aceito(self):
        r = cadastrar_usuario({**USUARIO_BASE, "cidade": "A" * 30})
        assert r is not None

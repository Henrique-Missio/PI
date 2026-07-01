"""
Testes das funcionalidades recentes:
- gerar_dados_relatorio (relatorio.py)
- gerar_pdf (relatorio.py)
- cadastrar voluntário pelo admin (servicos.py)
- excluir voluntário pelo admin — regra: não pode excluir admin
"""
import pytest
from datetime import date, timedelta

from app.servicos import (
    cadastrar_usuario, listar_usuarios, excluir_usuario,
)
from app.relatorio import gerar_dados_relatorio, gerar_pdf
from app.database import SessionLocal
from app.models import Pessoa, Pessoa_fisica, Endereco, Email, Telefone, Aparelhos, Pecas, Estoque


# ── Payloads base ─────────────────────────────────────────────────────────────

VOLUNTARIO_BASE = {
    "nome_completo":    "Maria Voluntária",
    "cpf":              "52998224725",
    "funcao":           "tecnico",
    "email_pessoal":    "maria@teste.com",
    "telefone_celular": "51988880000",
    "cep":              "96810000",
    "rua":              "Rua Sinimbu",
    "numero":           "100",
    "bairro":           "Centro",
    "cidade":           "Santa Cruz do Sul",
    "estado":           "RS",
    "senha":            "senha123",
    "data_nasc":        "10-05-1995",
}

ADMIN_BASE = {
    **VOLUNTARIO_BASE,
    "nome_completo":    "Admin Teste",
    "cpf":              "11144477735",
    "email_pessoal":    "admin@teste.com",
}

VOLUNTARIO_B = {
    **VOLUNTARIO_BASE,
    "nome_completo":    "Carlos Voluntário",
    "cpf":              "85249637010",
    "email_pessoal":    "carlos@teste.com",
}

APARELHO_BASE = {
    "nome":        "Notebook Dell",
    "marca":       "Dell",
    "informacoes": "Core i5, 8GB RAM",
    "problema":    "Tela trincada",
    "status":      "Em conserto",
}

PECA_BASE = {
    "nome":        "Placa de vídeo",
    "marca":       "NVIDIA",
    "informacoes": "GTX 1050",
    "status":      "Funcional",
}


# ── Fixtures de limpeza ───────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def limpar_tudo():
    def _limpar():
        session = SessionLocal()
        try:
            session.query(Estoque).delete()
            session.query(Aparelhos).delete()
            session.query(Pecas).delete()
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
def voluntario():
    return cadastrar_usuario(VOLUNTARIO_BASE, tipo="voluntario")


@pytest.fixture
def admin():
    return cadastrar_usuario(ADMIN_BASE, tipo="administrador")


@pytest.fixture
def voluntario_b():
    return cadastrar_usuario(VOLUNTARIO_B, tipo="voluntario")


# ═════════════════════════════════════════════════════════════════════════════
# CADASTRO DE VOLUNTÁRIO PELO ADMIN
# ═════════════════════════════════════════════════════════════════════════════

class TestCadastroVoluntarioPeloAdmin:
    def test_cadastrar_voluntario_retorna_dict(self):
        resultado = cadastrar_usuario(VOLUNTARIO_BASE, tipo="voluntario")
        assert isinstance(resultado, dict)

    def test_tipo_voluntario_correto(self):
        resultado = cadastrar_usuario(VOLUNTARIO_BASE, tipo="voluntario")
        assert resultado["tipo"] == "voluntario"

    def test_cadastrar_admin_retorna_tipo_administrador(self):
        resultado = cadastrar_usuario(VOLUNTARIO_BASE, tipo="administrador")
        assert resultado["tipo"] == "administrador"

    def test_voluntario_aparece_na_listagem(self):
        cadastrar_usuario(VOLUNTARIO_BASE, tipo="voluntario")
        usuarios = listar_usuarios()
        voluntarios = [u for u in usuarios if u["tipo"] == "voluntario"]
        assert len(voluntarios) == 1

    def test_multiplos_voluntarios_cadastrados(self, voluntario):
        cadastrar_usuario(VOLUNTARIO_B, tipo="voluntario")
        usuarios = listar_usuarios()
        voluntarios = [u for u in usuarios if u["tipo"] == "voluntario"]
        assert len(voluntarios) == 2

    def test_nome_correto_no_cadastro(self):
        resultado = cadastrar_usuario(VOLUNTARIO_BASE, tipo="voluntario")
        assert resultado["nome_completo"] == "Maria Voluntária"

    def test_senha_nao_vaza_no_retorno(self):
        resultado = cadastrar_usuario(VOLUNTARIO_BASE, tipo="voluntario")
        assert "senha" not in resultado

    def test_cpf_duplicado_falha(self, voluntario):
        dados = {**VOLUNTARIO_BASE, "email_pessoal": "outro@teste.com"}
        with pytest.raises(ValueError, match="CPF"):
            cadastrar_usuario(dados, tipo="voluntario")

    def test_email_duplicado_falha(self, voluntario):
        dados = {**VOLUNTARIO_BASE, "cpf": "11144477735"}
        with pytest.raises(ValueError, match="e-mail"):
            cadastrar_usuario(dados, tipo="voluntario")

    def test_tipo_invalido_falha(self):
        with pytest.raises(ValueError, match="[Tt]ipo"):
            cadastrar_usuario(VOLUNTARIO_BASE, tipo="superadmin")

    def test_senha_curta_falha(self):
        dados = {**VOLUNTARIO_BASE, "senha": "abc"}
        with pytest.raises(ValueError, match="senha"):
            cadastrar_usuario(dados, tipo="voluntario")

    def test_campo_obrigatorio_ausente_falha(self):
        dados = {**VOLUNTARIO_BASE, "nome_completo": ""}
        with pytest.raises(ValueError, match="nome_completo"):
            cadastrar_usuario(dados, tipo="voluntario")


# ═════════════════════════════════════════════════════════════════════════════
# EXCLUSÃO DE VOLUNTÁRIO PELO ADMIN
# ═════════════════════════════════════════════════════════════════════════════

class TestExclusaoVoluntarioPeloAdmin:
    def test_excluir_voluntario_retorna_mensagem(self, voluntario):
        resultado = excluir_usuario(voluntario["id"])
        assert "mensagem" in resultado

    def test_excluir_voluntario_remove_da_listagem(self, voluntario):
        excluir_usuario(voluntario["id"])
        usuarios = listar_usuarios()
        ids = [u["id"] for u in usuarios]
        assert voluntario["id"] not in ids

    def test_excluir_voluntario_nao_afeta_admin(self, admin, voluntario):
        excluir_usuario(voluntario["id"])
        usuarios = listar_usuarios()
        ids = [u["id"] for u in usuarios]
        assert admin["id"] in ids

    def test_excluir_admin_via_servico_e_possivel(self, admin):
        """O servico.py permite excluir admin — a regra de negócio fica na rota."""
        resultado = excluir_usuario(admin["id"])
        assert "mensagem" in resultado

    def test_excluir_id_inexistente_falha(self):
        with pytest.raises(ValueError, match="não encontrado"):
            excluir_usuario(99999)

    def test_excluir_voluntario_nao_afeta_outro_voluntario(self, voluntario, voluntario_b):
        excluir_usuario(voluntario["id"])
        usuarios = listar_usuarios()
        ids = [u["id"] for u in usuarios]
        assert voluntario_b["id"] in ids

    def test_excluir_remove_dados_relacionados(self, voluntario):
        pid = voluntario["id"]
        excluir_usuario(pid)
        session = SessionLocal()
        try:
            assert session.query(Email).filter_by(id_pessoa=pid).first() is None
            assert session.query(Pessoa_fisica).filter_by(id_pessoa=pid).first() is None
            assert session.query(Endereco).filter_by(id_pessoa=pid).first() is None
            assert session.query(Telefone).filter_by(id_pessoa=pid).first() is None
        finally:
            session.close()

    def test_excluir_duas_vezes_falha(self, voluntario):
        excluir_usuario(voluntario["id"])
        with pytest.raises(ValueError, match="não encontrado"):
            excluir_usuario(voluntario["id"])

    def test_listar_so_voluntarios(self, admin, voluntario, voluntario_b):
        usuarios = listar_usuarios()
        voluntarios = [u for u in usuarios if u["tipo"] == "voluntario"]
        admins = [u for u in usuarios if u["tipo"] == "administrador"]
        assert len(voluntarios) == 2
        assert len(admins) == 1


# ═════════════════════════════════════════════════════════════════════════════
# GERAR DADOS DE RELATÓRIO
# ═════════════════════════════════════════════════════════════════════════════

class TestGerarDadosRelatorio:
    def _criar_aparelho(self, dados=None):
        from app.servicos import cadastrar_aparelho
        return cadastrar_aparelho(dados or APARELHO_BASE)

    def _criar_peca(self, dados=None):
        from app.servicos import cadastrar_peca
        return cadastrar_peca(dados or PECA_BASE)

    def test_retorna_dict(self):
        dados = gerar_dados_relatorio()
        assert isinstance(dados, dict)

    def test_campos_obrigatorios_presentes(self):
        dados = gerar_dados_relatorio()
        for campo in ["gerado_em", "total", "recebidos_mes", "doados",
                      "consertados_mes", "status_count", "por_mes", "itens"]:
            assert campo in dados

    def test_total_zero_sem_itens(self):
        dados = gerar_dados_relatorio()
        assert dados["total"] == 0

    def test_total_com_aparelho(self):
        self._criar_aparelho()
        dados = gerar_dados_relatorio()
        assert dados["total"] == 1

    def test_total_com_peca(self):
        self._criar_peca()
        dados = gerar_dados_relatorio()
        assert dados["total"] == 1

    def test_total_misto(self):
        self._criar_aparelho()
        self._criar_peca()
        dados = gerar_dados_relatorio()
        assert dados["total"] == 2

    def test_filtro_categoria_aparelho(self):
        self._criar_aparelho()
        self._criar_peca()
        dados = gerar_dados_relatorio(categoria="aparelho")
        assert dados["total"] == 1
        assert all(i["categoria"] == "aparelho" for i in dados["itens"])

    def test_filtro_categoria_peca(self):
        self._criar_aparelho()
        self._criar_peca()
        dados = gerar_dados_relatorio(categoria="peca")
        assert dados["total"] == 1
        assert all(i["categoria"] == "peca" for i in dados["itens"])

    def test_filtro_nome_parcial(self):
        self._criar_aparelho()
        self._criar_peca()
        dados = gerar_dados_relatorio(nome="notebook")
        assert dados["total"] == 1
        assert dados["itens"][0]["nome"] == "Notebook Dell"

    def test_filtro_nome_case_insensitive(self):
        self._criar_aparelho()
        dados = gerar_dados_relatorio(nome="NOTEBOOK")
        assert dados["total"] == 1

    def test_filtro_nome_inexistente_retorna_zero(self):
        self._criar_aparelho()
        dados = gerar_dados_relatorio(nome="impressora")
        assert dados["total"] == 0

    def test_status_count_correto(self):
        self._criar_aparelho()  # status "Em conserto"
        dados = gerar_dados_relatorio()
        assert "Em conserto" in dados["status_count"]
        assert dados["status_count"]["Em conserto"] == 1

    def test_itens_retorna_lista(self):
        self._criar_aparelho()
        dados = gerar_dados_relatorio()
        assert isinstance(dados["itens"], list)

    def test_itens_contem_campos_essenciais(self):
        self._criar_aparelho()
        dados = gerar_dados_relatorio()
        item = dados["itens"][0]
        for campo in ["nome", "marca", "status", "categoria"]:
            assert campo in item

    def test_filtro_data_exclui_itens_fora_do_periodo(self):
        self._criar_aparelho()
        amanha = (date.today() + timedelta(days=1)).isoformat()
        depois = (date.today() + timedelta(days=2)).isoformat()
        dados = gerar_dados_relatorio(data_de=amanha, data_ate=depois)
        assert dados["total"] == 0

    def test_filtro_data_inclui_itens_no_periodo(self):
        self._criar_aparelho()
        ontem = (date.today() - timedelta(days=1)).isoformat()
        amanha = (date.today() + timedelta(days=1)).isoformat()
        dados = gerar_dados_relatorio(data_de=ontem, data_ate=amanha)
        assert dados["total"] == 1

    def test_doados_conta_apenas_status_doado(self):
        from app.servicos import cadastrar_aparelho
        cadastrar_aparelho({**APARELHO_BASE, "status": "Doado"})
        cadastrar_aparelho({**APARELHO_BASE, "nome": "Outro", "status": "Funcional"})
        dados = gerar_dados_relatorio()
        assert dados["doados"] == 1

    def test_gerado_em_formato_correto(self):
        dados = gerar_dados_relatorio()
        partes = dados["gerado_em"].split("/")
        assert len(partes) == 3  # DD/MM/AAAA

    def test_sem_filtros_retorna_tudo(self):
        self._criar_aparelho()
        self._criar_peca()
        dados = gerar_dados_relatorio()
        assert dados["total"] == 2


# ═════════════════════════════════════════════════════════════════════════════
# GERAR PDF
# ═════════════════════════════════════════════════════════════════════════════

class TestGerarPdf:
    def _dados_base(self, **kwargs):
        from app.servicos import cadastrar_aparelho
        cadastrar_aparelho(APARELHO_BASE)
        return gerar_dados_relatorio(**kwargs)

    def test_retorna_bytes(self):
        dados = gerar_dados_relatorio()
        pdf = gerar_pdf(dados)
        assert isinstance(pdf, bytes)

    def test_pdf_nao_vazio(self):
        dados = gerar_dados_relatorio()
        pdf = gerar_pdf(dados)
        assert len(pdf) > 0

    def test_pdf_comeca_com_assinatura_pdf(self):
        dados = gerar_dados_relatorio()
        pdf = gerar_pdf(dados)
        assert pdf[:4] == b"%PDF"

    def test_pdf_sem_itens_gera_sem_erro(self):
        dados = gerar_dados_relatorio()
        try:
            pdf = gerar_pdf(dados)
            assert isinstance(pdf, bytes)
        except Exception as e:
            pytest.fail(f"gerar_pdf levantou exceção com dados vazios: {e}")

    def test_pdf_com_itens_gera_sem_erro(self):
        dados = self._dados_base()
        try:
            pdf = gerar_pdf(dados)
            assert isinstance(pdf, bytes)
        except Exception as e:
            pytest.fail(f"gerar_pdf levantou exceção com dados preenchidos: {e}")

    def test_pdf_com_filtros_aplicados(self):
        dados = self._dados_base(categoria="aparelho", nome="notebook")
        pdf = gerar_pdf(dados)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 0

    def test_pdf_com_status_count_vazio(self):
        dados = gerar_dados_relatorio()
        dados["status_count"] = {}
        pdf = gerar_pdf(dados)
        assert isinstance(pdf, bytes)

    def test_pdf_com_por_mes_vazio(self):
        dados = gerar_dados_relatorio()
        dados["por_mes"] = {}
        pdf = gerar_pdf(dados)
        assert isinstance(pdf, bytes)

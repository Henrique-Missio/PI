"""
Testes do estoque: cadastrar, editar, excluir e listar Aparelhos e Peças.
Testa as funções reais do servicos.py, que gerenciam seu próprio SessionLocal.
"""
import pytest
from app.servicos import (
    cadastrar_aparelho, editar_aparelho, excluir_aparelho,
    buscar_aparelho_por_id, listar_aparelhos,
    cadastrar_peca, editar_peca, excluir_peca,
    buscar_peca_por_id, listar_pecas,
    listar_estoque, buscar_estoque_por_id,
)
from app.database import SessionLocal
from app.models import Aparelhos, Pecas, Estoque


# ── Payload base reutilizável ─────────────────────────────────────────────────

APARELHO_VALIDO = {
    "nome":        "Notebook Dell",
    "marca":       "Dell",
    "informacoes": "Core i5, 8GB RAM, 256GB SSD",
    "problema":    "Tela trincada",
    "status":      "em reparo",
}

PECA_VALIDA = {
    "nome":        "Placa de vídeo",
    "marca":       "NVIDIA",
    "informacoes": "GTX 1050, 4GB GDDR5",
    "problema":    "Superaquecimento",
    "status":      "disponivel",
}


# ── Fixture de limpeza ────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def limpar_estoque():
    """Limpa Aparelhos, Peças e Estoque antes de cada teste."""
    session = SessionLocal()
    try:
        session.query(Estoque).delete()
        session.query(Aparelhos).delete()
        session.query(Pecas).delete()
        session.commit()
    finally:
        session.close()
    yield
    # limpeza também após o teste
    session = SessionLocal()
    try:
        session.query(Estoque).delete()
        session.query(Aparelhos).delete()
        session.query(Pecas).delete()
        session.commit()
    finally:
        session.close()


# ═════════════════════════════════════════════════════════════════════════════
# APARELHOS
# ═════════════════════════════════════════════════════════════════════════════

class TestCadastrarAparelho:
    def test_cadastro_retorna_dict(self):
        resultado = cadastrar_aparelho(APARELHO_VALIDO)
        assert isinstance(resultado, dict)

    def test_cadastro_persiste_no_banco(self):
        resultado = cadastrar_aparelho(APARELHO_VALIDO)
        buscado = buscar_aparelho_por_id(resultado["id"])
        assert buscado["nome"] == "Notebook Dell"

    def test_cadastro_cria_entrada_no_estoque(self):
        resultado = cadastrar_aparelho(APARELHO_VALIDO)
        session = SessionLocal()
        try:
            estoque = session.query(Estoque).filter_by(
                id_aparelho=resultado["id"]
            ).first()
            assert estoque is not None
            assert estoque.categoria == "aparelho"
        finally:
            session.close()

    def test_cadastro_campos_corretos(self):
        resultado = cadastrar_aparelho(APARELHO_VALIDO)
        assert resultado["nome"] == "Notebook Dell"
        assert resultado["marca"] == "Dell"
        assert resultado["status"] == "em reparo"
        assert resultado["problema"] == "Tela trincada"

    def test_cadastro_data_entrada_padrao_hoje(self):
        from datetime import date
        resultado = cadastrar_aparelho(APARELHO_VALIDO)
        assert resultado["data_entrada"] == str(date.today())

    def test_cadastro_data_saida_nula_por_padrao(self):
        resultado = cadastrar_aparelho(APARELHO_VALIDO)
        assert resultado["data_saida"] is None

    def test_cadastro_com_data_entrada_explicita(self):
        dados = {**APARELHO_VALIDO, "data_entrada": "01-01-2024"}
        resultado = cadastrar_aparelho(dados)
        assert resultado["data_entrada"] == "2024-01-01"

    def test_cadastro_nome_obrigatorio(self):
        dados = {**APARELHO_VALIDO, "nome": ""}
        with pytest.raises(ValueError, match="nome"):
            cadastrar_aparelho(dados)

    def test_cadastro_marca_obrigatoria(self):
        dados = {**APARELHO_VALIDO, "marca": ""}
        with pytest.raises(ValueError, match="marca"):
            cadastrar_aparelho(dados)

    def test_cadastro_informacoes_obrigatorias(self):
        dados = {**APARELHO_VALIDO, "informacoes": ""}
        with pytest.raises(ValueError, match="informacoes"):
            cadastrar_aparelho(dados)

    def test_cadastro_problema_obrigatorio(self):
        dados = {**APARELHO_VALIDO, "problema": ""}
        with pytest.raises(ValueError, match="problema"):
            cadastrar_aparelho(dados)

    def test_cadastro_status_obrigatorio(self):
        dados = {**APARELHO_VALIDO, "status": ""}
        with pytest.raises(ValueError, match="status"):
            cadastrar_aparelho(dados)

    def test_cadastro_nome_apenas_espacos_falha(self):
        dados = {**APARELHO_VALIDO, "nome": "   "}
        with pytest.raises(ValueError):
            cadastrar_aparelho(dados)

    def test_cadastro_data_formato_invalido(self):
        dados = {**APARELHO_VALIDO, "data_entrada": "2024/01/01"}
        with pytest.raises(ValueError):
            cadastrar_aparelho(dados)


class TestEditarAparelho:
    def test_editar_nome(self):
        ap = cadastrar_aparelho(APARELHO_VALIDO)
        resultado = editar_aparelho(ap["id"], {"nome": "Notebook HP"})
        assert resultado["nome"] == "Notebook HP"

    def test_editar_marca(self):
        ap = cadastrar_aparelho(APARELHO_VALIDO)
        resultado = editar_aparelho(ap["id"], {"marca": "HP"})
        assert resultado["marca"] == "HP"

    def test_editar_status(self):
        ap = cadastrar_aparelho(APARELHO_VALIDO)
        resultado = editar_aparelho(ap["id"], {"status": "disponivel"})
        assert resultado["status"] == "disponivel"

    def test_editar_multiplos_campos(self):
        ap = cadastrar_aparelho(APARELHO_VALIDO)
        resultado = editar_aparelho(ap["id"], {
            "nome": "Notebook Lenovo",
            "marca": "Lenovo",
            "status": "doado",
        })
        assert resultado["nome"] == "Notebook Lenovo"
        assert resultado["marca"] == "Lenovo"
        assert resultado["status"] == "doado"

    def test_editar_persiste_no_banco(self):
        ap = cadastrar_aparelho(APARELHO_VALIDO)
        editar_aparelho(ap["id"], {"nome": "Editado"})
        buscado = buscar_aparelho_por_id(ap["id"])
        assert buscado["nome"] == "Editado"

    def test_editar_campo_nao_enviado_nao_muda(self):
        ap = cadastrar_aparelho(APARELHO_VALIDO)
        editar_aparelho(ap["id"], {"status": "doado"})
        buscado = buscar_aparelho_por_id(ap["id"])
        assert buscado["marca"] == "Dell"  # não foi alterada

    def test_editar_id_inexistente_levanta_erro(self):
        with pytest.raises(ValueError, match="não encontrado"):
            editar_aparelho(99999, {"nome": "X"})

    def test_editar_nome_vazio_falha(self):
        ap = cadastrar_aparelho(APARELHO_VALIDO)
        with pytest.raises(ValueError, match="nome"):
            editar_aparelho(ap["id"], {"nome": ""})

    def test_editar_data_saida_como_none(self):
        ap = cadastrar_aparelho(APARELHO_VALIDO)
        resultado = editar_aparelho(ap["id"], {"data_saida": None})
        assert resultado["data_saida"] is None

    def test_editar_data_saida_valida(self):
        ap = cadastrar_aparelho(APARELHO_VALIDO)
        resultado = editar_aparelho(ap["id"], {"data_saida": "10-06-2025"})
        assert resultado["data_saida"] == "2025-06-10"


class TestExcluirAparelho:
    def test_excluir_retorna_mensagem(self):
        ap = cadastrar_aparelho(APARELHO_VALIDO)
        resultado = excluir_aparelho(ap["id"])
        assert "mensagem" in resultado

    def test_excluir_remove_do_banco(self):
        ap = cadastrar_aparelho(APARELHO_VALIDO)
        excluir_aparelho(ap["id"])
        with pytest.raises(ValueError):
            buscar_aparelho_por_id(ap["id"])

    def test_excluir_remove_estoque_em_cascata(self):
        ap = cadastrar_aparelho(APARELHO_VALIDO)
        ap_id = ap["id"]
        excluir_aparelho(ap_id)
        session = SessionLocal()
        try:
            estoque = session.query(Estoque).filter_by(
                id_aparelho=ap_id).first()
            assert estoque is None
        finally:
            session.close()

    def test_excluir_id_inexistente_levanta_erro(self):
        with pytest.raises(ValueError, match="não encontrado"):
            excluir_aparelho(99999)

    def test_excluir_nao_afeta_outros_aparelhos(self):
        ap1 = cadastrar_aparelho(APARELHO_VALIDO)
        ap2 = cadastrar_aparelho({**APARELHO_VALIDO, "nome": "Outro Aparelho"})
        excluir_aparelho(ap1["id"])
        buscado = buscar_aparelho_por_id(ap2["id"])
        assert buscado["id"] == ap2["id"]


class TestListarBuscarAparelho:
    def test_listar_retorna_lista(self):
        assert isinstance(listar_aparelhos(), list)

    def test_listar_vazio(self):
        assert listar_aparelhos() == []

    def test_listar_com_itens(self):
        cadastrar_aparelho(APARELHO_VALIDO)
        cadastrar_aparelho({**APARELHO_VALIDO, "nome": "Segundo"})
        assert len(listar_aparelhos()) == 2

    def test_buscar_por_id_retorna_dict(self):
        ap = cadastrar_aparelho(APARELHO_VALIDO)
        buscado = buscar_aparelho_por_id(ap["id"])
        assert isinstance(buscado, dict)
        assert buscado["id"] == ap["id"]

    def test_buscar_id_inexistente_levanta_erro(self):
        with pytest.raises(ValueError, match="não encontrado"):
            buscar_aparelho_por_id(99999)


# ═════════════════════════════════════════════════════════════════════════════
# PEÇAS
# ═════════════════════════════════════════════════════════════════════════════

class TestCadastrarPeca:
    def test_cadastro_retorna_dict(self):
        resultado = cadastrar_peca(PECA_VALIDA)
        assert isinstance(resultado, dict)

    def test_cadastro_persiste_no_banco(self):
        resultado = cadastrar_peca(PECA_VALIDA)
        buscada = buscar_peca_por_id(resultado["id"])
        assert buscada["nome"] == "Placa de vídeo"

    def test_cadastro_cria_entrada_no_estoque(self):
        resultado = cadastrar_peca(PECA_VALIDA)
        session = SessionLocal()
        try:
            estoque = session.query(Estoque).filter_by(
                id_pecas=resultado["id"]
            ).first()
            assert estoque is not None
            assert estoque.categoria == "peca"
        finally:
            session.close()

    def test_cadastro_problema_opcional(self):
        dados = {**PECA_VALIDA, "problema": None}
        resultado = cadastrar_peca(dados)
        assert resultado["problema"] is None

    def test_cadastro_problema_vazio_vira_none(self):
        dados = {**PECA_VALIDA, "problema": ""}
        resultado = cadastrar_peca(dados)
        assert resultado["problema"] is None

    def test_cadastro_data_saida_nula_por_padrao(self):
        resultado = cadastrar_peca(PECA_VALIDA)
        assert resultado["data_saida"] is None

    def test_cadastro_nome_obrigatorio(self):
        dados = {**PECA_VALIDA, "nome": ""}
        with pytest.raises(ValueError, match="nome"):
            cadastrar_peca(dados)

    def test_cadastro_marca_obrigatoria(self):
        dados = {**PECA_VALIDA, "marca": ""}
        with pytest.raises(ValueError, match="marca"):
            cadastrar_peca(dados)

    def test_cadastro_informacoes_obrigatorias(self):
        dados = {**PECA_VALIDA, "informacoes": ""}
        with pytest.raises(ValueError, match="informacoes"):
            cadastrar_peca(dados)

    def test_cadastro_status_obrigatorio(self):
        dados = {**PECA_VALIDA, "status": ""}
        with pytest.raises(ValueError, match="status"):
            cadastrar_peca(dados)

    def test_cadastro_nome_apenas_espacos_falha(self):
        dados = {**PECA_VALIDA, "nome": "   "}
        with pytest.raises(ValueError):
            cadastrar_peca(dados)


class TestEditarPeca:
    def test_editar_nome(self):
        peca = cadastrar_peca(PECA_VALIDA)
        resultado = editar_peca(peca["id"], {"nome": "Memória RAM"})
        assert resultado["nome"] == "Memória RAM"

    def test_editar_status(self):
        peca = cadastrar_peca(PECA_VALIDA)
        resultado = editar_peca(peca["id"], {"status": "em reparo"})
        assert resultado["status"] == "em reparo"

    def test_editar_problema_para_none(self):
        peca = cadastrar_peca(PECA_VALIDA)
        resultado = editar_peca(peca["id"], {"problema": None})
        assert resultado["problema"] is None

    def test_editar_multiplos_campos(self):
        peca = cadastrar_peca(PECA_VALIDA)
        resultado = editar_peca(peca["id"], {
            "nome": "HD SSD",
            "marca": "Kingston",
            "status": "doado",
        })
        assert resultado["nome"] == "HD SSD"
        assert resultado["marca"] == "Kingston"
        assert resultado["status"] == "doado"

    def test_editar_persiste_no_banco(self):
        peca = cadastrar_peca(PECA_VALIDA)
        editar_peca(peca["id"], {"nome": "Editada"})
        buscada = buscar_peca_por_id(peca["id"])
        assert buscada["nome"] == "Editada"

    def test_editar_campo_nao_enviado_nao_muda(self):
        peca = cadastrar_peca(PECA_VALIDA)
        editar_peca(peca["id"], {"status": "doado"})
        buscada = buscar_peca_por_id(peca["id"])
        assert buscada["marca"] == "NVIDIA"

    def test_editar_id_inexistente_levanta_erro(self):
        with pytest.raises(ValueError, match="não encontrada"):
            editar_peca(99999, {"nome": "X"})

    def test_editar_nome_vazio_falha(self):
        peca = cadastrar_peca(PECA_VALIDA)
        with pytest.raises(ValueError, match="nome"):
            editar_peca(peca["id"], {"nome": ""})

    def test_editar_data_saida_valida(self):
        peca = cadastrar_peca(PECA_VALIDA)
        resultado = editar_peca(peca["id"], {"data_saida": "15-03-2025"})
        assert resultado["data_saida"] == "2025-03-15"


class TestExcluirPeca:
    def test_excluir_retorna_mensagem(self):
        peca = cadastrar_peca(PECA_VALIDA)
        resultado = excluir_peca(peca["id"])
        assert "mensagem" in resultado

    def test_excluir_remove_do_banco(self):
        peca = cadastrar_peca(PECA_VALIDA)
        excluir_peca(peca["id"])
        with pytest.raises(ValueError):
            buscar_peca_por_id(peca["id"])

    def test_excluir_remove_estoque_em_cascata(self):
        peca = cadastrar_peca(PECA_VALIDA)
        peca_id = peca["id"]
        excluir_peca(peca_id)
        session = SessionLocal()
        try:
            estoque = session.query(Estoque).filter_by(
                id_pecas=peca_id).first()
            assert estoque is None
        finally:
            session.close()

    def test_excluir_id_inexistente_levanta_erro(self):
        with pytest.raises(ValueError, match="não encontrada"):
            excluir_peca(99999)

    def test_excluir_nao_afeta_outras_pecas(self):
        p1 = cadastrar_peca(PECA_VALIDA)
        p2 = cadastrar_peca({**PECA_VALIDA, "nome": "Outra Peça"})
        excluir_peca(p1["id"])
        buscada = buscar_peca_por_id(p2["id"])
        assert buscada["id"] == p2["id"]


class TestListarBuscarPeca:
    def test_listar_retorna_lista(self):
        assert isinstance(listar_pecas(), list)

    def test_listar_vazio(self):
        assert listar_pecas() == []

    def test_listar_com_itens(self):
        cadastrar_peca(PECA_VALIDA)
        cadastrar_peca({**PECA_VALIDA, "nome": "Segunda Peça"})
        assert len(listar_pecas()) == 2

    def test_buscar_por_id_retorna_dict(self):
        peca = cadastrar_peca(PECA_VALIDA)
        buscada = buscar_peca_por_id(peca["id"])
        assert isinstance(buscada, dict)
        assert buscada["id"] == peca["id"]

    def test_buscar_id_inexistente_levanta_erro(self):
        with pytest.raises(ValueError, match="não encontrada"):
            buscar_peca_por_id(99999)


# ═════════════════════════════════════════════════════════════════════════════
# ESTOQUE
# ═════════════════════════════════════════════════════════════════════════════

class TestEstoque:
    def test_listar_estoque_retorna_lista(self):
        assert isinstance(listar_estoque(), list)

    def test_listar_estoque_vazio(self):
        assert listar_estoque() == []

    def test_cadastrar_aparelho_aparece_no_estoque(self):
        cadastrar_aparelho(APARELHO_VALIDO)
        estoque = listar_estoque()
        assert len(estoque) == 1
        assert estoque[0]["categoria"] == "aparelho"

    def test_cadastrar_peca_aparece_no_estoque(self):
        cadastrar_peca(PECA_VALIDA)
        estoque = listar_estoque()
        assert len(estoque) == 1
        assert estoque[0]["categoria"] == "peca"

    def test_estoque_conta_aparelhos_e_pecas(self):
        cadastrar_aparelho(APARELHO_VALIDO)
        cadastrar_aparelho({**APARELHO_VALIDO, "nome": "Segundo Aparelho"})
        cadastrar_peca(PECA_VALIDA)
        estoque = listar_estoque()
        assert len(estoque) == 3

    def test_buscar_estoque_por_id(self):
        ap = cadastrar_aparelho(APARELHO_VALIDO)
        session = SessionLocal()
        try:
            item = session.query(Estoque).filter_by(
                id_aparelho=ap["id"]).first()
            estoque_id = item.id
        finally:
            session.close()

        resultado = buscar_estoque_por_id(estoque_id)
        assert resultado["categoria"] == "aparelho"

    def test_buscar_estoque_id_inexistente(self):
        with pytest.raises(ValueError, match="não encontrado"):
            buscar_estoque_por_id(99999)

    def test_excluir_aparelho_remove_do_estoque(self):
        ap = cadastrar_aparelho(APARELHO_VALIDO)
        excluir_aparelho(ap["id"])
        assert listar_estoque() == []

    def test_excluir_peca_remove_do_estoque(self):
        peca = cadastrar_peca(PECA_VALIDA)
        excluir_peca(peca["id"])
        assert listar_estoque() == []

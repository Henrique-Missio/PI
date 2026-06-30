"""
Testes dos helpers internos do servicos.py:
_texto_obrigatorio, _texto_opcional, _converter_data
"""
import pytest
from datetime import date

# importa diretamente via módulo (são privados mas testáveis)
from app.servicos import _texto_obrigatorio, _texto_opcional, _converter_data


class TestTextoObrigatorio:
    def test_valor_normal_retorna_stripped(self):
        assert _texto_obrigatorio("  João  ", "nome") == "João"

    def test_string_simples(self):
        assert _texto_obrigatorio("teste", "campo") == "teste"

    def test_valor_none_levanta_erro(self):
        with pytest.raises(ValueError, match="nome"):
            _texto_obrigatorio(None, "nome")

    def test_string_vazia_levanta_erro(self):
        with pytest.raises(ValueError, match="campo"):
            _texto_obrigatorio("", "campo")

    def test_apenas_espacos_levanta_erro(self):
        with pytest.raises(ValueError, match="funcao"):
            _texto_obrigatorio("   ", "funcao")

    def test_mensagem_contem_nome_do_campo(self):
        with pytest.raises(ValueError, match="email_pessoal"):
            _texto_obrigatorio("", "email_pessoal")

    def test_numero_como_string(self):
        assert _texto_obrigatorio("42", "numero") == "42"

    def test_inteiro_convertido_para_string(self):
        assert _texto_obrigatorio(123, "campo") == "123"


class TestTextoOpcional:
    def test_valor_normal_retorna_stripped(self):
        assert _texto_opcional("  apto 2  ") == "apto 2"

    def test_none_retorna_none(self):
        assert _texto_opcional(None) is None

    def test_string_vazia_retorna_none(self):
        assert _texto_opcional("") is None

    def test_apenas_espacos_retorna_none(self):
        assert _texto_opcional("   ") is None

    def test_string_com_conteudo(self):
        assert _texto_opcional("bloco B") == "bloco B"

    def test_numero_como_string(self):
        assert _texto_opcional("0") == "0"


class TestConverterData:
    def test_data_valida_retorna_date(self):
        resultado = _converter_data("10-05-2000", "data_nasc")
        assert resultado == date(2000, 5, 10)

    def test_formato_dd_mm_aaaa(self):
        resultado = _converter_data("01-01-1990", "data_nasc")
        assert resultado == date(1990, 1, 1)

    def test_ultimo_dia_do_mes(self):
        resultado = _converter_data("31-12-2023", "data_nasc")
        assert resultado == date(2023, 12, 31)

    def test_valor_none_levanta_erro(self):
        with pytest.raises(ValueError, match="data_nasc"):
            _converter_data(None, "data_nasc")

    def test_string_vazia_levanta_erro(self):
        with pytest.raises(ValueError, match="data_nasc"):
            _converter_data("", "data_nasc")

    def test_formato_errado_barra_levanta_erro(self):
        with pytest.raises(ValueError):
            _converter_data("2000/05/10", "data_nasc")

    def test_formato_iso_levanta_erro(self):
        with pytest.raises(ValueError):
            _converter_data("2000-05-10", "data_nasc")

    def test_data_invalida_levanta_erro(self):
        with pytest.raises(ValueError):
            _converter_data("32-13-2000", "data_nasc")

    def test_mensagem_contem_nome_do_campo(self):
        with pytest.raises(ValueError, match="data_entrada"):
            _converter_data("", "data_entrada")

    def test_retorna_objeto_date(self):
        resultado = _converter_data("15-06-2025", "data")
        assert isinstance(resultado, date)

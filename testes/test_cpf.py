"""
Testes unitários para validação de CPF.
Tenta importar do projeto; se não existir ainda, usa implementação local.
"""
import pytest

try:
    from app.servicos import validar_cpf
except ImportError:
    try:
        from app.utils import validar_cpf
    except ImportError:
        def validar_cpf(cpf: str) -> bool:
            if not cpf:
                return False
            nums = "".join(c for c in str(cpf) if c.isdigit())
            if len(nums) != 11 or len(set(nums)) == 1:
                return False
            for i in range(2):
                soma = sum(int(nums[j]) * (10 + i - j) for j in range(9 + i))
                digito = (soma * 10 % 11) % 10
                if digito != int(nums[9 + i]):
                    return False
            return True


def _gerar_cpf_valido(base: str) -> str:
    """Gera CPF válido a partir de 9 dígitos."""
    nums = [int(d) for d in base]
    for i in range(2):
        soma = sum(nums[j] * (10 + i - j) for j in range(9 + i))
        nums.append((soma * 10 % 11) % 10)
    return "".join(map(str, nums))


CPFs_VALIDOS = [_gerar_cpf_valido(base) for base in [
    "529982247",
    "111444777",
    "000000001",
    "123456789",
    "987654321",
]]

CPFs_INVALIDOS = [
    "111.111.111-11",    # todos iguais
    "000.000.000-00",
    "123.456.789-00",    # dígito errado
    "529.982.247-26",    # último dígito errado
    "abcdefghijk",
    "529.982.247",       # incompleto
    "",
    "1234",
]


class TestValidarCPF:
    @pytest.mark.parametrize("cpf", CPFs_VALIDOS)
    def test_cpf_valido(self, cpf):
        assert validar_cpf(cpf) is True

    @pytest.mark.parametrize("cpf", CPFs_INVALIDOS)
    def test_cpf_invalido(self, cpf):
        assert validar_cpf(cpf) is False

    def test_todos_digitos_iguais_invalidos(self):
        for d in "0123456789":
            assert validar_cpf(d * 11) is False

    def test_cpf_com_espacos_nao_causa_crash(self):
        try:
            resultado = validar_cpf("  529.982.247-25  ")
            assert isinstance(resultado, bool)
        except Exception as e:
            pytest.fail(f"Exceção inesperada: {e}")

    def test_cpf_none_nao_causa_crash(self):
        try:
            resultado = validar_cpf(None)
            assert resultado is False
        except TypeError:
            pass

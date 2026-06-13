"""
Testes de cadastro — criação completa de Pessoa e todos os dados relacionados.
Como o projeto usa SQLAlchemy puro (sem Flask-SQLAlchemy), os testes
operam diretamente na sessão, sem simular requisições HTTP.
"""
import pytest
from datetime import date
from sqlalchemy.exc import IntegrityError

from app.models import Pessoa, Pessoa_fisica, Endereco, Email, Telefone
from testes.conftest import (
    make_pessoa, make_pessoa_fisica, make_endereco, make_email, make_telefone,
    VALID_PESSOA, VALID_CPF, VALID_ENDERECO,
)


class TestCadastroFluxoCompleto:
    """Simula o fluxo de cadastro de ponta a ponta na camada de dados."""

    def test_cadastro_cria_pessoa(self, session):
        p = Pessoa(**VALID_PESSOA)
        session.add(p)
        session.flush()
        assert p.id is not None

    def test_cadastro_cria_pessoa_fisica(self, session):
        p = Pessoa(**VALID_PESSOA)
        session.add(p)
        session.flush()

        pf = Pessoa_fisica(cpf=VALID_CPF, id_pessoa=p.id)
        session.add(pf)
        session.flush()

        assert pf.id is not None
        assert pf.id_pessoa == p.id

    def test_cadastro_cria_endereco(self, session):
        p = Pessoa(**VALID_PESSOA)
        session.add(p)
        session.flush()

        end = Endereco(**VALID_ENDERECO, id_pessoa=p.id)
        session.add(end)
        session.flush()

        assert end.id is not None
        assert end.numero == "456"

    def test_cadastro_cria_email_pessoal(self, session):
        p = Pessoa(**VALID_PESSOA)
        session.add(p)
        session.flush()

        email = Email(email_pessoal="joao@teste.com", id_pessoa=p.id)
        session.add(email)
        session.flush()

        assert email.id is not None

    def test_cadastro_cria_telefone_celular(self, session):
        p = Pessoa(**VALID_PESSOA)
        session.add(p)
        session.flush()

        tel = Telefone(telefone_celular="51988880000", id_pessoa=p.id)
        session.add(tel)
        session.flush()

        assert tel.id is not None

    def test_cadastro_completo_todos_relacionamentos(self, session):
        """Cria Pessoa + PF + Endereço + Email + Telefone de uma vez."""
        p = Pessoa(**VALID_PESSOA)
        session.add(p)
        session.flush()

        pf = Pessoa_fisica(cpf=VALID_CPF, id_pessoa=p.id)
        end = Endereco(**VALID_ENDERECO, id_pessoa=p.id)
        eml = Email(email_pessoal="joao@completo.com", id_pessoa=p.id)
        tel = Telefone(telefone_celular="51988880000", id_pessoa=p.id)

        session.add_all([pf, end, eml, tel])
        session.flush()

        # Verifica relacionamentos via ORM
        session.refresh(p)
        assert p.pessoa_fisica is not None
        assert len(p.enderecos) == 1
        assert len(p.emails) == 1
        assert len(p.telefones) == 1

    def test_tipo_padrao_voluntario(self, session):
        p = Pessoa(**VALID_PESSOA)
        session.add(p)
        session.flush()
        assert p.tipo == "voluntario"


class TestCadastroValidacaoCPF:
    def test_cpf_duplicado_levanta_erro(self, session):
        p1 = make_pessoa(session, nome="Pessoa 1")
        p2 = make_pessoa(session, nome="Pessoa 2")
        make_pessoa_fisica(session, p1, cpf="529.982.247-25")

        session.add(Pessoa_fisica(cpf="529.982.247-25", id_pessoa=p2.id))
        with pytest.raises(IntegrityError):
            session.flush()

    def test_cpfs_diferentes_sao_aceitos(self, session):
        p1 = make_pessoa(session, nome="Pessoa A")
        p2 = make_pessoa(session, nome="Pessoa B")
        pf1 = make_pessoa_fisica(session, p1, cpf="529.982.247-25")
        pf2 = make_pessoa_fisica(session, p2, cpf="111.444.777-35")
        assert pf1.id != pf2.id

    def test_cpf_nao_pode_ser_nulo(self, session):
        p = make_pessoa(session)
        pf = Pessoa_fisica(cpf=None, id_pessoa=p.id)
        session.add(pf)
        with pytest.raises(IntegrityError):
            session.flush()


class TestCadastroValidacaoEndereco:
    def test_numero_nao_pode_ser_nulo(self, session):
        p = make_pessoa(session)
        end = Endereco(
            cep="96810000", rua="Rua X", numero=None,
            bairro="B", cidade="C", estado="RS", id_pessoa=p.id,
        )
        session.add(end)
        with pytest.raises(IntegrityError):
            session.flush()

    def test_cep_nao_pode_ser_nulo(self, session):
        p = make_pessoa(session)
        end = Endereco(
            cep=None, rua="Rua X", numero="1",
            bairro="B", cidade="C", estado="RS", id_pessoa=p.id,
        )
        session.add(end)
        with pytest.raises(IntegrityError):
            session.flush()

    def test_complemento_aceita_nulo(self, session):
        p = make_pessoa(session)
        end = Endereco(
            cep="96810000", rua="Rua X", numero="1",
            bairro="B", cidade="C", estado="RS",
            complemento=None, id_pessoa=p.id,
        )
        session.add(end)
        session.flush()
        assert end.id is not None

    def test_complemento_aceita_string_vazia(self, session):
        p = make_pessoa(session)
        end = Endereco(
            cep="96810000", rua="Rua X", numero="1",
            bairro="B", cidade="C", estado="RS",
            complemento="", id_pessoa=p.id,
        )
        session.add(end)
        session.flush()
        assert end.id is not None


class TestCadastroDeleteCascata:
    def test_delete_pessoa_remove_tudo(self, session):
        p = make_pessoa(session, nome="Delete Completo")
        pf = make_pessoa_fisica(session, p, cpf="852.496.370-10")
        end = make_endereco(session, p)
        eml = make_email(session, p)
        tel = make_telefone(session, p)

        ids = dict(pf=pf.id, end=end.id, eml=eml.id, tel=tel.id)

        session.delete(p)
        session.flush()

        assert session.get(Pessoa_fisica, ids["pf"]) is None
        assert session.get(Endereco,      ids["end"]) is None
        assert session.get(Email,         ids["eml"]) is None
        assert session.get(Telefone,      ids["tel"]) is None

    def test_delete_nao_afeta_outra_pessoa(self, session):
        p1 = make_pessoa(session, nome="Pessoa Deletada")
        p2 = make_pessoa(session, nome="Pessoa Mantida")
        pf2 = make_pessoa_fisica(session, p2, cpf="111.444.777-35")

        session.delete(p1)
        session.flush()

        assert session.get(Pessoa_fisica, pf2.id) is not None

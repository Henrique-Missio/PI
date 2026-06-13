"""
Testes dos modelos: Pessoa, Pessoa_fisica, Endereco, Email, Telefone
"""
import pytest
from sqlalchemy.exc import IntegrityError
from datetime import date

from app.models import Pessoa, Pessoa_fisica, Endereco, Email, Telefone
from testes.conftest import (
    make_pessoa, make_pessoa_fisica, make_endereco, make_email, make_telefone,
    VALID_PESSOA, VALID_CPF, VALID_ENDERECO,
)


class TestPessoaModel:
    def test_criar_pessoa_basica(self, session):
        p = make_pessoa(session)
        assert p.id is not None
        assert p.nome_completo == "Teste"

    def test_campos_obrigatorios_nome(self, session):
        p = Pessoa(tipo="voluntario", funcao="tecnico",
                   senha="abc", data_nasc=date(1990, 1, 1))
        session.add(p)
        with pytest.raises(IntegrityError):
            session.flush()

    def test_campos_obrigatorios_senha(self, session):
        p = Pessoa(nome_completo="Sem Senha", tipo="voluntario",
                   funcao="tecnico", data_nasc=date(1990, 1, 1))
        session.add(p)
        with pytest.raises(IntegrityError):
            session.flush()

    def test_campos_obrigatorios_data_nasc(self, session):
        p = Pessoa(nome_completo="Sem Data", tipo="voluntario",
                   funcao="tecnico", senha="abc")
        session.add(p)
        with pytest.raises(IntegrityError):
            session.flush()

    def test_tipo_admin(self, session):
        p = make_pessoa(session, tipo="admin", funcao="administrador")
        assert p.tipo == "admin"

    def test_tipo_voluntario(self, session):
        p = make_pessoa(session, tipo="voluntario")
        assert p.tipo == "voluntario"

    def test_to_dict_retorna_campos_corretos(self, session):
        p = make_pessoa(session, nome="Dict Teste")
        d = p.to_dict()
        assert "id" in d
        assert "nome_completo" in d
        assert "tipo" in d
        assert "senha" not in d  # senha não deve vazar no to_dict


class TestPessoaFisicaModel:
    def test_criar_pessoa_fisica(self, session):
        p = make_pessoa(session)
        pf = make_pessoa_fisica(session, p, cpf="529.982.247-25")
        assert pf.id is not None
        assert pf.cpf == "529.982.247-25"

    def test_cpf_unico(self, session):
        p1 = make_pessoa(session, nome="P1")
        p2 = make_pessoa(session, nome="P2")
        make_pessoa_fisica(session, p1, cpf="111.444.777-35")
        session.add(Pessoa_fisica(cpf="111.444.777-35", id_pessoa=p2.id))
        with pytest.raises(IntegrityError):
            session.flush()

    def test_delete_pessoa_cascata_pessoa_fisica(self, session):
        p = make_pessoa(session, nome="Cascata PF")
        pf = make_pessoa_fisica(session, p, cpf="852.496.370-10")
        pf_id = pf.id
        session.delete(p)
        session.flush()
        assert session.get(Pessoa_fisica, pf_id) is None

    def test_pessoa_fisica_sem_id_pessoa_falha(self, session):
        pf = Pessoa_fisica(cpf="000.000.001-91")
        session.add(pf)
        with pytest.raises(IntegrityError):
            session.flush()


class TestEnderecoModel:
    def test_criar_endereco_completo(self, session):
        p = make_pessoa(session)
        end = make_endereco(session, p, numero="200")
        assert end.id is not None
        assert end.numero == "200"
        assert end.cidade == "Santa Cruz do Sul"

    def test_complemento_opcional(self, session):
        p = make_pessoa(session)
        end = Endereco(
            cep="96810000", rua="Rua X", numero="1",
            bairro="B", cidade="C", estado="RS",
            id_pessoa=p.id,
        )
        session.add(end)
        session.flush()
        assert end.complemento is None or end.complemento == ""

    def test_numero_obrigatorio(self, session):
        p = make_pessoa(session)
        end = Endereco(
            cep="96810000", rua="Rua X", numero=None,
            bairro="B", cidade="C", estado="RS",
            id_pessoa=p.id,
        )
        session.add(end)
        with pytest.raises(IntegrityError):
            session.flush()

    def test_delete_pessoa_cascata_endereco(self, session):
        p = make_pessoa(session, nome="Cascata End")
        end = make_endereco(session, p)
        end_id = end.id
        session.delete(p)
        session.flush()
        assert session.get(Endereco, end_id) is None

    def test_to_dict_contem_campos_de_endereco(self, session):
        p = make_pessoa(session)
        end = make_endereco(session, p)
        d = end.to_dict()
        for campo in ("cep", "rua", "numero", "bairro", "cidade", "estado"):
            assert campo in d


class TestEmailModel:
    def test_criar_email_pessoal(self, session):
        p = make_pessoa(session)
        email = make_email(session, p, pessoal="joao@teste.com")
        assert email.id is not None
        assert email.email_pessoal == "joao@teste.com"

    def test_criar_email_juridico(self, session):
        p = make_pessoa(session)
        email = Email(email_juridico="empresa@pids.com", id_pessoa=p.id)
        session.add(email)
        session.flush()
        assert email.email_juridico == "empresa@pids.com"

    def test_ambos_emails_podem_ser_nulos(self, session):
        """Email admite pessoal e jurídico nulos (somente id_pessoa obrigatório)"""
        p = make_pessoa(session)
        email = Email(id_pessoa=p.id)
        session.add(email)
        session.flush()
        assert email.id is not None

    def test_delete_pessoa_cascata_email(self, session):
        p = make_pessoa(session, nome="Cascata Email")
        email = make_email(session, p)
        email_id = email.id
        session.delete(p)
        session.flush()
        assert session.get(Email, email_id) is None


class TestTelefoneModel:
    def test_criar_telefone_celular(self, session):
        p = make_pessoa(session)
        tel = make_telefone(session, p, celular="51999990000")
        assert tel.id is not None
        assert tel.telefone_celular == "51999990000"

    def test_criar_telefone_fixo(self, session):
        p = make_pessoa(session)
        tel = Telefone(telefone_fixo="5132221111", id_pessoa=p.id)
        session.add(tel)
        session.flush()
        assert tel.telefone_fixo == "5132221111"

    def test_criar_telefone_corporativo(self, session):
        p = make_pessoa(session)
        tel = Telefone(telefone_corporativo="5133330000", id_pessoa=p.id)
        session.add(tel)
        session.flush()
        assert tel.telefone_corporativo == "5133330000"

    def test_delete_pessoa_cascata_telefone(self, session):
        p = make_pessoa(session, nome="Cascata Tel")
        tel = make_telefone(session, p)
        tel_id = tel.id
        session.delete(p)
        session.flush()
        assert session.get(Telefone, tel_id) is None

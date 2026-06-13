import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import (
    Pessoa, Pessoa_fisica, Endereco, Email, Telefone,
    Aparelhos, Pecas, Estoque,
)
from datetime import date


# ── Engine em memória só para testes ─────────────────────────────────────────
@pytest.fixture(scope="session")
def engine():
    eng = create_engine("sqlite:///:memory:",
                        connect_args={"check_same_thread": False})
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture(scope="session")
def SessionFactory(engine):
    return sessionmaker(bind=engine)


@pytest.fixture
def session(engine, SessionFactory):
    """
    Cada teste recebe uma sessão isolada dentro de uma transação
    que é revertida ao final — sem sujar o banco entre testes.
    """
    connection = engine.connect()
    transaction = connection.begin()
    sess = SessionFactory(bind=connection)

    yield sess

    sess.close()
    transaction.rollback()
    connection.close()


# ── Helpers de criação reutilizáveis ─────────────────────────────────────────
def make_pessoa(session, nome="Teste", tipo="voluntario", funcao="tecnico", senha="senha123"):
    p = Pessoa(
        nome_completo=nome,
        tipo=tipo,
        funcao=funcao,
        senha=senha,
        data_nasc=date(1990, 1, 1),
    )
    session.add(p)
    session.flush()
    return p


def make_pessoa_fisica(session, pessoa, cpf="529.982.247-25"):
    pf = Pessoa_fisica(cpf=cpf, id_pessoa=pessoa.id)
    session.add(pf)
    session.flush()
    return pf


def make_endereco(session, pessoa, numero="100"):
    end = Endereco(
        cep="96810000",
        rua="Rua Sinimbu",
        numero=numero,
        complemento="",
        bairro="Centro",
        cidade="Santa Cruz do Sul",
        estado="RS",
        id_pessoa=pessoa.id,
    )
    session.add(end)
    session.flush()
    return end


def make_email(session, pessoa, pessoal="teste@pids.com"):
    email = Email(email_pessoal=pessoal, id_pessoa=pessoa.id)
    session.add(email)
    session.flush()
    return email


def make_telefone(session, pessoa, celular="51999990000"):
    tel = Telefone(telefone_celular=celular, id_pessoa=pessoa.id)
    session.add(tel)
    session.flush()
    return tel


# ── Fixtures prontas para uso nos testes ─────────────────────────────────────
@pytest.fixture
def pessoa_admin(session):
    return make_pessoa(session, nome="Admin Teste", tipo="admin", funcao="administrador", senha="admin123")


@pytest.fixture
def pessoa_voluntario(session):
    p = make_pessoa(session, nome="Voluntário Teste",
                    tipo="voluntario", funcao="tecnico", senha="senha123")
    make_pessoa_fisica(session, p, cpf="529.982.247-25")
    make_email(session, p, pessoal="voluntario@teste.com")
    make_endereco(session, p)
    make_telefone(session, p)
    return p


# ── Payload de cadastro válido ────────────────────────────────────────────────
VALID_PESSOA = dict(
    nome_completo="João da Silva",
    tipo="voluntario",
    funcao="tecnico",
    senha="senha123",
    data_nasc=date(2000, 5, 10),
)

VALID_CPF = "111.444.777-35"

VALID_ENDERECO = dict(
    cep="96810000",
    rua="Rua das Flores",
    numero="456",
    complemento="",
    bairro="Centro",
    cidade="Santa Cruz do Sul",
    estado="RS",
)

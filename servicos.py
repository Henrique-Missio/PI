"""
Regras de negócio e acesso ao banco (sessão + consultas).
Nas rotas só chamamos estas funções e devolvemos JSON — fica mais fácil de explicar.
"""

from sqlalchemy import select

from database import SessionLocal
from models import Aluno, Professor, Turma


def listar_professores():
    session = SessionLocal()
    try:
        linhas = session.scalars(select(Professor).order_by(Professor.nome)).all()
        return [p.to_dict() for p in linhas]
    finally:
        session.close()


def listar_turmas():
    session = SessionLocal()
    try:
        linhas = session.scalars(select(Turma).order_by(Turma.codigo)).all()
        return [t.to_dict() for t in linhas]
    finally:
        session.close()


def listar_alunos():
    session = SessionLocal()
    try:
        linhas = session.scalars(select(Aluno).order_by(Aluno.nome)).all()
        return [a.to_dict() for a in linhas]
    finally:
        session.close()


def _texto_obrigatorio(valor, campo):
    if valor is None or str(valor).strip() == "":
        raise ValueError(f"O campo '{campo}' é obrigatório.")
    return str(valor).strip()


def _texto_opcional(valor):
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto or None


def cadastrar_professor(dados):
    nome = _texto_obrigatorio(dados.get("nome"), "nome")
    email = _texto_opcional(dados.get("email"))

    session = SessionLocal()
    try:
        professor = Professor(nome=nome, email=email)
        session.add(professor)
        session.commit()
        session.refresh(professor)
        return professor.to_dict()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def cadastrar_turma(dados):
    nome = _texto_obrigatorio(dados.get("nome"), "nome")
    codigo = _texto_obrigatorio(dados.get("codigo"), "codigo")
    professor_id = dados.get("professor_id")
    if not professor_id:
        raise ValueError("O campo 'professor_id' é obrigatório.")

    session = SessionLocal()
    try:
        professor = session.get(Professor, int(professor_id))
        if professor is None:
            raise ValueError(f"Professor {professor_id} não encontrado.")

        turma = Turma(nome=nome, codigo=codigo, professor_id=professor.id)
        session.add(turma)
        session.commit()
        session.refresh(turma)
        return turma.to_dict()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def cadastrar_aluno(dados):
    nome = _texto_obrigatorio(dados.get("nome"), "nome")
    email = _texto_opcional(dados.get("email"))
    turma_id = dados.get("turma_id")
    if not turma_id:
        raise ValueError("O campo 'turma_id' é obrigatório.")

    session = SessionLocal()
    try:
        turma = session.get(Turma, int(turma_id))
        if turma is None:
            raise ValueError(f"Turma {turma_id} não encontrada.")

        aluno = Aluno(nome=nome, email=email, turma_id=turma.id)
        session.add(aluno)
        session.commit()
        session.refresh(aluno)
        return aluno.to_dict()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

import flask as fk
from sqlalchemy.exc import IntegrityError

from servicos import (
    cadastrar_aluno,
    cadastrar_professor,
    cadastrar_turma,
    listar_alunos,
    listar_professores,
    listar_turmas,
)

bp = fk.Blueprint("api", __name__, url_prefix="/api")


def _erro(mensagem, status=400):
    return fk.jsonify({"erro": mensagem}), status


@bp.get("/professores")
def professores():
    return fk.jsonify(listar_professores())


@bp.post("/professores")
def criar_professor():
    dados = fk.request.get_json(silent=True) or {}
    try:
        return fk.jsonify(cadastrar_professor(dados)), 201
    except ValueError as exc:
        return _erro(str(exc))
    except IntegrityError:
        return _erro("Já existe um professor com este e-mail.", 409)


@bp.get("/turmas")
def turmas():
    return fk.jsonify(listar_turmas())


@bp.post("/turmas")
def criar_turma():
    dados = fk.request.get_json(silent=True) or {}
    try:
        return fk.jsonify(cadastrar_turma(dados)), 201
    except ValueError as exc:
        return _erro(str(exc))
    except IntegrityError:
        return _erro("Já existe uma turma com este código.", 409)


@bp.get("/alunos")
def alunos():
    return fk.jsonify(listar_alunos())


@bp.post("/alunos")
def criar_aluno():
    dados = fk.request.get_json(silent=True) or {}
    try:
        return fk.jsonify(cadastrar_aluno(dados)), 201
    except ValueError as exc:
        return _erro(str(exc))
    except IntegrityError:
        return _erro("Já existe um aluno com este e-mail.", 409)


paginas = fk.Blueprint("paginas", __name__)


@paginas.get("/")
def home():
    return fk.render_template("index.html")

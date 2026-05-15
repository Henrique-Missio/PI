import flask as fk
from sqlalchemy.exc import IntegrityError
from app.servicos import (
    listar_aparelhos, buscar_aparelho_por_id, cadastrar_aparelho, editar_aparelho, excluir_aparelho,
    listar_pecas,     buscar_peca_por_id,     cadastrar_peca,     editar_peca,     excluir_peca,
    listar_estoque,   buscar_estoque_por_id,
)

bp = fk.Blueprint("api", __name__, url_prefix="/api")

def _erro(mensagem, status=400):
    return fk.jsonify({"erro": mensagem}), status


# ── APARELHOS ──
@bp.get("/aparelhos")
def get_aparelhos():
    return fk.jsonify(listar_aparelhos())

@bp.get("/aparelhos/<int:aparelho_id>")
def get_aparelho(aparelho_id):
    try:
        return fk.jsonify(buscar_aparelho_por_id(aparelho_id))
    except ValueError as exc:
        return _erro(str(exc), 404)

@bp.post("/aparelhos")
def post_aparelho():
    dados = fk.request.get_json(silent=True) or {}
    try:
        return fk.jsonify(cadastrar_aparelho(dados)), 201
    except ValueError as exc:
        return _erro(str(exc))
    except IntegrityError:
        return _erro("Erro de integridade ao cadastrar aparelho.", 409)

@bp.put("/aparelhos/<int:aparelho_id>")
def put_aparelho(aparelho_id):
    dados = fk.request.get_json(silent=True) or {}
    try:
        return fk.jsonify(editar_aparelho(aparelho_id, dados))
    except ValueError as exc:
        return _erro(str(exc), 404)

@bp.delete("/aparelhos/<int:aparelho_id>")
def delete_aparelho(aparelho_id):
    try:
        return fk.jsonify(excluir_aparelho(aparelho_id))
    except ValueError as exc:
        return _erro(str(exc), 404)


# ── PEÇAS ──
@bp.get("/pecas")
def get_pecas():
    return fk.jsonify(listar_pecas())

@bp.get("/pecas/<int:peca_id>")
def get_peca(peca_id):
    try:
        return fk.jsonify(buscar_peca_por_id(peca_id))
    except ValueError as exc:
        return _erro(str(exc), 404)

@bp.post("/pecas")
def post_peca():
    dados = fk.request.get_json(silent=True) or {}
    try:
        return fk.jsonify(cadastrar_peca(dados)), 201
    except ValueError as exc:
        return _erro(str(exc))
    except IntegrityError:
        return _erro("Erro de integridade ao cadastrar peça.", 409)

@bp.put("/pecas/<int:peca_id>")
def put_peca(peca_id):
    dados = fk.request.get_json(silent=True) or {}
    try:
        return fk.jsonify(editar_peca(peca_id, dados))
    except ValueError as exc:
        return _erro(str(exc), 404)

@bp.delete("/pecas/<int:peca_id>")
def delete_peca(peca_id):
    try:
        return fk.jsonify(excluir_peca(peca_id))
    except ValueError as exc:
        return _erro(str(exc), 404)


# ── ESTOQUE — somente leitura ──
@bp.get("/estoque")
def get_estoque():
    return fk.jsonify(listar_estoque())

@bp.get("/estoque/<int:estoque_id>")
def get_estoque_por_id(estoque_id):
    try:
        return fk.jsonify(buscar_estoque_por_id(estoque_id))
    except ValueError as exc:
        return _erro(str(exc), 404)


# ── PÁGINAS ──
paginas = fk.Blueprint("paginas", __name__)

@paginas.get("/")
def home():
    return fk.render_template("index.html")
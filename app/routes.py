import flask as fk
from sqlalchemy.exc import IntegrityError
from app.servicos import (
    login, cadastrar_usuario, listar_usuarios, excluir_usuario,
    buscar_perfil, editar_perfil,
    listar_aparelhos, buscar_aparelho_por_id, cadastrar_aparelho, editar_aparelho, excluir_aparelho,
    listar_pecas,     buscar_peca_por_id,     cadastrar_peca,     editar_peca,     excluir_peca,
    listar_estoque,   buscar_estoque_por_id,
)

bp = fk.Blueprint("api",     __name__, url_prefix="/api")
paginas = fk.Blueprint("paginas", __name__)


def _erro(mensagem, status=400):
    return fk.jsonify({"erro": mensagem}), status


def _usuario_logado():
    return fk.session.get("usuario")


def _requer_login():
    if not _usuario_logado():
        return _erro("Não autorizado. Faça login.", 401)


def _requer_admin():
    usuario = _usuario_logado()
    if not usuario:
        return _erro("Não autorizado. Faça login.", 401)
    if usuario.get("tipo") != "administrador":
        return _erro("Acesso negado. Apenas administradores.", 403)


# ── AUTENTICAÇÃO ──
@bp.post("/login")
def rota_login():
    dados = fk.request.get_json(silent=True) or {}
    try:
        usuario = login(dados)
        fk.session["usuario"] = usuario
        return fk.jsonify(usuario), 200
    except ValueError as exc:
        return _erro(str(exc), 401)


@bp.post("/logout")
def rota_logout():
    fk.session.pop("usuario", None)
    return fk.jsonify({"mensagem": "Logout realizado com sucesso."})


@bp.get("/me")
def rota_me():
    usuario = _usuario_logado()
    if not usuario:
        return _erro("Não autorizado.", 401)
    return fk.jsonify(usuario)


# ── USUÁRIOS ──
@bp.post("/cadastro")
def rota_cadastro():
    dados = fk.request.get_json(silent=True) or {}
    # verifica se já existe algum usuário — se não, permite cadastro livre do primeiro admin
    from app.servicos import listar_usuarios
    usuarios = listar_usuarios()
    tipo = "administrador" if not usuarios else "voluntario"
    try:
        return fk.jsonify(cadastrar_usuario(dados, tipo=tipo)), 201
    except ValueError as exc:
        return _erro(str(exc))
    except IntegrityError:
        return _erro("Dados duplicados.", 409)


@bp.post("/usuarios")
def rota_criar_usuario():
    erro = _requer_admin()
    if erro:
        return erro
    dados = fk.request.get_json(silent=True) or {}
    tipo = dados.pop("tipo", "voluntario")
    try:
        return fk.jsonify(cadastrar_usuario(dados, tipo=tipo)), 201
    except ValueError as exc:
        return _erro(str(exc))
    except IntegrityError:
        return _erro("Dados duplicados.", 409)


@bp.get("/usuarios")
def rota_listar_usuarios():
    erro = _requer_admin()
    if erro:
        return erro
    return fk.jsonify(listar_usuarios())


@bp.delete("/usuarios/<int:pessoa_id>")
def rota_excluir_usuario(pessoa_id):
    erro = _requer_admin()
    if erro:
        return erro
    try:
        usuarios = listar_usuarios()
        alvo = next((u for u in usuarios if u["id"] == pessoa_id), None)
        if alvo is None:
            return _erro(f"Usuário com id {pessoa_id} não encontrado.", 404)
        if alvo["tipo"] == "administrador":
            return _erro("Não é possível excluir outro administrador por aqui.", 403)
        return fk.jsonify(excluir_usuario(pessoa_id))
    except ValueError as exc:
        return _erro(str(exc), 404)

# ── PERFIL (próprio usuário) ──


@bp.get("/perfil")
def rota_ver_perfil():
    usuario = _usuario_logado()
    if not usuario:
        return _erro("Não autorizado. Faça login.", 401)
    try:
        return fk.jsonify(buscar_perfil(usuario["id"]))
    except ValueError as exc:
        return _erro(str(exc), 404)


@bp.put("/perfil")
def rota_editar_perfil():
    usuario = _usuario_logado()
    if not usuario:
        return _erro("Não autorizado. Faça login.", 401)
    dados = fk.request.get_json(silent=True) or {}
    try:
        atualizado = editar_perfil(usuario["id"], dados)
        fk.session["usuario"]["nome_completo"] = atualizado["nome_completo"]
        fk.session.modified = True
        return fk.jsonify(atualizado)
    except ValueError as exc:
        return _erro(str(exc))
    except IntegrityError:
        return _erro("Dados duplicados.", 409)


@bp.delete("/perfil")
def rota_excluir_propria_conta():
    usuario = _usuario_logado()
    if not usuario:
        return _erro("Não autorizado. Faça login.", 401)
    try:
        resultado = excluir_usuario(usuario["id"])
        fk.session.pop("usuario", None)
        return fk.jsonify(resultado)
    except ValueError as exc:
        return _erro(str(exc), 404)


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
    erro = _requer_login()
    if erro:
        return erro
    dados = fk.request.get_json(silent=True) or {}
    try:
        return fk.jsonify(cadastrar_aparelho(dados)), 201
    except ValueError as exc:
        return _erro(str(exc))
    except IntegrityError:
        return _erro("Erro de integridade ao cadastrar aparelho.", 409)


@bp.put("/aparelhos/<int:aparelho_id>")
def put_aparelho(aparelho_id):
    erro = _requer_login()
    if erro:
        return erro
    dados = fk.request.get_json(silent=True) or {}
    try:
        return fk.jsonify(editar_aparelho(aparelho_id, dados))
    except ValueError as exc:
        return _erro(str(exc), 404)


@bp.delete("/aparelhos/<int:aparelho_id>")
def delete_aparelho(aparelho_id):
    erro = _requer_admin()
    if erro:
        return erro
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
    erro = _requer_login()
    if erro:
        return erro
    dados = fk.request.get_json(silent=True) or {}
    try:
        return fk.jsonify(cadastrar_peca(dados)), 201
    except ValueError as exc:
        return _erro(str(exc))
    except IntegrityError:
        return _erro("Erro de integridade ao cadastrar peça.", 409)


@bp.put("/pecas/<int:peca_id>")
def put_peca(peca_id):
    erro = _requer_login()
    if erro:
        return erro
    dados = fk.request.get_json(silent=True) or {}
    try:
        return fk.jsonify(editar_peca(peca_id, dados))
    except ValueError as exc:
        return _erro(str(exc), 404)


@bp.delete("/pecas/<int:peca_id>")
def delete_peca(peca_id):
    erro = _requer_admin()
    if erro:
        return erro
    try:
        return fk.jsonify(excluir_peca(peca_id))
    except ValueError as exc:
        return _erro(str(exc), 404)


# ── ESTOQUE ──
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
@paginas.get("/")
def home():
    return fk.render_template("index.html")


@paginas.get("/login")
def pagina_login():
    if _usuario_logado():
        return fk.redirect("/")
    return fk.render_template("login.html")


@paginas.get("/cadastro")
def pagina_cadastro():
    return fk.render_template("cadastro.html")


@paginas.get("/perfil")
def pagina_perfil():
    if not _usuario_logado():
        return fk.redirect("/login")
    return fk.render_template("perfil.html")

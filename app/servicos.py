from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import select
from app.database import SessionLocal
from app.models import Pecas, Estoque, Aparelhos, Pessoa, Pessoa_fisica, Endereco, Email, Telefone


def _texto_obrigatorio(valor, campo):
    if valor is None or str(valor).strip() == "":
        raise ValueError(f"O campo '{campo}' é obrigatório.")
    return str(valor).strip()


def _texto_opcional(valor):
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto or None


def _converter_data(valor, campo):
    """Converte string 'DD-MM-AAAA' para date."""
    if valor is None or str(valor).strip() == "":
        raise ValueError(f"O campo '{campo}' é obrigatório.")
    try:
        return date(*(int(x) for x in reversed(str(valor).strip().split("-"))))
    except ValueError:
        raise ValueError(f"O campo '{campo}' deve estar no formato DD-MM-AAAA.")


# ──────────────────────────────────────────
# AUTENTICAÇÃO
# ──────────────────────────────────────────

def login(dados):
    email = _texto_obrigatorio(dados.get("email"), "email")
    senha = _texto_obrigatorio(dados.get("senha"), "senha")

    session = SessionLocal()
    try:
        # busca o email na tabela Email
        email_obj = session.scalars(
            select(Email).where(Email.email_pessoal == email)
        ).first()

        if email_obj is None:
            raise ValueError("E-mail ou senha incorretos.")

        pessoa = session.get(Pessoa, email_obj.id_pessoa)

        if pessoa is None or not check_password_hash(pessoa.senha, senha):
            raise ValueError("E-mail ou senha incorretos.")

        return {
            "id":            pessoa.id,
            "nome_completo": pessoa.nome_completo,
            "tipo":          pessoa.tipo,
            "funcao":        pessoa.funcao,
        }
    finally:
        session.close()


def cadastrar_usuario(dados, tipo="voluntario"):
    nome_completo    = _texto_obrigatorio(dados.get("nome_completo"),    "nome_completo")
    cpf              = _texto_obrigatorio(dados.get("cpf"),              "cpf")
    funcao           = _texto_obrigatorio(dados.get("funcao"),           "funcao")
    email_pessoal    = _texto_obrigatorio(dados.get("email_pessoal"),    "email_pessoal")
    telefone_celular = _texto_obrigatorio(dados.get("telefone_celular"), "telefone_celular")
    cep              = _texto_obrigatorio(dados.get("cep"),              "cep")
    rua              = _texto_obrigatorio(dados.get("rua"),              "rua")
    bairro           = _texto_obrigatorio(dados.get("bairro"),           "bairro")
    cidade           = _texto_obrigatorio(dados.get("cidade"),           "cidade")
    estado           = _texto_obrigatorio(dados.get("estado"),           "estado")
    senha            = _texto_obrigatorio(dados.get("senha"),            "senha")
    data_nasc        = _converter_data(dados.get("data_nasc"),           "data_nasc")

    # validações
    if not cpf.isdigit() or len(cpf) != 11:
        raise ValueError("CPF inválido. Use apenas 11 números.")
    if not telefone_celular.isdigit() or len(telefone_celular) not in [10, 11]:
        raise ValueError("Telefone inválido. Use apenas números com DDD.")
    if not cep.isdigit() or len(cep) != 8:
        raise ValueError("CEP inválido. Use apenas 8 números.")
    if len(senha) < 6:
        raise ValueError("A senha deve ter pelo menos 6 caracteres.")
    if tipo not in ["administrador", "voluntario"]:
        raise ValueError("Tipo inválido.")

    session = SessionLocal()
    try:
        # verifica se email já existe
        email_existente = session.scalars(
            select(Email).where(Email.email_pessoal == email_pessoal)
        ).first()
        if email_existente:
            raise ValueError("Este e-mail já está cadastrado.")

        # verifica se CPF já existe
        cpf_existente = session.scalars(
            select(Pessoa_fisica).where(Pessoa_fisica.cpf == cpf)
        ).first()
        if cpf_existente:
            raise ValueError("Este CPF já está cadastrado.")

        # cria pessoa
        pessoa = Pessoa(
            tipo=tipo,
            nome_completo=nome_completo,
            senha=generate_password_hash(senha),
            funcao=funcao,
            data_nasc=data_nasc,
        )
        session.add(pessoa)
        session.flush()

        # cria registros relacionados
        session.add(Pessoa_fisica(cpf=cpf, id_pessoa=pessoa.id))
        session.add(Email(email_pessoal=email_pessoal, id_pessoa=pessoa.id))
        session.add(Telefone(telefone_celular=telefone_celular, id_pessoa=pessoa.id))
        session.add(Endereco(
            cep=cep, rua=rua, bairro=bairro,
            cidade=cidade, estado=estado,
            id_pessoa=pessoa.id
        ))

        session.commit()
        session.refresh(pessoa)
        return pessoa.to_dict()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def listar_usuarios():
    session = SessionLocal()
    try:
        linhas = session.scalars(select(Pessoa).order_by(Pessoa.id)).all()
        return [p.to_dict() for p in linhas]
    finally:
        session.close()


def excluir_usuario(pessoa_id):
    session = SessionLocal()
    try:
        pessoa = session.get(Pessoa, pessoa_id)
        if pessoa is None:
            raise ValueError(f"Usuário com id {pessoa_id} não encontrado.")
        session.delete(pessoa)
        session.commit()
        return {"mensagem": f"Usuário {pessoa_id} excluído com sucesso."}
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ──────────────────────────────────────────
# APARELHOS
# ──────────────────────────────────────────

def listar_aparelhos():
    session = SessionLocal()
    try:
        linhas = session.scalars(select(Aparelhos).order_by(Aparelhos.id)).all()
        return [a.to_dict() for a in linhas]
    finally:
        session.close()


def buscar_aparelho_por_id(aparelho_id):
    session = SessionLocal()
    try:
        aparelho = session.get(Aparelhos, aparelho_id)
        if aparelho is None:
            raise ValueError(f"Aparelho com id {aparelho_id} não encontrado.")
        return aparelho.to_dict()
    finally:
        session.close()


def cadastrar_aparelho(dados):
    nome         = _texto_obrigatorio(dados.get("nome"),        "nome")
    marca        = _texto_obrigatorio(dados.get("marca"),       "marca")
    informacoes  = _texto_obrigatorio(dados.get("informacoes"), "informacoes")
    problema     = _texto_obrigatorio(dados.get("problema"),    "problema")
    status       = _texto_obrigatorio(dados.get("status"),      "status")
    data_entrada = _converter_data(dados["data_entrada"], "data_entrada") if dados.get("data_entrada") else date.today()
    data_saida   = _converter_data(dados["data_saida"],   "data_saida")   if dados.get("data_saida")   else None

    session = SessionLocal()
    try:
        aparelho = Aparelhos(
            nome=nome, marca=marca, informacoes=informacoes,
            problema=problema, status=status,
            data_entrada=data_entrada, data_saida=data_saida
        )
        session.add(aparelho)
        session.flush()

        estoque = Estoque(categoria="aparelho", id_aparelho=aparelho.id)
        session.add(estoque)

        session.commit()
        session.refresh(aparelho)
        return aparelho.to_dict()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def editar_aparelho(aparelho_id, dados):
    session = SessionLocal()
    try:
        aparelho = session.get(Aparelhos, aparelho_id)
        if aparelho is None:
            raise ValueError(f"Aparelho com id {aparelho_id} não encontrado.")

        if "nome"        in dados: aparelho.nome        = _texto_obrigatorio(dados["nome"],        "nome")
        if "marca"       in dados: aparelho.marca       = _texto_obrigatorio(dados["marca"],       "marca")
        if "informacoes" in dados: aparelho.informacoes = _texto_obrigatorio(dados["informacoes"], "informacoes")
        if "problema"    in dados: aparelho.problema    = _texto_obrigatorio(dados["problema"],    "problema")
        if "status"      in dados: aparelho.status      = _texto_obrigatorio(dados["status"],      "status")
        if "data_entrada"in dados: aparelho.data_entrada= _converter_data(dados["data_entrada"],   "data_entrada")
        if "data_saida"  in dados: aparelho.data_saida  = _converter_data(dados["data_saida"],     "data_saida") if dados["data_saida"] else None

        session.commit()
        session.refresh(aparelho)
        return aparelho.to_dict()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def excluir_aparelho(aparelho_id):
    session = SessionLocal()
    try:
        aparelho = session.get(Aparelhos, aparelho_id)
        if aparelho is None:
            raise ValueError(f"Aparelho com id {aparelho_id} não encontrado.")
        session.delete(aparelho)
        session.commit()
        return {"mensagem": f"Aparelho {aparelho_id} excluído com sucesso."}
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ──────────────────────────────────────────
# PEÇAS
# ──────────────────────────────────────────

def listar_pecas():
    session = SessionLocal()
    try:
        linhas = session.scalars(select(Pecas).order_by(Pecas.id)).all()
        return [p.to_dict() for p in linhas]
    finally:
        session.close()


def buscar_peca_por_id(peca_id):
    session = SessionLocal()
    try:
        peca = session.get(Pecas, peca_id)
        if peca is None:
            raise ValueError(f"Peça com id {peca_id} não encontrada.")
        return peca.to_dict()
    finally:
        session.close()


def cadastrar_peca(dados):
    nome         = _texto_obrigatorio(dados.get("nome"),        "nome")
    marca        = _texto_obrigatorio(dados.get("marca"),       "marca")
    informacoes  = _texto_obrigatorio(dados.get("informacoes"), "informacoes")
    problema     = _texto_opcional(dados.get("problema"))
    status       = _texto_obrigatorio(dados.get("status"),      "status")
    data_entrada = _converter_data(dados["data_entrada"], "data_entrada") if dados.get("data_entrada") else date.today()
    data_saida   = _converter_data(dados["data_saida"],   "data_saida")   if dados.get("data_saida")   else None

    session = SessionLocal()
    try:
        peca = Pecas(
            nome=nome, marca=marca, informacoes=informacoes,
            problema=problema, status=status,
            data_entrada=data_entrada, data_saida=data_saida
        )
        session.add(peca)
        session.flush()

        estoque = Estoque(categoria="peca", id_pecas=peca.id)
        session.add(estoque)

        session.commit()
        session.refresh(peca)
        return peca.to_dict()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def editar_peca(peca_id, dados):
    session = SessionLocal()
    try:
        peca = session.get(Pecas, peca_id)
        if peca is None:
            raise ValueError(f"Peça com id {peca_id} não encontrada.")

        if "nome"        in dados: peca.nome        = _texto_obrigatorio(dados["nome"],        "nome")
        if "marca"       in dados: peca.marca       = _texto_obrigatorio(dados["marca"],       "marca")
        if "informacoes" in dados: peca.informacoes = _texto_obrigatorio(dados["informacoes"], "informacoes")
        if "problema"    in dados: peca.problema    = _texto_opcional(dados["problema"])
        if "status"      in dados: peca.status      = _texto_obrigatorio(dados["status"],      "status")
        if "data_entrada"in dados: peca.data_entrada= _converter_data(dados["data_entrada"],   "data_entrada")
        if "data_saida"  in dados: peca.data_saida  = _converter_data(dados["data_saida"],     "data_saida") if dados["data_saida"] else None

        session.commit()
        session.refresh(peca)
        return peca.to_dict()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def excluir_peca(peca_id):
    session = SessionLocal()
    try:
        peca = session.get(Pecas, peca_id)
        if peca is None:
            raise ValueError(f"Peça com id {peca_id} não encontrada.")
        session.delete(peca)
        session.commit()
        return {"mensagem": f"Peça {peca_id} excluída com sucesso."}
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ──────────────────────────────────────────
# ESTOQUE — somente leitura
# ──────────────────────────────────────────

def listar_estoque():
    session = SessionLocal()
    try:
        linhas = session.scalars(select(Estoque).order_by(Estoque.id)).all()
        return [e.to_dict() for e in linhas]
    finally:
        session.close()


def buscar_estoque_por_id(estoque_id):
    session = SessionLocal()
    try:
        estoque = session.get(Estoque, estoque_id)
        if estoque is None:
            raise ValueError(f"Item de estoque com id {estoque_id} não encontrado.")
        return estoque.to_dict()
    finally:
        session.close()
        
# ──────────────────────────────────────────
# PESSOA
# ──────────────────────────────────────────

# def listar_pessoas():
#     session = SessionLocal()
#     try:
#         linhas = session.scalars(select(Pessoa).order_by(Pessoa.id)).all()
#         return [p.to_dict() for p in linhas]
#     finally:
#         session.close()


# def buscar_pessoa_por_id(pessoa_id):
#     session = SessionLocal()
#     try:
#         pessoa = session.get(Pessoa, pessoa_id)
#         if pessoa is None:
#             raise ValueError(f"Pessoa com id {pessoa_id} não encontrada.")
#         return pessoa.to_dict()
#     finally:
#         session.close()


# def cadastrar_pessoa(dados):
#     nome_completo = _texto_obrigatorio(dados.get("nome_completo"), "nome_completo")
#     tipo          = _texto_obrigatorio(dados.get("tipo"),          "tipo")
#     funcao        = _texto_obrigatorio(dados.get("funcao"),        "funcao")
#     senha         = _texto_obrigatorio(dados.get("senha"),         "senha")
#     data_nasc     = _converter_data(dados.get("data_nasc"),        "data_nasc")

#     # tipo só pode ser administrador, voluntário ou usuário
#     tipos_validos = ["administrador", "voluntario", "usuario"]
#     if tipo.lower() not in tipos_validos:
#         raise ValueError(f"Tipo inválido. Use: {', '.join(tipos_validos)}")

#     # hash da senha antes de salvar — nunca salvar senha pura
#     from werkzeug.security import generate_password_hash
#     senha_hash = generate_password_hash(senha)

#     session = SessionLocal()
#     try:
#         pessoa = Pessoa(
#             nome_completo=nome_completo,
#             tipo=tipo.lower(),
#             funcao=funcao,
#             senha=senha_hash,
#             data_nasc=data_nasc
#         )
#         session.add(pessoa)
#         session.commit()
#         session.refresh(pessoa)
#         return pessoa.to_dict()
#     except Exception:
#         session.rollback()
#         raise
#     finally:
#         session.close()


# def editar_pessoa(pessoa_id, dados):
#     session = SessionLocal()
#     try:
#         pessoa = session.get(Pessoa, pessoa_id)
#         if pessoa is None:
#             raise ValueError(f"Pessoa com id {pessoa_id} não encontrada.")

#         if "nome_completo" in dados: pessoa.nome_completo = _texto_obrigatorio(dados["nome_completo"], "nome_completo")
#         if "tipo"          in dados: pessoa.tipo          = _texto_obrigatorio(dados["tipo"],          "tipo")
#         if "funcao"        in dados: pessoa.funcao        = _texto_obrigatorio(dados["funcao"],        "funcao")
#         if "data_nasc"     in dados: pessoa.data_nasc     = _converter_data(dados["data_nasc"],        "data_nasc")
#         if "senha"         in dados:
#             from werkzeug.security import generate_password_hash
#             pessoa.senha = generate_password_hash(_texto_obrigatorio(dados["senha"], "senha"))

#         session.commit()
#         session.refresh(pessoa)
#         return pessoa.to_dict()
#     except Exception:
#         session.rollback()
#         raise
#     finally:
#         session.close()


# def excluir_pessoa(pessoa_id):
#     session = SessionLocal()
#     try:
#         pessoa = session.get(Pessoa, pessoa_id)
#         if pessoa is None:
#             raise ValueError(f"Pessoa com id {pessoa_id} não encontrada.")
#         session.delete(pessoa)
#         session.commit()
#         return {"mensagem": f"Pessoa {pessoa_id} excluída com sucesso."}
#     except Exception:
#         session.rollback()
#         raise
#     finally:
#         session.close()


# ──────────────────────────────────────────
# PESSOA FÍSICA
# ──────────────────────────────────────────

# def cadastrar_pessoa_fisica(dados):
#     id_pessoa = dados.get("id_pessoa")
#     cpf       = _texto_obrigatorio(dados.get("cpf"), "cpf")

#     if not id_pessoa:
#         raise ValueError("O campo 'id_pessoa' é obrigatório.")

#     # valida formato do CPF (só números, 11 dígitos)
#     if not cpf.isdigit() or len(cpf) != 11:
#         raise ValueError("CPF inválido. Informe apenas os 11 números sem pontos ou traços.")

#     session = SessionLocal()
#     try:
#         if session.get(Pessoa, int(id_pessoa)) is None:
#             raise ValueError(f"Pessoa com id {id_pessoa} não encontrada.")

#         pessoa_fisica = Pessoa_fisica(
#             cpf=cpf,
#             id_pessoa=int(id_pessoa)
#         )
#         session.add(pessoa_fisica)
#         session.commit()
#         session.refresh(pessoa_fisica)
#         return pessoa_fisica.to_dict()
#     except Exception:
#         session.rollback()
#         raise
#     finally:
#         session.close()


# def excluir_pessoa_fisica(pessoa_fisica_id):
#     session = SessionLocal()
#     try:
#         pessoa_fisica = session.get(Pessoa_fisica, pessoa_fisica_id)
#         if pessoa_fisica is None:
#             raise ValueError(f"Pessoa física com id {pessoa_fisica_id} não encontrada.")
#         session.delete(pessoa_fisica)
#         session.commit()
#         return {"mensagem": f"Pessoa física {pessoa_fisica_id} excluída com sucesso."}
#     except Exception:
#         session.rollback()
#         raise
#     finally:
#         session.close()


# ──────────────────────────────────────────
# PESSOA JURÍDICA
# ──────────────────────────────────────────

# def cadastrar_pessoa_juridica(dados):
#     id_pessoa         = dados.get("id_pessoa")
#     cnpj              = _texto_obrigatorio(dados.get("cnpj"),              "cnpj")
#     nome_fantasia     = _texto_obrigatorio(dados.get("nome_fantasia"),     "nome_fantasia")
#     razao_social      = _texto_obrigatorio(dados.get("razao_social"),      "razao_social")
#     inscricao_estadual= _texto_obrigatorio(dados.get("inscricao_estadual"),"inscricao_estadual")

#     if not id_pessoa:
#         raise ValueError("O campo 'id_pessoa' é obrigatório.")

#     # valida formato do CNPJ (só números, 14 dígitos)
#     if not cnpj.isdigit() or len(cnpj) != 14:
#         raise ValueError("CNPJ inválido. Informe apenas os 14 números sem pontos, traços ou barras.")

#     session = SessionLocal()
#     try:
#         if session.get(Pessoa, int(id_pessoa)) is None:
#             raise ValueError(f"Pessoa com id {id_pessoa} não encontrada.")

#         pessoa_juridica = Pessoa_juridica(
#             cnpj=cnpj,
#             nome_fantasia=nome_fantasia,
#             razao_social=razao_social,
#             inscricao_estadual=inscricao_estadual,
#             id_pessoa=int(id_pessoa)
#         )
#         session.add(pessoa_juridica)
#         session.commit()
#         session.refresh(pessoa_juridica)
#         return pessoa_juridica.to_dict()
#     except Exception:
#         session.rollback()
#         raise
#     finally:
#         session.close()


# def excluir_pessoa_juridica(pessoa_juridica_id):
#     session = SessionLocal()
#     try:
#         pessoa_juridica = session.get(Pessoa_juridica, pessoa_juridica_id)
#         if pessoa_juridica is None:
#             raise ValueError(f"Pessoa jurídica com id {pessoa_juridica_id} não encontrada.")
#         session.delete(pessoa_juridica)
#         session.commit()
#         return {"mensagem": f"Pessoa jurídica {pessoa_juridica_id} excluída com sucesso."}
#     except Exception:
#         session.rollback()
#         raise
#     finally:
#         session.close()


# ──────────────────────────────────────────
# ENDEREÇO
# ──────────────────────────────────────────

# def cadastrar_endereco(dados):
#     id_pessoa = dados.get("id_pessoa")
#     cep       = _texto_obrigatorio(dados.get("cep"),    "cep")
#     rua       = _texto_obrigatorio(dados.get("rua"),    "rua")
#     bairro    = _texto_obrigatorio(dados.get("bairro"), "bairro")
#     cidade    = _texto_obrigatorio(dados.get("cidade"), "cidade")
#     estado    = _texto_obrigatorio(dados.get("estado"), "estado")

#     if not id_pessoa:
#         raise ValueError("O campo 'id_pessoa' é obrigatório.")

#     if not cep.isdigit() or len(cep) != 8:
#         raise ValueError("CEP inválido. Informe apenas os 8 números sem traço.")

#     session = SessionLocal()
#     try:
#         if session.get(Pessoa, int(id_pessoa)) is None:
#             raise ValueError(f"Pessoa com id {id_pessoa} não encontrada.")

#         endereco = Endereco(
#             cep=cep, rua=rua, bairro=bairro,
#             cidade=cidade, estado=estado,
#             id_pessoa=int(id_pessoa)
#         )
#         session.add(endereco)
#         session.commit()
#         session.refresh(endereco)
#         return endereco.to_dict()
#     except Exception:
#         session.rollback()
#         raise
#     finally:
#         session.close()


# def editar_endereco(endereco_id, dados):
#     session = SessionLocal()
#     try:
#         endereco = session.get(Endereco, endereco_id)
#         if endereco is None:
#             raise ValueError(f"Endereço com id {endereco_id} não encontrado.")

#         if "cep"    in dados: endereco.cep    = _texto_obrigatorio(dados["cep"],    "cep")
#         if "rua"    in dados: endereco.rua    = _texto_obrigatorio(dados["rua"],    "rua")
#         if "bairro" in dados: endereco.bairro = _texto_obrigatorio(dados["bairro"], "bairro")
#         if "cidade" in dados: endereco.cidade = _texto_obrigatorio(dados["cidade"], "cidade")
#         if "estado" in dados: endereco.estado = _texto_obrigatorio(dados["estado"], "estado")

#         session.commit()
#         session.refresh(endereco)
#         return endereco.to_dict()
#     except Exception:
#         session.rollback()
#         raise
#     finally:
#         session.close()


# def excluir_endereco(endereco_id):
#     session = SessionLocal()
#     try:
#         endereco = session.get(Endereco, endereco_id)
#         if endereco is None:
#             raise ValueError(f"Endereço com id {endereco_id} não encontrado.")
#         session.delete(endereco)
#         session.commit()
#         return {"mensagem": f"Endereço {endereco_id} excluído com sucesso."}
#     except Exception:
#         session.rollback()
#         raise
#     finally:
#         session.close()


# ──────────────────────────────────────────
# EMAIL
# ──────────────────────────────────────────

# def cadastrar_email(dados):
#     id_pessoa      = dados.get("id_pessoa")
#     email_pessoal  = _texto_opcional(dados.get("email_pessoal"))
#     email_juridico = _texto_opcional(dados.get("email_juridico"))

#     if not id_pessoa:
#         raise ValueError("O campo 'id_pessoa' é obrigatório.")

#     # pelo menos um email tem que ser informado
#     if not email_pessoal and not email_juridico:
#         raise ValueError("Informe pelo menos um email (pessoal ou jurídico).")

#     session = SessionLocal()
#     try:
#         if session.get(Pessoa, int(id_pessoa)) is None:
#             raise ValueError(f"Pessoa com id {id_pessoa} não encontrada.")

#         email = Email(
#             email_pessoal=email_pessoal,
#             email_juridico=email_juridico,
#             id_pessoa=int(id_pessoa)
#         )
#         session.add(email)
#         session.commit()
#         session.refresh(email)
#         return email.to_dict()
#     except Exception:
#         session.rollback()
#         raise
#     finally:
#         session.close()


# def editar_email(email_id, dados):
#     session = SessionLocal()
#     try:
#         email = session.get(Email, email_id)
#         if email is None:
#             raise ValueError(f"Email com id {email_id} não encontrado.")

#         if "email_pessoal"  in dados: email.email_pessoal  = _texto_opcional(dados["email_pessoal"])
#         if "email_juridico" in dados: email.email_juridico = _texto_opcional(dados["email_juridico"])

#         session.commit()
#         session.refresh(email)
#         return email.to_dict()
#     except Exception:
#         session.rollback()
#         raise
#     finally:
#         session.close()


# def excluir_email(email_id):
#     session = SessionLocal()
#     try:
#         email = session.get(Email, email_id)
#         if email is None:
#             raise ValueError(f"Email com id {email_id} não encontrado.")
#         session.delete(email)
#         session.commit()
#         return {"mensagem": f"Email {email_id} excluído com sucesso."}
#     except Exception:
#         session.rollback()
#         raise
#     finally:
#         session.close()


# ──────────────────────────────────────────
# TELEFONE
# ──────────────────────────────────────────

# def cadastrar_telefone(dados):
#     id_pessoa           = dados.get("id_pessoa")
#     telefone_celular    = _texto_opcional(dados.get("telefone_celular"))
#     telefone_corporativo= _texto_opcional(dados.get("telefone_corporativo"))
#     telefone_fixo       = _texto_opcional(dados.get("telefone_fixo"))

#     if not id_pessoa:
#         raise ValueError("O campo 'id_pessoa' é obrigatório.")

#     # pelo menos um telefone tem que ser informado
#     if not telefone_celular and not telefone_corporativo and not telefone_fixo:
#         raise ValueError("Informe pelo menos um telefone.")

#     # valida que os informados têm só números e 11 dígitos (celular) ou 10 (fixo)
#     for campo, valor in [("telefone_celular", telefone_celular),
#                          ("telefone_corporativo", telefone_corporativo),
#                          ("telefone_fixo", telefone_fixo)]:
#         if valor and (not valor.isdigit() or len(valor) not in [10, 11]):
#             raise ValueError(f"{campo} inválido. Informe apenas números com DDD (10 ou 11 dígitos).")

#     session = SessionLocal()
#     try:
#         if session.get(Pessoa, int(id_pessoa)) is None:
#             raise ValueError(f"Pessoa com id {id_pessoa} não encontrada.")

#         telefone = Telefone(
#             telefone_celular=telefone_celular,
#             telefone_corporativo=telefone_corporativo,
#             telefone_fixo=telefone_fixo,
#             id_pessoa=int(id_pessoa)
#         )
#         session.add(telefone)
#         session.commit()
#         session.refresh(telefone)
#         return telefone.to_dict()
#     except Exception:
#         session.rollback()
#         raise
#     finally:
#         session.close()


# def editar_telefone(telefone_id, dados):
#     session = SessionLocal()
#     try:
#         telefone = session.get(Telefone, telefone_id)
#         if telefone is None:
#             raise ValueError(f"Telefone com id {telefone_id} não encontrado.")

#         if "telefone_celular"     in dados: telefone.telefone_celular     = _texto_opcional(dados["telefone_celular"])
#         if "telefone_corporativo" in dados: telefone.telefone_corporativo = _texto_opcional(dados["telefone_corporativo"])
#         if "telefone_fixo"        in dados: telefone.telefone_fixo        = _texto_opcional(dados["telefone_fixo"])

#         session.commit()
#         session.refresh(telefone)
#         return telefone.to_dict()
#     except Exception:
#         session.rollback()
#         raise
#     finally:
#         session.close()


# def excluir_telefone(telefone_id):
#     session = SessionLocal()
#     try:
#         telefone = session.get(Telefone, telefone_id)
#         if telefone is None:
#             raise ValueError(f"Telefone com id {telefone_id} não encontrado.")
#         session.delete(telefone)
#         session.commit()
#         return {"mensagem": f"Telefone {telefone_id} excluído com sucesso."}
#     except Exception:
#         session.rollback()
#         raise
#     finally:
#         session.close()
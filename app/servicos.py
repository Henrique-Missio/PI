from datetime import date, datetime, timedelta
import random
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import select, func
from app.database import SessionLocal
from app.models import Pecas, Estoque, Aparelhos, Pessoa, Pessoa_fisica, Endereco, Email, Telefone, CodigoRecuperacao
from app.email_utils import enviar_codigo_recuperacao


def _texto_obrigatorio(valor, campo, max_len=None):
    if valor is None or str(valor).strip() == "":
        raise ValueError(f"O campo '{campo}' é obrigatório.")
    texto = str(valor).strip()
    if max_len and len(texto) > max_len:
        raise ValueError(f"O campo '{campo}' deve ter no máximo {max_len} caracteres.")
    return texto


def _texto_opcional(valor, max_len=None):
    if valor is None:
        return None
    texto = str(valor).strip()
    if not texto:
        return None
    if max_len and len(texto) > max_len:
        raise ValueError(f"O campo excede o limite de {max_len} caracteres.")
    return texto


def _converter_data(valor, campo):
    """Converte string 'DD-MM-AAAA' para date."""
    if valor is None or str(valor).strip() == "":
        raise ValueError(f"O campo '{campo}' é obrigatório.")
    try:
        return date(*(int(x) for x in reversed(str(valor).strip().split("-"))))
    except ValueError:
        raise ValueError(f"O campo '{campo}' deve estar no formato DD-MM-AAAA.")


def _validar_datas_estoque(data_entrada, data_saida):
    """Regras de negócio para datas de itens do estoque (aparelhos e peças):
    - a data de entrada não pode ser no futuro.
    - a data de saída não pode ser anterior à data de entrada.
    """
    if data_entrada and data_entrada > date.today():
        raise ValueError("A data de entrada não pode ser uma data futura.")
    if data_saida and data_entrada and data_saida < data_entrada:
        raise ValueError("A data de saída não pode ser anterior à data de entrada.")


def validar_data_nascimento(data_nasc) -> bool:
    """Retorna False se a data for no futuro ou implicar idade impossível (>120 anos)."""
    if data_nasc > date.today():
        return False
    idade = (date.today() - data_nasc).days / 365.25
    if idade > 120:
        return False
    return True


def validar_senha_forte(senha: str) -> bool:
    """8+ chars, 1 maiuscula, 1 numero, 1 especial."""
    if not senha or len(senha) < 8:
        return False
    if not any(c.isupper() for c in senha):
        return False
    if not any(c.isdigit() for c in senha):
        return False
    if not any(not c.isalnum() for c in senha):
        return False
    return True


def validar_cpf(cpf: str) -> bool:
    """Valida CPF pelo algoritmo oficial de dígitos verificadores.
    Aceita string com ou sem máscara; retorna False para None/valores inválidos.
    """
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
    nome_completo        = _texto_obrigatorio(dados.get("nome_completo"),        "nome_completo", max_len=60)
    cpf                  = _texto_obrigatorio(dados.get("cpf"),                  "cpf")
    funcao               = _texto_obrigatorio(dados.get("funcao"),               "funcao", max_len=20)
    email_pessoal        = _texto_obrigatorio(dados.get("email_pessoal"),        "email_pessoal", max_len=40)
    telefone_celular     = _texto_obrigatorio(dados.get("telefone_celular"),     "telefone_celular")
    cep                  = _texto_obrigatorio(dados.get("cep"),                  "cep")
    rua                  = _texto_obrigatorio(dados.get("rua"),                  "rua", max_len=60)
    numero               = _texto_obrigatorio(dados.get("numero"),               "numero", max_len=10)
    bairro                = _texto_obrigatorio(dados.get("bairro"),               "bairro", max_len=30)
    cidade               = _texto_obrigatorio(dados.get("cidade"),               "cidade", max_len=30)
    estado               = _texto_obrigatorio(dados.get("estado"),               "estado", max_len=30)
    senha                = _texto_obrigatorio(dados.get("senha"),                "senha")
    data_nasc            = _converter_data(dados.get("data_nasc"),               "data_nasc")

    # campos opcionais
    complemento          = _texto_opcional(dados.get("complemento"), max_len=60)
    email_juridico       = _texto_opcional(dados.get("email_juridico"), max_len=40)
    telefone_corporativo = _texto_opcional(dados.get("telefone_corporativo"))
    telefone_fixo        = _texto_opcional(dados.get("telefone_fixo"))

    if not validar_cpf(cpf):
        raise ValueError("CPF inválido.")
    cpf = "".join(c for c in cpf if c.isdigit())
    if not telefone_celular.isdigit() or len(telefone_celular) not in [10, 11]:
        raise ValueError("Telefone inválido. Use apenas números com DDD.")
    if not cep.isdigit() or len(cep) != 8:
        raise ValueError("CEP inválido. Use apenas 8 números.")
    if not validar_senha_forte(senha):
        raise ValueError("Senha fraca. Use 8+ caracteres, maiúscula, número e caractere especial.")
    if not validar_data_nascimento(data_nasc):
        raise ValueError("Data de nascimento inválida.")
    if tipo not in ["administrador", "voluntario"]:
        raise ValueError("Tipo inválido.")

    session = SessionLocal()
    try:
        email_existente = session.scalars(
            select(Email).where(Email.email_pessoal == email_pessoal)
        ).first()
        if email_existente:
            raise ValueError("Este e-mail já está cadastrado.")

        cpf_existente = session.scalars(
            select(Pessoa_fisica).where(Pessoa_fisica.cpf == cpf)
        ).first()
        if cpf_existente:
            raise ValueError("Este CPF já está cadastrado.")

        pessoa = Pessoa(
            tipo=tipo,
            nome_completo=nome_completo,
            senha=generate_password_hash(senha),
            funcao=funcao,
            data_nasc=data_nasc,
        )
        session.add(pessoa)
        session.flush()

        session.add(Pessoa_fisica(cpf=cpf, id_pessoa=pessoa.id))
        session.add(Email(
            email_pessoal=email_pessoal,
            email_juridico=email_juridico,
            id_pessoa=pessoa.id
        ))
        session.add(Telefone(
            telefone_celular=telefone_celular,
            telefone_corporativo=telefone_corporativo,
            telefone_fixo=telefone_fixo,
            id_pessoa=pessoa.id
        ))
        session.add(Endereco(
            cep=cep, rua=rua, numero=numero,
            complemento=complemento, bairro=bairro,
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
    nome         = _texto_obrigatorio(dados.get("nome"),        "nome", max_len=120)
    marca        = _texto_obrigatorio(dados.get("marca"),       "marca", max_len=40)
    informacoes  = _texto_obrigatorio(dados.get("informacoes"), "informacoes", max_len=1500)
    problema     = _texto_obrigatorio(dados.get("problema"),    "problema", max_len=500)
    status       = _texto_obrigatorio(dados.get("status"),      "status", max_len=30)
    data_entrada = _converter_data(dados["data_entrada"], "data_entrada") if dados.get("data_entrada") else date.today()
    data_saida   = _converter_data(dados["data_saida"],   "data_saida")   if dados.get("data_saida")   else None

    _validar_datas_estoque(data_entrada, data_saida)

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

        if "nome"        in dados: aparelho.nome        = _texto_obrigatorio(dados["nome"],        "nome", max_len=120)
        if "marca"       in dados: aparelho.marca       = _texto_obrigatorio(dados["marca"],       "marca", max_len=40)
        if "informacoes" in dados: aparelho.informacoes = _texto_obrigatorio(dados["informacoes"], "informacoes", max_len=1500)
        if "problema"    in dados: aparelho.problema    = _texto_obrigatorio(dados["problema"],    "problema", max_len=500)
        if "status" in dados:
            aparelho.status = _texto_obrigatorio(
                dados["status"],      "status", max_len=30)
        if aparelho.status == "Doado" and "data_saida" not in dados:
            aparelho.data_saida = date.today()
        if "data_entrada" in dados:
            aparelho.data_entrada = _converter_data(
                dados["data_entrada"],   "data_entrada")
        if "data_saida" in dados:
            aparelho.data_saida = _converter_data(
                dados["data_saida"],     "data_saida") if dados["data_saida"] else None

        _validar_datas_estoque(aparelho.data_entrada, aparelho.data_saida)

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
    nome         = _texto_obrigatorio(dados.get("nome"),        "nome", max_len=120)
    marca        = _texto_obrigatorio(dados.get("marca"),       "marca", max_len=40)
    informacoes  = _texto_obrigatorio(dados.get("informacoes"), "informacoes", max_len=1500)
    problema     = _texto_opcional(dados.get("problema"), max_len=500)
    status       = _texto_obrigatorio(dados.get("status"),      "status", max_len=30)
    data_entrada = _converter_data(dados["data_entrada"], "data_entrada") if dados.get("data_entrada") else date.today()
    data_saida   = _converter_data(dados["data_saida"],   "data_saida")   if dados.get("data_saida")   else None

    _validar_datas_estoque(data_entrada, data_saida)

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

        if "nome"        in dados: peca.nome        = _texto_obrigatorio(dados["nome"],        "nome", max_len=120)
        if "marca"       in dados: peca.marca       = _texto_obrigatorio(dados["marca"],       "marca", max_len=40)
        if "informacoes" in dados: peca.informacoes = _texto_obrigatorio(dados["informacoes"], "informacoes", max_len=1500)
        if "problema"    in dados: peca.problema    = _texto_opcional(dados["problema"], max_len=500)
        if "status" in dados:
            peca.status = _texto_obrigatorio(
                dados["status"],      "status", max_len=30)
        if peca.status == "Doado" and "data_saida" not in dados:
            peca.data_saida = date.today()
        if "data_entrada" in dados:
            peca.data_entrada = _converter_data(
                dados["data_entrada"],   "data_entrada")
        if "data_saida" in dados:
            peca.data_saida = _converter_data(
                dados["data_saida"],     "data_saida") if dados["data_saida"] else None

        _validar_datas_estoque(peca.data_entrada, peca.data_saida)

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
# PERFIL — somente leitura
# ──────────────────────────────────────────
        
def buscar_perfil(pessoa_id):
    session = SessionLocal()
    try:
        pessoa = session.get(Pessoa, pessoa_id)
        if pessoa is None:
            raise ValueError(f"Usuário com id {pessoa_id} não encontrado.")

        dados = pessoa.to_dict()

        pessoa_fisica = session.scalars(
            select(Pessoa_fisica).where(Pessoa_fisica.id_pessoa == pessoa_id)
        ).first()
        dados["cpf"] = pessoa_fisica.cpf if pessoa_fisica else None

        email = session.scalars(
            select(Email).where(Email.id_pessoa == pessoa_id)
        ).first()
        dados["email_pessoal"]  = email.email_pessoal  if email else None
        dados["email_juridico"] = email.email_juridico if email else None

        telefone = session.scalars(
            select(Telefone).where(Telefone.id_pessoa == pessoa_id)
        ).first()
        dados["telefone_celular"]     = telefone.telefone_celular     if telefone else None
        dados["telefone_corporativo"] = telefone.telefone_corporativo if telefone else None
        dados["telefone_fixo"]        = telefone.telefone_fixo        if telefone else None

        endereco = session.scalars(
            select(Endereco).where(Endereco.id_pessoa == pessoa_id)
        ).first()
        if endereco:
            dados["cep"]         = endereco.cep
            dados["rua"]         = endereco.rua
            dados["numero"]      = endereco.numero
            dados["complemento"] = endereco.complemento
            dados["bairro"]      = endereco.bairro
            dados["cidade"]      = endereco.cidade
            dados["estado"]      = endereco.estado

        return dados
    finally:
        session.close()


def editar_perfil(pessoa_id, dados):
    session = SessionLocal()
    try:
        pessoa = session.get(Pessoa, pessoa_id)
        if pessoa is None:
            raise ValueError(f"Usuário com id {pessoa_id} não encontrado.")

        if "nome_completo" in dados:
            pessoa.nome_completo = _texto_obrigatorio(dados["nome_completo"], "nome_completo", max_len=60)
        if "funcao" in dados:
            pessoa.funcao = _texto_obrigatorio(dados["funcao"], "funcao", max_len=20)
        if "data_nasc" in dados:
            pessoa.data_nasc = _converter_data(dados["data_nasc"], "data_nasc")
        if dados.get("senha"):
            if not validar_senha_forte(dados["senha"]):
                raise ValueError("Senha fraca. Use 8+ caracteres, maiúscula, número e caractere especial.")
            pessoa.senha = generate_password_hash(dados["senha"])

        # CPF
        if "cpf" in dados:
            cpf = _texto_obrigatorio(dados["cpf"], "cpf")
            if not validar_cpf(cpf):
                raise ValueError("CPF inválido.")
            cpf = "".join(c for c in cpf if c.isdigit())
            cpf_existente = session.scalars(
                select(Pessoa_fisica).where(
                    Pessoa_fisica.cpf == cpf, Pessoa_fisica.id_pessoa != pessoa_id
                )
            ).first()
            if cpf_existente:
                raise ValueError("Este CPF já está cadastrado em outra conta.")

            pessoa_fisica = session.scalars(
                select(Pessoa_fisica).where(Pessoa_fisica.id_pessoa == pessoa_id)
            ).first()
            if pessoa_fisica:
                pessoa_fisica.cpf = cpf
            else:
                session.add(Pessoa_fisica(cpf=cpf, id_pessoa=pessoa_id))

        # Email
        if "email_pessoal" in dados:
            if dados["email_pessoal"]:
                email_existente = session.scalars(
                    select(Email).where(
                        Email.email_pessoal == dados["email_pessoal"],
                        Email.id_pessoa != pessoa_id
                    )
                ).first()
                if email_existente:
                    raise ValueError("Este e-mail já está em uso por outra conta.")

            email = session.scalars(
                select(Email).where(Email.id_pessoa == pessoa_id)
            ).first()
            if email:
                email.email_pessoal = _texto_opcional(dados.get("email_pessoal"), max_len=40)
            else:
                session.add(Email(email_pessoal=_texto_opcional(dados.get("email_pessoal"), max_len=40), id_pessoa=pessoa_id))

        # Telefone
        if "telefone_celular" in dados:
            telefone = session.scalars(
                select(Telefone).where(Telefone.id_pessoa == pessoa_id)
            ).first()
            if telefone:
                telefone.telefone_celular = _texto_opcional(dados.get("telefone_celular"))
            else:
                session.add(Telefone(telefone_celular=_texto_opcional(dados.get("telefone_celular")), id_pessoa=pessoa_id))

        # Endereço
        campos_endereco = ["cep", "rua", "numero", "complemento", "bairro", "cidade", "estado"]
        if any(c in dados for c in campos_endereco):
            endereco = session.scalars(
                select(Endereco).where(Endereco.id_pessoa == pessoa_id)
            ).first()
            if endereco:
                if "cep"         in dados: endereco.cep         = _texto_obrigatorio(dados["cep"], "cep")
                if "rua"         in dados: endereco.rua         = _texto_obrigatorio(dados["rua"], "rua", max_len=60)
                if "numero"      in dados: endereco.numero      = _texto_obrigatorio(dados["numero"], "numero", max_len=10)
                if "complemento" in dados: endereco.complemento = _texto_opcional(dados.get("complemento"), max_len=60)
                if "bairro"      in dados: endereco.bairro      = _texto_obrigatorio(dados["bairro"], "bairro", max_len=30)
                if "cidade"      in dados: endereco.cidade      = _texto_obrigatorio(dados["cidade"], "cidade", max_len=30)
                if "estado"      in dados: endereco.estado      = _texto_obrigatorio(dados["estado"], "estado", max_len=30)

        session.commit()
        session.refresh(pessoa)
        return pessoa.to_dict()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ──────────────────────────────────────────
# RECUPERAÇÃO DE SENHA
# ──────────────────────────────────────────

def solicitar_recuperacao_senha(email: str):
    """Gera codigo 6-digitos, salva com expiracao 15min, envia email.
    Nunca bloqueia/revela se email existe — sempre retorna sucesso generico,
    so gera codigo de verdade se a conta existir."""
    email = _texto_obrigatorio(email, "email")
    email_normalizado = email.strip().lower()

    session = SessionLocal()
    try:
        email_obj = session.scalars(
            select(Email).where(func.lower(Email.email_pessoal) == email_normalizado)
        ).first()

        print(f"[DEBUG recuperar-senha] buscado='{email_normalizado}' | encontrado={bool(email_obj)}", flush=True)

        if email_obj:
            codigo = f"{random.randint(0, 999999):06d}"
            registro = CodigoRecuperacao(
                id_pessoa=email_obj.id_pessoa,
                codigo=codigo,
                expira_em=datetime.utcnow() + timedelta(minutes=15),
                usado=False,
            )
            session.add(registro)
            session.commit()
            enviar_codigo_recuperacao(email_obj.email_pessoal, codigo)

        return {"mensagem": "O código de verificação foi enviado para o seu e-mail."}
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _buscar_codigo_valido(session, email, codigo):
    email_obj = session.scalars(
        select(Email).where(func.lower(Email.email_pessoal) == email.strip().lower())
    ).first()
    if not email_obj:
        return None

    registro = session.scalars(
        select(CodigoRecuperacao)
        .where(
            CodigoRecuperacao.id_pessoa == email_obj.id_pessoa,
            CodigoRecuperacao.codigo == codigo,
            CodigoRecuperacao.usado == False,
        )
        .order_by(CodigoRecuperacao.id.desc())
    ).first()

    if not registro:
        return None
    if registro.expira_em < datetime.utcnow():
        return None
    return registro


def verificar_codigo_recuperacao(email: str, codigo: str) -> bool:
    email  = _texto_obrigatorio(email, "email")
    codigo = _texto_obrigatorio(codigo, "codigo")

    session = SessionLocal()
    try:
        return _buscar_codigo_valido(session, email, codigo) is not None
    finally:
        session.close()


def redefinir_senha_com_codigo(email: str, codigo: str, nova_senha: str):
    """Valida codigo de novo (nao confia em chamada anterior), troca senha, marca codigo usado."""
    email  = _texto_obrigatorio(email, "email")
    codigo = _texto_obrigatorio(codigo, "codigo")
    nova_senha = _texto_obrigatorio(nova_senha, "nova_senha")

    if not validar_senha_forte(nova_senha):
        raise ValueError("Senha fraca. Use 8+ caracteres, maiúscula, número e caractere especial.")

    session = SessionLocal()
    try:
        registro = _buscar_codigo_valido(session, email, codigo)
        if not registro:
            raise ValueError("Código inválido ou expirado.")

        pessoa = session.get(Pessoa, registro.id_pessoa)
        if not pessoa:
            raise ValueError("Usuário não encontrado.")

        pessoa.senha = generate_password_hash(nova_senha)
        registro.usado = True
        session.commit()
        return {"mensagem": "Senha redefinida com sucesso."}
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

from sqlalchemy import Column, ForeignKey, Integer, String, Text, Date, func
from sqlalchemy.orm import relationship
from app.database import Base

class Pecas(Base):
    __tablename__ = "pecas"

    id          = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    nome        = Column(String(120), nullable=False)
    marca       = Column(String(40), nullable=False)
    informacoes = Column(Text(1500), nullable=False)
    problema    = Column(Text(500), nullable=True)
    status      = Column(String(30), nullable=False)
    quantidade  = Column(Integer, nullable=False)                              # adicionado
    data_entrada= Column(Date, nullable=False, default=func.current_date())
    data_saida  = Column(Date, nullable=True)                                  # adicionado

    estoque = relationship("Estoque", back_populates="pecas")

    def to_dict(self):
        return {
            "id":          self.id,
            "nome":        self.nome,
            "marca":       self.marca,
            "informacoes": self.informacoes,
            "problema":    self.problema,
            "status":      self.status,
            "quantidade":  self.quantidade,
            "data_entrada":str(self.data_entrada),
            "data_saida":  str(self.data_saida) if self.data_saida else None,
        }

    def __repr__(self):
        return f"<Peca {self.id} {self.nome!r}>"


class Aparelhos(Base):
    __tablename__ = "aparelhos"

    id          = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    nome        = Column(String(120), nullable=False)
    marca       = Column(String(40), nullable=False)
    informacoes = Column(Text(1500), nullable=False)
    problema    = Column(Text(500), nullable=False)
    status      = Column(String(30), nullable=False)
    quantidade  = Column(Integer, nullable=False)                              # adicionado
    data_entrada= Column(Date, nullable=False, default=func.current_date())
    data_saida  = Column(Date, nullable=True)                                  # adicionado

    estoque = relationship("Estoque", back_populates="aparelhos")

    def to_dict(self):
        return {
            "id":          self.id,
            "nome":        self.nome,
            "marca":       self.marca,
            "informacoes": self.informacoes,
            "problema":    self.problema,
            "status":      self.status,
            "quantidade":  self.quantidade,
            "data_entrada":str(self.data_entrada),
            "data_saida":  str(self.data_saida) if self.data_saida else None,
        }

    def __repr__(self):
        return f"<Aparelho {self.id} {self.nome!r}>"


class Estoque(Base):
    __tablename__ = "estoque"

    id          = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    categoria   = Column(String(15), nullable=False)  # "aparelho" ou "peca"
    id_aparelho = Column(Integer, ForeignKey("aparelhos.id"), nullable=True)
    id_pecas    = Column(Integer, ForeignKey("pecas.id"), nullable=True)

    aparelhos = relationship("Aparelhos", back_populates="estoque")
    pecas     = relationship("Pecas", back_populates="estoque")

    def to_dict(self):
        # puxa os dados do aparelho ou peça relacionado
        if self.aparelhos:
            dados_item = self.aparelhos.to_dict()
        elif self.pecas:
            dados_item = self.pecas.to_dict()
        else:
            dados_item = {}

        return {
            "id":          self.id,
            "categoria":   self.categoria,
            "id_aparelho": self.id_aparelho,
            "id_pecas":    self.id_pecas,
            **dados_item   # espalha todos os campos do aparelho/peça
        }

    def __repr__(self):
        return f"<Estoque {self.id} {self.categoria}>"

# class Pessoa_fisica(Base):
#     __tablename__="pessoa_fisica"

#     id=Column(Integer,primary_key=True,autoincrement=True)
#     cpf=Column(String(11),unique=True,nullable=False)

    # id_pessoa = Column(Integer, ForeignKey("pessoa.id"), nullable=False)
    # pessoa = relationship("Pessoa", back_populates="pessoa_fisica")

    # def to_dict(self):
    #     return {"id": self.id, "cpf": self.cpf, "id_pessoa": self.id_pessoa}

    # def __repr__(self):
    #     return f"<Pessoa física {self.id} {self.cpf}>"

# class Pessoa_juridica(Base):
#     __tablename__="pessoa_juridica"

#     id=Column(Integer,primary_key=True,autoincrement=True)
#     cnpj=Column(String(18),unique=True,nullable=False)
#     nome_fantasia=Column(String(60),nullable=False)
#     inscricao_estadual=Column(String(20),nullable=False)
#     razao_social=Column(String(80),nullable=False)

    # id_pessoa = Column(Integer, ForeignKey("pessoa.id"), nullable=False)
    # pessoa = relationship("Pessoa", back_populates="pessoa_juridica")

    # def to_dict(self):
    #         return {
    #             "id": self.id,
    #             "cnpj": self.cnpj,
    #             "nome_fantasia": self.nome_fantasia,
    #             "inscricao_estadual": self.inscricao_estadual,
    #             "razao_social": self.razao_social,
    #             "id_pessoa": self.id_pessoa
    #         }

    #     def __repr__(self):
    #         return f"<Pessoa jurídica {self.id} {self.nome_fantasia} {self.cnpj}>"

# class Endereco(Base):
#     __tablename__="endereco"

#     id=Column(Integer,primary_key=True,autoincrement=True)
#     cep=Column(String(8),nullable=False)
#     rua=Column(String(30),nullable=False)
#     bairro=Column(String(30),nullable=False)
#     cidade=Column(String(30),nullable=False)
#     estado=Column(String(30),nullable=False)

    # id_pessoa = Column(Integer, ForeignKey("pessoa.id"), nullable=False)
    # pessoa = relationship("Pessoa", back_populates="enderecos")

    # def to_dict(self):
    #     return {
    #         "id": self.id,
    #         "cep": self.cep,
    #         "rua": self.rua,
    #         "bairro": self.bairro,
    #         "cidade": self.cidade,
    #         "estado": self.estado,
    #         "id_pessoa": self.id_pessoa
    #     }

    # def __repr__(self):
    #     return f"<Endereço {self.id} {self.cep}>"

# class Email(Base):
#     __tablename__="email"

#     id=Column(Integer,primary_key=True,autoincrement=True)
#     email_pessoal=Column(String(40),nullable=True)
#     email_juridico=Column(String(40),nullable=True)

#     id_pessoa = Column(Integer, ForeignKey("pessoa.id"), nullable=False)
#     pessoa = relationship("Pessoa", back_populates="emails")

#     def to_dict(self):
#         return {
#             "id": self.id,
#             "email_pessoal": self.email_pessoal,
#             "email_juridico": self.email_juridico,
#             "id_pessoa": self.id_pessoa
#         }

#     def __repr__(self):
#         return f"<Email {self.id}>"

# class Telefone(Base):
#     __tablename__="telefone"

#     id=Column(Integer,primary_key=True,autoincrement=True)
#     telefone_celular=Column(String(11),unique=True,nullable=True)
#     telefone_corporativo=Column(String(11),nullable=True)
#     telefone_fixo=Column(String(11),nullable=True)

    # id_pessoa = Column(Integer, ForeignKey("pessoa.id"), nullable=False)
    # pessoa = relationship("Pessoa", back_populates="telefones")

    # def to_dict(self):
    #     return {
    #         "id": self.id,
    #         "telefone_celular": self.telefone_celular,
    #         "telefone_corporativo": self.telefone_corporativo,
    #         "telefone_fixo": self.telefone_fixo,
    #         "id_pessoa": self.id_pessoa
    #     }

    # def __repr__(self):
    #     return f"<Telefone {self.id}>"

# class Pessoa(Base):
#     __tablename__="pessoa"

#     id=Column(Integer,primary_key=True,autoincrement=True)
#     tipo=Column(String(15),nullable=False)
#     nome_completo=Column(String(60),nullable=False)
#     senha=Column(String(255),nullable=False)
#     funcao=Column(String(20),nullable=False)
#     data_nasc=Column(Date,nullable=False)

    # pessoa_fisica = relationship("Pessoa_fisica", back_populates="pessoa", uselist=False)
    # pessoa_juridica = relationship("Pessoa_juridica", back_populates="pessoa", uselist=False)
    # enderecos = relationship("Endereco", back_populates="pessoa")
    # emails = relationship("Email", back_populates="pessoa")
    # telefones = relationship("Telefone", back_populates="pessoa")

    # def to_dict(self):
    #     return {
    #         "id": self.id,
    #         "tipo": self.tipo,
    #         "nome_completo": self.nome_completo,
    #         "funcao": self.funcao,
    #         "data_nasc": str(self.data_nasc)
    #     }

    # def __repr__(self):
    #     return f"<Pessoa {self.id} {self.nome_completo!r} {self.tipo}>"

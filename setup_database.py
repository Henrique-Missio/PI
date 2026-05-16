"""
Script didático: DDL (create/drop tables) + DML (inserts) com sessão explícita.
Execute na raiz do projeto: python setup_database.py
"""
from sqlalchemy import select
from app.database import Base, SessionLocal, engine
from app import models
from datetime import date
from werkzeug.security import generate_password_hash
from app.database import Base, SessionLocal, engine
from app import models


def populate_database():
    print("Limpando e criando tabelas...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        print("Criando administrador padrão...")

        admin = models.Pessoa(
            tipo="administrador",
            nome_completo="Administrador",
            senha=generate_password_hash("admin123"),
            funcao="administrador",
            data_nasc=date(2000, 1, 1),
        )
        session.add(admin)
        session.flush()

        pessoa_fisica = models.Pessoa_fisica(
            cpf="00000000000",
            id_pessoa=admin.id,
        )
        session.add(pessoa_fisica)

        endereco = models.Endereco(
            cep="00000000",
            rua="Rua Padrão",
            bairro="Bairro Padrão",
            cidade="Porto Alegre",
            estado="RS",
            id_pessoa=admin.id,
        )
        session.add(endereco)

        email = models.Email(
            email_pessoal="admin@pidstech.com",
            id_pessoa=admin.id,
        )
        session.add(email)

        telefone = models.Telefone(
            telefone_celular="00000000000",
            id_pessoa=admin.id,
        )
        session.add(telefone)

        session.commit()
        print("Admin padrão criado!")
        print("  Login: admin@pidstech.com")
        print("  Senha: admin123")
        print("\nLembre de trocar a senha após o primeiro acesso.")

    except Exception as e:
        print(f"Ocorreu um erro: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    populate_database()

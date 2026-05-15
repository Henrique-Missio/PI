"""
Script didático: DDL (create/drop tables) + DML (inserts) com sessão explícita.
Execute na raiz do projeto: python setup_database.py
"""
from sqlalchemy import select
from app.database import Base, SessionLocal, engine
from app import models


def populate_database():
    print("Limpando e criando tabelas...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        print("Tabelas criadas com sucesso.")
        session.commit()
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    populate_database()

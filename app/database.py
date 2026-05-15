import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from config import INSTANCE_DIR

os.makedirs(INSTANCE_DIR, exist_ok=True)

_db_path = os.path.join(INSTANCE_DIR, "Pids.db").replace("\\", "/")
DATABASE_URL = f"sqlite:///{_db_path}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
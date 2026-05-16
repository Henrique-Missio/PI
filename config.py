import os

BASE_DIR     = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")


class Config:
    SECRET_KEY   = os.environ.get("SECRET_KEY", "pidstech-dev-key-2025")
    SESSION_TYPE = "filesystem"
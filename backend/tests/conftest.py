import os

# Banco isolado para testes (SQLite em arquivo temporário)
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///./.pytest_ttv.sqlite")
os.environ.setdefault("SECRET_KEY", "test-secret")

from app.config import get_settings

get_settings.cache_clear()

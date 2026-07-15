"""
Camada de acesso ao banco de dados SQLite.
Centraliza conexões e fornece context manager.
"""
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from backend.config import DATABASE_PATH


def get_connection(db_path: Path = None) -> sqlite3.Connection:
    """Cria e retorna uma conexão SQLite com Row factory."""
    path = db_path or DATABASE_PATH
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db(db_path: Path = None):
    """Context manager para conexão ao banco de dados.

    Uso:
        with get_db() as conn:
            cursor = conn.execute("SELECT ...")
    """
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: Path = None, schema_path: Path = None):
    """Inicializa o banco executando o schema SQL."""
    from backend.config import SCHEMA_PATH
    db = db_path or DATABASE_PATH
    schema = schema_path or SCHEMA_PATH

    # Garante que o diretório existe
    db.parent.mkdir(parents=True, exist_ok=True)

    with open(schema, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    conn = sqlite3.connect(str(db))
    try:
        conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()

    return db

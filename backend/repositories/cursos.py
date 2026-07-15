"""
Repositório de cursos — acesso centralizado à tabela cursos.
"""
from backend.database import get_db


def listar_cursos(db_path=None) -> list[dict]:
    """Lista todos os cursos ativos.

    Returns:
        Lista de dicionários com dados dos cursos.
    """
    with get_db(db_path) as conn:
        cursor = conn.execute(
            "SELECT * FROM cursos WHERE ativo = 1 ORDER BY nome"
        )
        return [dict(row) for row in cursor.fetchall()]


def buscar_curso_por_id(curso_id: int, db_path=None) -> dict | None:
    """Busca um curso pelo ID.

    Args:
        curso_id: ID do curso.

    Returns:
        Dicionário com dados do curso ou None.
    """
    with get_db(db_path) as conn:
        cursor = conn.execute("SELECT * FROM cursos WHERE id = ?", (curso_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

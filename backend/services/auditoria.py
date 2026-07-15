"""
Serviço de auditoria para registro de alterações.

Toda edição feita por funcionários é registrada na tabela historico_edicoes,
garantindo rastreabilidade completa das modificações.
"""
from datetime import datetime
from backend.database import get_db


def registrar_alteracao(
    tabela_alterada: str,
    identificador_registro: str,
    campo_alterado: str,
    valor_anterior,
    valor_novo,
    usuario_responsavel: str = "sistema",
    db_path=None,
):
    """Registra uma alteração na tabela de auditoria.

    Args:
        tabela_alterada: Nome da tabela que foi alterada.
        identificador_registro: ID ou identificador do registro alterado.
        campo_alterado: Nome do campo que foi alterado.
        valor_anterior: Valor antes da alteração.
        valor_novo: Valor após a alteração.
        usuario_responsavel: Quem realizou a alteração.
        db_path: Caminho opcional do banco (para testes).
    """
    with get_db(db_path) as conn:
        conn.execute(
            """
            INSERT INTO historico_edicoes
                (tabela_alterada, identificador_registro, campo_alterado,
                 valor_anterior, valor_novo, usuario_responsavel, data_hora)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                tabela_alterada,
                str(identificador_registro),
                campo_alterado,
                str(valor_anterior) if valor_anterior is not None else None,
                str(valor_novo) if valor_novo is not None else None,
                usuario_responsavel,
                datetime.now().isoformat(),
            ),
        )


def buscar_historico(
    tabela: str = None,
    identificador: str = None,
    limite: int = 100,
    offset: int = 0,
    db_path=None,
) -> list[dict]:
    """Busca registros de auditoria com filtros opcionais.

    Args:
        tabela: Filtrar por nome da tabela alterada.
        identificador: Filtrar por identificador do registro.
        limite: Número máximo de registros.
        offset: Deslocamento para paginação.
        db_path: Caminho opcional do banco.

    Returns:
        Lista de dicionários com registros de auditoria.
    """
    with get_db(db_path) as conn:
        query = "SELECT * FROM historico_edicoes WHERE 1=1"
        params = []

        if tabela:
            query += " AND tabela_alterada = ?"
            params.append(tabela)

        if identificador:
            query += " AND identificador_registro = ?"
            params.append(identificador)

        query += " ORDER BY data_hora DESC LIMIT ? OFFSET ?"
        params.extend([limite, offset])

        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

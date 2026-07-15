"""
Repositório de estudantes — acesso centralizado à tabela estudantes
e dados relacionados (acompanhamentos, matrículas de disciplinas).
"""
from backend.database import get_db


def listar_estudantes(
    curso_id: int = None,
    ano: int = None,
    semestre: int = None,
    risco: str = None,
    busca: str = None,
    limite: int = 50,
    offset: int = 0,
    ordenar_por: str = "probabilidade_risco",
    ordem: str = "DESC",
    db_path=None,
) -> dict:
    """Lista estudantes com filtros, paginação e ordenação.

    Args:
        curso_id: Filtrar por curso.
        ano: Filtrar por ano do período letivo.
        semestre: Filtrar por semestre do período letivo.
        risco: Filtrar por classificação de risco (OK, Atenção, Perigo).
        busca: Busca por nome ou matrícula.
        limite: Registros por página.
        offset: Deslocamento.
        ordenar_por: Campo para ordenação.
        ordem: ASC ou DESC.
        db_path: Caminho opcional do banco.

    Returns:
        Dicionário com 'estudantes' (lista) e 'total' (int).
    """
    campos_validos = {
        "probabilidade_risco", "nome", "matricula", "media_global",
        "media_semestre", "frequencia_media", "reprovacoes",
        "percentual_integralizacao", "distancia_km",
    }
    if ordenar_por not in campos_validos:
        ordenar_por = "probabilidade_risco"
    if ordem.upper() not in ("ASC", "DESC"):
        ordem = "DESC"

    with get_db(db_path) as conn:
        # Query principal com JOIN no último acompanhamento
        base_query = """
            FROM estudantes e
            LEFT JOIN (
                SELECT a1.*
                FROM acompanhamentos a1
                INNER JOIN (
                    SELECT estudante_id, MAX(id) as max_id
                    FROM acompanhamentos
                    GROUP BY estudante_id
                ) a2 ON a1.id = a2.max_id
            ) a ON e.id = a.estudante_id
            LEFT JOIN cursos c ON e.curso_id = c.id
            LEFT JOIN acompanhamentos_funcionarios af ON e.id = af.estudante_id
            WHERE 1=1
        """
        params = []

        if curso_id is not None:
            base_query += " AND e.curso_id = ?"
            params.append(curso_id)

        if risco:
            base_query += " AND a.classificacao_risco = ?"
            params.append(risco)

        if busca:
            base_query += " AND (e.nome LIKE ? OR e.matricula LIKE ?)"
            params.extend([f"%{busca}%", f"%{busca}%"])

        if ano is not None:
            base_query += """
                AND a.periodo_letivo_id IN (
                    SELECT id FROM periodos_letivos WHERE ano = ?
                )
            """
            params.append(ano)

        if semestre is not None:
            base_query += """
                AND a.periodo_letivo_id IN (
                    SELECT id FROM periodos_letivos WHERE semestre = ?
                )
            """
            params.append(semestre)

        # Contagem total
        count_cursor = conn.execute(
            f"SELECT COUNT(DISTINCT e.id) {base_query}", params
        )
        total = count_cursor.fetchone()[0]

        # Query de dados
        select_query = f"""
            SELECT DISTINCT
                e.id, e.matricula, e.nome, e.telefone, e.sexo,
                e.curso_id, c.nome as curso_nome, e.situacao,
                e.ano_ingresso, e.semestre_ingresso,
                a.periodo_curricular, a.media_global, a.media_semestre,
                a.frequencia_media, a.disciplinas_cursadas,
                a.disciplinas_aprovadas, a.reprovacoes,
                a.reprovacoes_sucessivas, a.percentual_integralizacao,
                a.trancamentos, a.distancia_km,
                a.probabilidade_risco, a.classificacao_risco, a.z_score,
                af.funcionario_responsavel, af.situacao_atendimento,
                af.ultimo_contato, af.prioridade_manual
            {base_query}
            ORDER BY {ordenar_por} {ordem} NULLS LAST
            LIMIT ? OFFSET ?
        """
        params.extend([limite, offset])

        cursor = conn.execute(select_query, params)
        estudantes = [dict(row) for row in cursor.fetchall()]

        return {"estudantes": estudantes, "total": total}


def buscar_estudante_por_id(estudante_id: int, db_path=None) -> dict | None:
    """Busca um estudante pelo ID com dados completos.

    Returns:
        Dicionário completo do estudante ou None.
    """
    with get_db(db_path) as conn:
        cursor = conn.execute(
            """
            SELECT e.*, c.nome as curso_nome, c.duracao_periodos,
                   af.funcionario_responsavel, af.situacao_atendimento,
                   af.observacao, af.encaminhamento,
                   af.data_prevista_contato, af.ultimo_contato,
                   af.estudante_contatado, af.acao_realizada,
                   af.prioridade_manual
            FROM estudantes e
            LEFT JOIN cursos c ON e.curso_id = c.id
            LEFT JOIN acompanhamentos_funcionarios af ON e.id = af.estudante_id
            WHERE e.id = ?
            """,
            (estudante_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def buscar_historico_estudante(estudante_id: int, db_path=None) -> list[dict]:
    """Busca o histórico completo de acompanhamentos de um estudante.

    Returns:
        Lista de acompanhamentos ordenados cronologicamente.
    """
    with get_db(db_path) as conn:
        cursor = conn.execute(
            """
            SELECT a.*, pl.ano, pl.semestre,
                   CAST(pl.ano AS TEXT) || '.' || CAST(pl.semestre AS TEXT) as periodo_letivo
            FROM acompanhamentos a
            JOIN periodos_letivos pl ON a.periodo_letivo_id = pl.id
            WHERE a.estudante_id = ?
            ORDER BY pl.ano, pl.semestre
            """,
            (estudante_id,),
        )
        return [dict(row) for row in cursor.fetchall()]


def buscar_disciplinas_estudante(
    estudante_id: int, periodo_letivo_id: int = None, db_path=None
) -> list[dict]:
    """Busca as disciplinas matriculadas de um estudante.

    Args:
        estudante_id: ID do estudante.
        periodo_letivo_id: Filtrar por período (opcional).

    Returns:
        Lista de matrículas em disciplinas.
    """
    with get_db(db_path) as conn:
        query = """
            SELECT md.*, d.nome as disciplina_nome, d.codigo as disciplina_codigo,
                   d.carga_horaria, d.periodo_recomendado,
                   pl.ano, pl.semestre
            FROM matriculas_disciplinas md
            JOIN disciplinas d ON md.disciplina_id = d.id
            JOIN periodos_letivos pl ON md.periodo_letivo_id = pl.id
            WHERE md.estudante_id = ?
        """
        params = [estudante_id]

        if periodo_letivo_id:
            query += " AND md.periodo_letivo_id = ?"
            params.append(periodo_letivo_id)

        query += " ORDER BY pl.ano, pl.semestre, d.periodo_recomendado"

        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

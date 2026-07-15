"""
Rotas de dashboard — endpoints para resumo, histograma e evolução.
"""
import numpy as np
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from backend.database import get_db
from backend.services.estatisticas import resumo_distribuicao


router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/resumo")
def get_resumo(
    curso_id: Optional[int] = Query(None),
    ano: Optional[int] = Query(None),
    semestre: Optional[int] = Query(None),
):
    """Retorna resumo geral para o dashboard."""
    with get_db() as conn:
        # Query base com filtros
        filtro_sql = ""
        params = []

        if curso_id is not None:
            filtro_sql += " AND e.curso_id = ?"
            params.append(curso_id)

        periodo_filtro = ""
        if ano is not None or semestre is not None:
            periodo_filtro = """
                AND a.periodo_letivo_id IN (
                    SELECT id FROM periodos_letivos WHERE 1=1
            """
            if ano is not None:
                periodo_filtro += " AND ano = ?"
                params.append(ano)
            if semestre is not None:
                periodo_filtro += " AND semestre = ?"
                params.append(semestre)
            periodo_filtro += ")"
            filtro_sql += periodo_filtro

        # Total de estudantes e classificações
        cursor = conn.execute(
            f"""
            SELECT
                COUNT(DISTINCT e.id) as total,
                SUM(CASE WHEN a.classificacao_risco = 'OK' THEN 1 ELSE 0 END) as total_ok,
                SUM(CASE WHEN a.classificacao_risco = 'Atenção' THEN 1 ELSE 0 END) as total_atencao,
                SUM(CASE WHEN a.classificacao_risco = 'Perigo' THEN 1 ELSE 0 END) as total_perigo,
                AVG(a.media_global) as media_global_geral,
                AVG(a.frequencia_media) as frequencia_media_geral,
                AVG(CASE WHEN a.disciplinas_cursadas > 0
                    THEN CAST(a.reprovacoes AS FLOAT) / a.disciplinas_cursadas
                    ELSE 0 END) as taxa_reprovacao_media
            FROM estudantes e
            LEFT JOIN (
                SELECT a1.* FROM acompanhamentos a1
                INNER JOIN (
                    SELECT estudante_id, MAX(id) as max_id
                    FROM acompanhamentos GROUP BY estudante_id
                ) a2 ON a1.id = a2.max_id
            ) a ON e.id = a.estudante_id
            WHERE 1=1 {filtro_sql}
            """,
            params,
        )
        row = cursor.fetchone()
        total = row["total"] or 0
        total_ok = row["total_ok"] or 0
        total_atencao = row["total_atencao"] or 0
        total_perigo = row["total_perigo"] or 0

        # Mediana
        medias_cursor = conn.execute(
            f"""
            SELECT a.media_global
            FROM estudantes e
            LEFT JOIN (
                SELECT a1.* FROM acompanhamentos a1
                INNER JOIN (
                    SELECT estudante_id, MAX(id) as max_id
                    FROM acompanhamentos GROUP BY estudante_id
                ) a2 ON a1.id = a2.max_id
            ) a ON e.id = a.estudante_id
            WHERE a.media_global IS NOT NULL {filtro_sql}
            ORDER BY a.media_global
            """,
            params,
        )
        medias = [r["media_global"] for r in medias_cursor.fetchall()]
        mediana = float(np.median(medias)) if medias else None

        # Sem contato
        sem_contato_cursor = conn.execute(
            """
            SELECT COUNT(*) as cnt FROM estudantes e
            LEFT JOIN acompanhamentos_funcionarios af ON e.id = af.estudante_id
            WHERE af.id IS NULL OR af.ultimo_contato IS NULL
            """,
        )
        sem_contato = sem_contato_cursor.fetchone()["cnt"]

        # Acompanhamentos atrasados
        atrasados_cursor = conn.execute(
            """
            SELECT COUNT(*) as cnt FROM acompanhamentos_funcionarios
            WHERE situacao_atendimento IN ('pendente', 'em_andamento')
            AND data_prevista_contato < datetime('now')
            AND data_prevista_contato IS NOT NULL
            """,
        )
        acompanhamentos_atrasados = atrasados_cursor.fetchone()["cnt"]

        # Curso com maior % Perigo
        curso_perigo_cursor = conn.execute(
            """
            SELECT c.nome,
                   COUNT(CASE WHEN a.classificacao_risco = 'Perigo' THEN 1 END) * 100.0 / COUNT(*) as pct
            FROM estudantes e
            JOIN cursos c ON e.curso_id = c.id
            LEFT JOIN (
                SELECT a1.* FROM acompanhamentos a1
                INNER JOIN (
                    SELECT estudante_id, MAX(id) as max_id
                    FROM acompanhamentos GROUP BY estudante_id
                ) a2 ON a1.id = a2.max_id
            ) a ON e.id = a.estudante_id
            WHERE a.classificacao_risco IS NOT NULL
            GROUP BY c.id
            ORDER BY pct DESC
            LIMIT 1
            """,
        )
        curso_perigo_row = curso_perigo_cursor.fetchone()
        curso_maior_perigo = curso_perigo_row["nome"] if curso_perigo_row else None

        # Período com maior risco médio
        periodo_risco_cursor = conn.execute(
            """
            SELECT a.periodo_curricular as periodo,
                   AVG(a.probabilidade_risco) as risco_medio
            FROM acompanhamentos a
            WHERE a.probabilidade_risco IS NOT NULL
            GROUP BY a.periodo_curricular
            ORDER BY risco_medio DESC
            LIMIT 1
            """,
        )
        periodo_risco_row = periodo_risco_cursor.fetchone()
        periodo_maior_risco = (
            f"P{periodo_risco_row['periodo']}" if periodo_risco_row else None
        )

        return {
            "total_estudantes": total,
            "total_ok": total_ok,
            "total_atencao": total_atencao,
            "total_perigo": total_perigo,
            "percentual_ok": round(total_ok / total * 100, 1) if total > 0 else 0,
            "percentual_atencao": round(total_atencao / total * 100, 1) if total > 0 else 0,
            "percentual_perigo": round(total_perigo / total * 100, 1) if total > 0 else 0,
            "media_global_geral": round(row["media_global_geral"], 2) if row["media_global_geral"] else None,
            "mediana_global": round(mediana, 2) if mediana else None,
            "frequencia_media_geral": round(row["frequencia_media_geral"], 1) if row["frequencia_media_geral"] else None,
            "taxa_reprovacao_media": round(row["taxa_reprovacao_media"] * 100, 1) if row["taxa_reprovacao_media"] else None,
            "sem_contato": sem_contato,
            "acompanhamentos_atrasados": acompanhamentos_atrasados,
            "curso_maior_perigo": curso_maior_perigo,
            "periodo_maior_risco": periodo_maior_risco,
        }


@router.get("/histograma")
def get_histograma(
    indicador: str = Query("media_global"),
    curso_id: Optional[int] = Query(None),
    ano: Optional[int] = Query(None),
    semestre: Optional[int] = Query(None),
    bins: int = Query(20, ge=5, le=50),
):
    """Retorna dados para histograma de um indicador selecionável."""
    indicadores_validos = {
        "media_global", "media_semestre", "frequencia_media",
        "probabilidade_risco", "percentual_integralizacao",
    }
    if indicador not in indicadores_validos:
        raise HTTPException(
            status_code=400,
            detail=f"Indicador inválido. Válidos: {indicadores_validos}",
        )

    with get_db() as conn:
        filtro_sql = ""
        params = []

        if curso_id is not None:
            filtro_sql += " AND e.curso_id = ?"
            params.append(curso_id)

        if ano is not None:
            filtro_sql += " AND pl.ano = ?"
            params.append(ano)

        if semestre is not None:
            filtro_sql += " AND pl.semestre = ?"
            params.append(semestre)

        cursor = conn.execute(
            f"""
            SELECT a.{indicador}
            FROM acompanhamentos a
            JOIN estudantes e ON a.estudante_id = e.id
            JOIN periodos_letivos pl ON a.periodo_letivo_id = pl.id
            WHERE a.{indicador} IS NOT NULL {filtro_sql}
            """,
            params,
        )
        valores = [row[0] for row in cursor.fetchall()]

    if not valores:
        return {
            "indicador": indicador,
            "valores": [],
            "bins": [],
            "contagens": [],
            "media": 0,
            "mediana": 0,
            "desvio_padrao": 0,
        }

    arr = np.array(valores)
    contagens, bordas = np.histogram(arr, bins=bins)

    return {
        "indicador": indicador,
        "valores": valores,
        "bins": bordas.tolist(),
        "contagens": contagens.tolist(),
        "media": round(float(np.mean(arr)), 4),
        "mediana": round(float(np.median(arr)), 4),
        "desvio_padrao": round(float(np.std(arr, ddof=1)), 4) if len(arr) > 1 else 0,
    }


@router.get("/evolucao")
def get_evolucao(
    indicador: str = Query("media_global"),
    curso_id: Optional[int] = Query(None),
):
    """Retorna evolução de um indicador ao longo dos semestres."""
    indicadores_validos = {
        "media_global", "media_semestre", "frequencia_media",
        "probabilidade_risco", "reprovacoes",
    }
    if indicador not in indicadores_validos:
        raise HTTPException(
            status_code=400,
            detail=f"Indicador inválido. Válidos: {indicadores_validos}",
        )

    with get_db() as conn:
        filtro_sql = ""
        params = []

        if curso_id is not None:
            filtro_sql += " AND e.curso_id = ?"
            params.append(curso_id)

        cursor = conn.execute(
            f"""
            SELECT
                CAST(pl.ano AS TEXT) || '.' || CAST(pl.semestre AS TEXT) as periodo,
                AVG(a.{indicador}) as valor_medio
            FROM acompanhamentos a
            JOIN estudantes e ON a.estudante_id = e.id
            JOIN periodos_letivos pl ON a.periodo_letivo_id = pl.id
            WHERE a.{indicador} IS NOT NULL {filtro_sql}
            GROUP BY pl.ano, pl.semestre
            ORDER BY pl.ano, pl.semestre
            """,
            params,
        )
        rows = cursor.fetchall()

    return {
        "indicador": indicador,
        "periodos": [row["periodo"] for row in rows],
        "valores": [round(row["valor_medio"], 4) for row in rows],
    }

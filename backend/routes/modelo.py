"""
Rotas do modelo de regressão logística — treinar e recalcular.
"""
import subprocess
import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException
from backend.config import MODEL_PATH, DATABASE_PATH
from backend.database import get_db

router = APIRouter(prefix="/api/modelo", tags=["Modelo"])

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


@router.post("/treinar")
def treinar_modelo():
    """Executa o script de treinamento do modelo."""
    script = ROOT_DIR / "scripts" / "treinar_modelo.py"
    if not script.exists():
        raise HTTPException(
            status_code=500,
            detail="Script de treinamento não encontrado.",
        )

    try:
        resultado = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(ROOT_DIR),
        )
        if resultado.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Erro no treinamento: {resultado.stderr}",
            )

        return {
            "status": "sucesso",
            "mensagem": "Modelo treinado com sucesso.",
            "saida": resultado.stdout[-2000:] if resultado.stdout else "",
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=504,
            detail="Tempo limite excedido para treinamento do modelo.",
        )


@router.post("/recalcular")
def recalcular_probabilidades():
    """Recalcula probabilidades de risco para todos os estudantes
    usando o modelo treinado mais recente."""
    import joblib
    import pandas as pd
    from backend.services.risco import classificar_risco

    if not MODEL_PATH.exists():
        raise HTTPException(
            status_code=400,
            detail="Modelo ainda não treinado. Execute /api/modelo/treinar primeiro.",
        )

    try:
        pipeline = joblib.load(str(MODEL_PATH))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao carregar modelo: {str(e)}",
        )

    with get_db() as conn:
        # Busca último acompanhamento de cada estudante
        cursor = conn.execute(
            """
            SELECT a.id, a.estudante_id, a.media_global, a.media_semestre,
                   a.frequencia_media, a.reprovacoes, a.reprovacoes_sucessivas,
                   a.trancamentos, a.percentual_integralizacao, a.distancia_km,
                   a.disciplinas_cursadas, a.disciplinas_aprovadas,
                   a.periodo_curricular,
                   e.curso_id, c.nome as curso_nome
            FROM acompanhamentos a
            INNER JOIN (
                SELECT estudante_id, MAX(id) as max_id
                FROM acompanhamentos GROUP BY estudante_id
            ) ult ON a.id = ult.max_id
            JOIN estudantes e ON a.estudante_id = e.id
            JOIN cursos c ON e.curso_id = c.id
            """
        )
        registros = [dict(r) for r in cursor.fetchall()]

    if not registros:
        return {"status": "aviso", "mensagem": "Nenhum registro para recalcular."}

    # Prepara DataFrame para o modelo
    df = pd.DataFrame(registros)

    # Calcula features derivadas
    df["variacao_media"] = 0.0  # Sem dado anterior neste contexto
    df["taxa_reprovacao"] = df.apply(
        lambda r: r["reprovacoes"] / r["disciplinas_cursadas"]
        if r["disciplinas_cursadas"] and r["disciplinas_cursadas"] > 0 else 0.0,
        axis=1,
    )
    df["atraso_curricular"] = 0
    df["curso"] = df["curso_nome"]
    df["turno"] = "integral"
    df["assistencia_estudantil"] = "nao"

    # Features que o modelo espera
    feature_cols_num = [
        "media_global", "media_semestre", "variacao_media",
        "frequencia_media", "reprovacoes", "reprovacoes_sucessivas",
        "taxa_reprovacao", "trancamentos", "percentual_integralizacao",
        "atraso_curricular", "distancia_km",
    ]
    feature_cols_cat = ["curso", "periodo_curricular", "turno", "assistencia_estudantil"]

    for col in feature_cols_num + feature_cols_cat:
        if col not in df.columns:
            df[col] = 0

    X = df[feature_cols_num + feature_cols_cat]

    # Prediz probabilidades
    try:
        probabilidades = pipeline.predict_proba(X)[:, 1]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao calcular probabilidades: {str(e)}",
        )

    # Atualiza no banco
    atualizados = 0
    with get_db() as conn:
        for i, registro in enumerate(registros):
            prob = float(probabilidades[i])
            classif = classificar_risco(prob)

            conn.execute(
                """
                UPDATE acompanhamentos
                SET probabilidade_risco = ?,
                    classificacao_risco = ?,
                    data_calculo = datetime('now')
                WHERE id = ?
                """,
                (prob, classif["classificacao"], registro["id"]),
            )
            atualizados += 1

    return {
        "status": "sucesso",
        "mensagem": f"Probabilidades recalculadas para {atualizados} estudantes.",
        "total_recalculados": atualizados,
    }

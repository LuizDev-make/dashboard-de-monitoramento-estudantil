"""
Script para recálculo de indicadores estatísticos.

Recalcula z-scores, escore composto e atualiza a tabela acompanhamentos.
Deve ser executado após importação de novos dados ou periodicamente.

Uso:
    python scripts/calcular_indicadores.py
"""
import sys
import sqlite3
import numpy as np
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.config import DATABASE_PATH
from backend.services.estatisticas import calcular_z_score, resumo_distribuicao


def calcular():
    """Recalcula z-scores por grupo e atualiza o banco."""
    print("=" * 60)
    print("  RECÁLCULO DE INDICADORES ESTATÍSTICOS")
    print("=" * 60)

    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row

    # Busca todos os acompanhamentos com informações de grupo
    cursor = conn.execute("""
        SELECT a.id, a.media_global, a.media_semestre, a.frequencia_media,
               a.reprovacoes, a.disciplinas_cursadas, a.periodo_curricular,
               e.curso_id, pl.ano, pl.semestre
        FROM acompanhamentos a
        JOIN estudantes e ON a.estudante_id = e.id
        JOIN periodos_letivos pl ON a.periodo_letivo_id = pl.id
    """)
    registros = [dict(row) for row in cursor.fetchall()]

    if not registros:
        print("⚠️  Nenhum registro encontrado.")
        conn.close()
        return

    print(f"📊 Total de registros: {len(registros)}")

    # Agrupa por (curso_id, ano, semestre, periodo_curricular)
    grupos = {}
    for reg in registros:
        chave = (reg["curso_id"], reg["ano"], reg["semestre"], reg["periodo_curricular"])
        if chave not in grupos:
            grupos[chave] = []
        grupos[chave].append(reg)

    print(f"📂 Total de grupos: {len(grupos)}")

    # Calcula z-scores por grupo
    atualizados = 0
    for chave, membros in grupos.items():
        if len(membros) < 2:
            continue

        medias = [m["media_global"] for m in membros if m["media_global"] is not None]
        if len(medias) < 2:
            continue

        media_grupo = float(np.mean(medias))
        desvio_grupo = float(np.std(medias, ddof=1))

        for membro in membros:
            if membro["media_global"] is not None:
                z = calcular_z_score(membro["media_global"], media_grupo, desvio_grupo)
                if z is not None:
                    conn.execute(
                        "UPDATE acompanhamentos SET z_score = ?, data_calculo = ? WHERE id = ?",
                        (z, datetime.now().isoformat(), membro["id"]),
                    )
                    atualizados += 1

    conn.commit()
    conn.close()

    print(f"\n✅ {atualizados} registros atualizados com z-scores.")
    print("🎉 Recálculo concluído!")


if __name__ == "__main__":
    calcular()

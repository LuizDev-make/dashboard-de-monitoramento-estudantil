"""
Serviço de cálculos estatísticos para o sistema de monitoramento UFRPE.

Implementa todos os indicadores estatísticos descritivos e padronizados:
- Taxas de aprovação/reprovação
- Média, desvio-padrão, coeficiente de variação
- Variação da média entre semestres
- Z-score por grupo (curso + semestre + período curricular)
- Escore acadêmico composto
- Resumo de distribuição
- Evolução longitudinal
"""
import numpy as np
from scipy import stats as scipy_stats
from typing import Any


def taxa_aprovacao(aprovadas: int, cursadas: int) -> float:
    """Calcula a taxa de aprovação.

    Args:
        aprovadas: Número de disciplinas aprovadas.
        cursadas: Número de disciplinas cursadas.

    Returns:
        Taxa de aprovação entre 0.0 e 1.0. Retorna 0.0 se cursadas == 0.
    """
    if cursadas <= 0:
        return 0.0
    return aprovadas / cursadas


def taxa_reprovacao(reprovacoes: int, cursadas: int) -> float:
    """Calcula a taxa de reprovação.

    Args:
        reprovacoes: Número de reprovações.
        cursadas: Número de disciplinas cursadas.

    Returns:
        Taxa de reprovação entre 0.0 e 1.0. Retorna 0.0 se cursadas == 0.
    """
    if cursadas <= 0:
        return 0.0
    return reprovacoes / cursadas


def variacao_media(media_atual: float, media_anterior: float) -> float | None:
    """Calcula a variação da média em relação ao semestre anterior.

    Args:
        media_atual: Média do semestre atual.
        media_anterior: Média do semestre anterior.

    Returns:
        Variação (diferença). None se media_anterior for None.
    """
    if media_anterior is None:
        return None
    return media_atual - media_anterior


def coeficiente_variacao(valores: list[float]) -> float | None:
    """Calcula o coeficiente de variação (CV = σ/μ).

    Args:
        valores: Lista de valores numéricos.

    Returns:
        Coeficiente de variação. None se a média for zero ou lista vazia.
    """
    if not valores:
        return None
    arr = np.array(valores, dtype=float)
    media = np.mean(arr)
    if media == 0:
        return None
    return float(np.std(arr, ddof=1) / media)


def calcular_z_score(valor: float, media_grupo: float, desvio_grupo: float) -> float | None:
    """Calcula o z-score de um valor em relação ao seu grupo.

    O z-score é calculado dentro de grupos coerentes:
    mesmo curso + mesmo semestre letivo + mesmo período curricular.

    Args:
        valor: Valor individual do estudante.
        media_grupo: Média do grupo de referência.
        desvio_grupo: Desvio-padrão do grupo de referência.

    Returns:
        Z-score. None se o desvio for zero.
    """
    if desvio_grupo is None or desvio_grupo == 0:
        return None
    return (valor - media_grupo) / desvio_grupo


def calcular_z_scores_grupo(valores: list[float]) -> list[float | None]:
    """Calcula z-scores para todos os valores de um grupo.

    Args:
        valores: Lista de valores do grupo.

    Returns:
        Lista de z-scores correspondentes.
    """
    if not valores or len(valores) < 2:
        return [None] * len(valores) if valores else []

    arr = np.array(valores, dtype=float)
    media = float(np.mean(arr))
    desvio = float(np.std(arr, ddof=1))

    return [calcular_z_score(v, media, desvio) for v in valores]


def maior_sequencia_reprovacoes(situacoes: list[str]) -> int:
    """Calcula a maior sequência de reprovações sucessivas.

    Args:
        situacoes: Lista de situações das disciplinas em ordem cronológica
                   ('aprovado', 'reprovado_nota', 'reprovado_falta', 'trancado').

    Returns:
        Comprimento da maior sequência de reprovações consecutivas.
    """
    if not situacoes:
        return 0

    max_seq = 0
    seq_atual = 0
    for sit in situacoes:
        if sit in ('reprovado_nota', 'reprovado_falta'):
            seq_atual += 1
            max_seq = max(max_seq, seq_atual)
        else:
            seq_atual = 0

    return max_seq


def percentual_integralizacao(ch_concluida: float, ch_total_curso: float) -> float:
    """Calcula o percentual de integralização curricular.

    Args:
        ch_concluida: Carga horária concluída (aprovada).
        ch_total_curso: Carga horária total do curso.

    Returns:
        Percentual de integralização (0.0 a 100.0).
    """
    if ch_total_curso <= 0:
        return 0.0
    return min((ch_concluida / ch_total_curso) * 100, 100.0)


def atraso_curricular(periodo_atual: int, periodos_cursados: int) -> int:
    """Calcula o atraso curricular em número de períodos.

    Args:
        periodo_atual: Período curricular em que o estudante deveria estar
                       (baseado no tempo de ingresso).
        periodos_cursados: Período curricular efetivo do estudante.

    Returns:
        Atraso em períodos (>= 0).
    """
    return max(0, periodo_atual - periodos_cursados)


def resumo_distribuicao(valores: list[float]) -> dict[str, float | None]:
    """Calcula o resumo estatístico de uma distribuição.

    Args:
        valores: Lista de valores numéricos.

    Returns:
        Dicionário com: media, mediana, desvio_padrao, q1, q3, iqr, minimo, maximo.
    """
    if not valores:
        return {
            "media": None,
            "mediana": None,
            "desvio_padrao": None,
            "q1": None,
            "q3": None,
            "iqr": None,
            "minimo": None,
            "maximo": None,
            "contagem": 0,
        }

    arr = np.array(valores, dtype=float)
    q1 = float(np.percentile(arr, 25))
    q3 = float(np.percentile(arr, 75))

    return {
        "media": float(np.mean(arr)),
        "mediana": float(np.median(arr)),
        "desvio_padrao": float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0,
        "q1": q1,
        "q3": q3,
        "iqr": q3 - q1,
        "minimo": float(np.min(arr)),
        "maximo": float(np.max(arr)),
        "contagem": len(arr),
    }


# ---------------------------------------------------------------
# Escore acadêmico composto
# ---------------------------------------------------------------
#
# Pesos do escore composto (documentados e justificados):
#   - z_media_global (0.30): indicador principal de rendimento
#   - z_frequencia (0.20): assiduidade tem forte correlação com sucesso
#   - z_taxa_aprovacao (0.20): eficiência acadêmica
#   - z_integralizacao (0.15): progresso no curso
#   - z_reprovacoes_sucessivas (-0.15): penaliza padrão de reprovações
#     (valor negativo porque mais reprovações = pior escore)
#
# O escore é uma combinação ponderada de z-scores padronizados
# e NÃO deve ser interpretado como probabilidade.
# ---------------------------------------------------------------

PESOS_ESCORE = {
    "z_media_global": 0.30,
    "z_frequencia": 0.20,
    "z_taxa_aprovacao": 0.20,
    "z_integralizacao": 0.15,
    "z_reprovacoes_sucessivas": -0.15,  # invertido: mais reprovações = pior
}


def escore_academico_composto(z_scores: dict[str, float | None]) -> float | None:
    """Calcula o escore acadêmico composto a partir dos z-scores.

    Combinação ponderada de z-scores padronizados. Valores maiores indicam
    melhor desempenho acadêmico. NÃO é uma probabilidade.

    Args:
        z_scores: Dicionário com z-scores para cada dimensão.
                  Chaves esperadas: z_media_global, z_frequencia,
                  z_taxa_aprovacao, z_integralizacao, z_reprovacoes_sucessivas.

    Returns:
        Escore composto (float) ou None se dados insuficientes.
    """
    escore = 0.0
    peso_total = 0.0

    for chave, peso in PESOS_ESCORE.items():
        valor = z_scores.get(chave)
        if valor is not None:
            escore += peso * valor
            peso_total += abs(peso)

    if peso_total == 0:
        return None

    # Normaliza pelo peso total utilizado para lidar com valores faltantes
    return escore / peso_total


def evolucao_longitudinal(registros: list[dict[str, Any]]) -> dict[str, list]:
    """Extrai a evolução longitudinal de um estudante ao longo dos semestres.

    Args:
        registros: Lista de dicionários de acompanhamentos ordenados
                   cronologicamente. Cada registro deve ter: periodo_letivo,
                   media_global, media_semestre, frequencia_media, reprovacoes,
                   percentual_integralizacao, probabilidade_risco.

    Returns:
        Dicionário com listas de evolução para cada indicador:
        periodos, medias_globais, medias_semestre, frequencias,
        reprovacoes, integralizacao, probabilidades.
    """
    evolucao = {
        "periodos": [],
        "medias_globais": [],
        "medias_semestre": [],
        "frequencias": [],
        "reprovacoes": [],
        "integralizacao": [],
        "probabilidades": [],
    }

    for reg in registros:
        evolucao["periodos"].append(reg.get("periodo_letivo", ""))
        evolucao["medias_globais"].append(reg.get("media_global"))
        evolucao["medias_semestre"].append(reg.get("media_semestre"))
        evolucao["frequencias"].append(reg.get("frequencia_media"))
        evolucao["reprovacoes"].append(reg.get("reprovacoes", 0))
        evolucao["integralizacao"].append(reg.get("percentual_integralizacao", 0))
        evolucao["probabilidades"].append(reg.get("probabilidade_risco"))

    return evolucao


def calcular_estatisticas_turma(registros: list[dict[str, Any]]) -> dict[str, Any]:
    """Calcula estatísticas agregadas de uma turma/grupo de estudantes.

    Args:
        registros: Lista de registros de acompanhamento.

    Returns:
        Dicionário com estatísticas agregadas.
    """
    if not registros:
        return {
            "total_estudantes": 0,
            "resumo_media": resumo_distribuicao([]),
            "resumo_frequencia": resumo_distribuicao([]),
            "taxa_aprovacao_media": 0.0,
            "taxa_reprovacao_media": 0.0,
        }

    medias = [r.get("media_global", 0) for r in registros if r.get("media_global") is not None]
    frequencias = [r.get("frequencia_media", 0) for r in registros if r.get("frequencia_media") is not None]

    taxas_aprov = []
    taxas_reprov = []
    for r in registros:
        cursadas = r.get("disciplinas_cursadas", 0)
        if cursadas and cursadas > 0:
            taxas_aprov.append(taxa_aprovacao(r.get("disciplinas_aprovadas", 0), cursadas))
            taxas_reprov.append(taxa_reprovacao(r.get("reprovacoes", 0), cursadas))

    return {
        "total_estudantes": len(registros),
        "resumo_media": resumo_distribuicao(medias),
        "resumo_frequencia": resumo_distribuicao(frequencias),
        "taxa_aprovacao_media": float(np.mean(taxas_aprov)) if taxas_aprov else 0.0,
        "taxa_reprovacao_media": float(np.mean(taxas_reprov)) if taxas_reprov else 0.0,
    }

"""
Serviço de classificação de risco e fatores de alerta.

Implementa:
- classificar_risco(probabilidade): classifica com base nos limiares
  administrativos do projeto (70% / 85%).
- gerar_fatores_alerta(registro): identifica indicadores descritivos
  de possível risco acadêmico.

IMPORTANTE: A classificação é baseada exclusivamente na probabilidade
estimada pelo modelo de regressão logística. Os limiares são regras
administrativas do projeto, não necessariamente os melhores limiares
estatísticos.
"""
from backend.config import LIMIAR_ATENCAO, LIMIAR_PERIGO


# ---------------------------------------------------------------
# Classificação de risco
# ---------------------------------------------------------------
# | Classificação | Probabilidade    | Cor      |
# |---------------|------------------|----------|
# | OK            | 0% a 69,99%      | verde    |
# | Atenção       | 70% a 84,99%     | amarelo  |
# | Perigo        | 85% a 100%       | vermelho |
#
# Regra de fronteira:
#   70,00% pertence a "Atenção"
#   85,00% pertence a "Perigo"
# ---------------------------------------------------------------


def classificar_risco(probabilidade: float) -> dict:
    """Classifica o risco de um estudante com base na probabilidade do modelo.

    Args:
        probabilidade: Probabilidade estimada pelo modelo (0.0 a 1.0).

    Returns:
        Dicionário com 'classificacao', 'cor', 'probabilidade_percentual'.

    Raises:
        ValueError: Se a probabilidade estiver fora de [0, 1].
    """
    if probabilidade is None:
        raise ValueError("Probabilidade não pode ser None.")

    if not (0.0 <= probabilidade <= 1.0):
        raise ValueError(
            f"Probabilidade deve estar entre 0 e 1. Recebido: {probabilidade}"
        )

    if probabilidade >= LIMIAR_PERIGO:
        classificacao = "Perigo"
        cor = "vermelho"
    elif probabilidade >= LIMIAR_ATENCAO:
        classificacao = "Atenção"
        cor = "amarelo"
    else:
        classificacao = "OK"
        cor = "verde"

    return {
        "classificacao": classificacao,
        "cor": cor,
        "probabilidade_percentual": round(probabilidade * 100, 2),
    }


def gerar_fatores_alerta(registro: dict) -> list[str]:
    """Gera lista de fatores de alerta descritivos para um estudante.

    Analisa os indicadores acadêmicos e retorna mensagens descritivas
    sobre possíveis pontos de atenção. Estas são observações descritivas,
    NÃO provas causais.

    Args:
        registro: Dicionário com dados do acompanhamento acadêmico.
                  Chaves esperadas: media_global, media_semestre,
                  frequencia_media, reprovacoes_sucessivas, trancamentos,
                  percentual_integralizacao, variacao_media, taxa_reprovacao.

    Returns:
        Lista de strings com fatores de alerta identificados.
    """
    alertas = []

    # Média global abaixo do limiar
    media_global = registro.get("media_global")
    if media_global is not None and media_global < 5.0:
        alertas.append(
            f"Média global abaixo de 5,0 (atual: {media_global:.1f})"
        )

    # Média do semestre abaixo do limiar
    media_semestre = registro.get("media_semestre")
    if media_semestre is not None and media_semestre < 5.0:
        alertas.append(
            f"Média do semestre abaixo de 5,0 (atual: {media_semestre:.1f})"
        )

    # Frequência abaixo do mínimo
    frequencia = registro.get("frequencia_media")
    if frequencia is not None and frequencia < 75.0:
        alertas.append(
            f"Frequência média abaixo de 75% (atual: {frequencia:.1f}%)"
        )

    # Reprovações sucessivas
    reprov_sucessivas = registro.get("reprovacoes_sucessivas", 0)
    if reprov_sucessivas is not None and reprov_sucessivas >= 2:
        alertas.append(
            f"Reprovações sucessivas identificadas ({reprov_sucessivas} consecutivas)"
        )

    # Queda da média
    variacao = registro.get("variacao_media")
    if variacao is not None and variacao < -1.0:
        alertas.append(
            f"Queda relevante da média em relação ao semestre anterior "
            f"(variação: {variacao:+.1f})"
        )

    # Integralização abaixo do esperado
    integralizacao = registro.get("percentual_integralizacao")
    periodo = registro.get("periodo_curricular", 1)
    duracao = registro.get("duracao_periodos", 10)
    if integralizacao is not None and periodo is not None and duracao:
        esperado = (periodo / duracao) * 100
        if integralizacao < esperado * 0.7:  # menos de 70% do esperado
            alertas.append(
                f"Integralização abaixo do esperado "
                f"(atual: {integralizacao:.1f}%, esperado: ~{esperado:.0f}%)"
            )

    # Taxa de reprovação alta
    taxa_reprov = registro.get("taxa_reprovacao")
    if taxa_reprov is not None and taxa_reprov > 0.5:
        alertas.append(
            f"Taxa de reprovação acima de 50% (atual: {taxa_reprov*100:.1f}%)"
        )

    # Trancamentos frequentes
    trancamentos = registro.get("trancamentos", 0)
    if trancamentos is not None and trancamentos >= 2:
        alertas.append(
            f"Múltiplos trancamentos registrados ({trancamentos} no período)"
        )

    # Distância elevada
    distancia = registro.get("distancia_km")
    if distancia is not None and distancia > 30:
        alertas.append(
            f"Distância elevada da universidade ({distancia:.1f} km em linha reta)"
        )

    return alertas

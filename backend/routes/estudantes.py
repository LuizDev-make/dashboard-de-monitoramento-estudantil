"""
Rotas de estudantes — endpoints para listagem, detalhe e histórico.
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from backend.repositories.estudantes import (
    listar_estudantes,
    buscar_estudante_por_id,
    buscar_historico_estudante,
    buscar_disciplinas_estudante,
)
from backend.services.risco import classificar_risco, gerar_fatores_alerta
from backend.services.estatisticas import evolucao_longitudinal

router = APIRouter(prefix="/api", tags=["Estudantes"])


@router.get("/estudantes")
def get_estudantes(
    curso_id: Optional[int] = Query(None),
    ano: Optional[int] = Query(None),
    semestre: Optional[int] = Query(None),
    risco: Optional[str] = Query(None),
    busca: Optional[str] = Query(None),
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(50, ge=1, le=200),
    ordenar_por: str = Query("probabilidade_risco"),
    ordem: str = Query("DESC"),
):
    """Lista estudantes com filtros, paginação e ordenação."""
    offset = (pagina - 1) * por_pagina
    resultado = listar_estudantes(
        curso_id=curso_id,
        ano=ano,
        semestre=semestre,
        risco=risco,
        busca=busca,
        limite=por_pagina,
        offset=offset,
        ordenar_por=ordenar_por,
        ordem=ordem,
    )
    return {
        "estudantes": resultado["estudantes"],
        "total": resultado["total"],
        "pagina": pagina,
        "por_pagina": por_pagina,
    }


@router.get("/estudantes/{estudante_id}")
def get_estudante(estudante_id: int):
    """Retorna dados detalhados de um estudante."""
    estudante = buscar_estudante_por_id(estudante_id)
    if not estudante:
        raise HTTPException(status_code=404, detail="Estudante não encontrado")

    # Busca último acompanhamento para fatores de alerta
    historico = buscar_historico_estudante(estudante_id)
    fatores_alerta = []
    ultimo_acompanhamento = None

    if historico:
        ultimo_acompanhamento = historico[-1]
        fatores_alerta = gerar_fatores_alerta(ultimo_acompanhamento)

    # Classificação de risco
    classificacao = None
    if ultimo_acompanhamento and ultimo_acompanhamento.get("probabilidade_risco") is not None:
        try:
            classificacao = classificar_risco(
                ultimo_acompanhamento["probabilidade_risco"]
            )
        except ValueError:
            classificacao = None

    return {
        "estudante": estudante,
        "ultimo_acompanhamento": ultimo_acompanhamento,
        "fatores_alerta": fatores_alerta,
        "classificacao": classificacao,
    }


@router.get("/estudantes/{estudante_id}/historico")
def get_historico_estudante(estudante_id: int):
    """Retorna o histórico completo de acompanhamentos de um estudante."""
    estudante = buscar_estudante_por_id(estudante_id)
    if not estudante:
        raise HTTPException(status_code=404, detail="Estudante não encontrado")

    historico = buscar_historico_estudante(estudante_id)
    evolucao = evolucao_longitudinal(historico)

    # Busca disciplinas do último período
    disciplinas = []
    if historico:
        ultimo = historico[-1]
        disciplinas = buscar_disciplinas_estudante(
            estudante_id, ultimo.get("periodo_letivo_id")
        )

    return {
        "estudante": estudante,
        "historico": historico,
        "evolucao": evolucao,
        "disciplinas_atual": disciplinas,
    }

"""
Schemas Pydantic para validação de dados na API REST.

Define modelos de request e response para todos os endpoints.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


# ---------------------------------------------------------------
# Cursos
# ---------------------------------------------------------------
class CursoResponse(BaseModel):
    id: int
    nome: str
    codigo: str
    campus: str
    duracao_periodos: int
    ativo: int


# ---------------------------------------------------------------
# Períodos Letivos
# ---------------------------------------------------------------
class PeriodoLetivoResponse(BaseModel):
    id: int
    ano: int
    semestre: int
    data_inicio: Optional[str] = None
    data_fim: Optional[str] = None


# ---------------------------------------------------------------
# Estudantes
# ---------------------------------------------------------------
class EstudanteResumo(BaseModel):
    id: int
    matricula: str
    nome: str
    telefone: Optional[str] = None
    sexo: Optional[str] = None
    curso_id: int
    curso_nome: Optional[str] = None
    situacao: str
    ano_ingresso: int
    semestre_ingresso: int
    periodo_curricular: Optional[int] = None
    media_global: Optional[float] = None
    media_semestre: Optional[float] = None
    frequencia_media: Optional[float] = None
    disciplinas_cursadas: Optional[int] = None
    disciplinas_aprovadas: Optional[int] = None
    reprovacoes: Optional[int] = None
    reprovacoes_sucessivas: Optional[int] = None
    percentual_integralizacao: Optional[float] = None
    trancamentos: Optional[int] = None
    distancia_km: Optional[float] = None
    probabilidade_risco: Optional[float] = None
    classificacao_risco: Optional[str] = None
    z_score: Optional[float] = None
    funcionario_responsavel: Optional[str] = None
    situacao_atendimento: Optional[str] = None
    ultimo_contato: Optional[str] = None
    prioridade_manual: Optional[int] = None


class EstudanteListaResponse(BaseModel):
    estudantes: list[EstudanteResumo]
    total: int
    pagina: int = 1
    por_pagina: int = 50


class EstudanteDetalhe(BaseModel):
    id: int
    matricula: str
    nome: str
    telefone: Optional[str] = None
    sexo: Optional[str] = None
    data_nascimento: Optional[str] = None
    cep: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    curso_id: int
    curso_nome: Optional[str] = None
    duracao_periodos: Optional[int] = None
    ano_ingresso: int
    semestre_ingresso: int
    situacao: str
    funcionario_responsavel: Optional[str] = None
    situacao_atendimento: Optional[str] = None
    observacao: Optional[str] = None
    encaminhamento: Optional[str] = None
    data_prevista_contato: Optional[str] = None
    ultimo_contato: Optional[str] = None
    estudante_contatado: Optional[int] = None
    acao_realizada: Optional[str] = None
    prioridade_manual: Optional[int] = None


# ---------------------------------------------------------------
# Acompanhamentos
# ---------------------------------------------------------------
class AcompanhamentoResponse(BaseModel):
    id: int
    estudante_id: int
    periodo_letivo_id: int
    ano: Optional[int] = None
    semestre: Optional[int] = None
    periodo_letivo: Optional[str] = None
    periodo_curricular: Optional[int] = None
    media_global: Optional[float] = None
    media_semestre: Optional[float] = None
    disciplinas_cursadas: Optional[int] = None
    disciplinas_aprovadas: Optional[int] = None
    reprovacoes: Optional[int] = None
    reprovacoes_falta: Optional[int] = None
    reprovacoes_nota: Optional[int] = None
    reprovacoes_sucessivas: Optional[int] = None
    frequencia_media: Optional[float] = None
    carga_horaria_matriculada: Optional[float] = None
    carga_horaria_concluida: Optional[float] = None
    percentual_integralizacao: Optional[float] = None
    trancamentos: Optional[int] = None
    distancia_km: Optional[float] = None
    probabilidade_risco: Optional[float] = None
    classificacao_risco: Optional[str] = None
    z_score: Optional[float] = None
    data_calculo: Optional[str] = None


class AcompanhamentoFuncionarioCreate(BaseModel):
    funcionario_responsavel: Optional[str] = None
    prioridade_manual: Optional[int] = 0
    situacao_atendimento: Optional[str] = "pendente"
    observacao: Optional[str] = None
    encaminhamento: Optional[str] = None
    data_prevista_contato: Optional[str] = None
    ultimo_contato: Optional[str] = None
    estudante_contatado: Optional[int] = 0
    acao_realizada: Optional[str] = None

    @field_validator("situacao_atendimento")
    @classmethod
    def validar_situacao(cls, v):
        validos = {"pendente", "em_andamento", "concluido", "cancelado"}
        if v and v not in validos:
            raise ValueError(f"Situação deve ser uma de: {validos}")
        return v


class AcompanhamentoFuncionarioUpdate(BaseModel):
    funcionario_responsavel: Optional[str] = None
    prioridade_manual: Optional[int] = None
    situacao_atendimento: Optional[str] = None
    observacao: Optional[str] = None
    encaminhamento: Optional[str] = None
    data_prevista_contato: Optional[str] = None
    ultimo_contato: Optional[str] = None
    estudante_contatado: Optional[int] = None
    acao_realizada: Optional[str] = None

    @field_validator("situacao_atendimento")
    @classmethod
    def validar_situacao(cls, v):
        validos = {"pendente", "em_andamento", "concluido", "cancelado"}
        if v is not None and v not in validos:
            raise ValueError(f"Situação deve ser uma de: {validos}")
        return v


# ---------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------
class DashboardResumo(BaseModel):
    total_estudantes: int = 0
    total_ok: int = 0
    total_atencao: int = 0
    total_perigo: int = 0
    percentual_ok: float = 0.0
    percentual_atencao: float = 0.0
    percentual_perigo: float = 0.0
    media_global_geral: Optional[float] = None
    mediana_global: Optional[float] = None
    frequencia_media_geral: Optional[float] = None
    taxa_reprovacao_media: Optional[float] = None
    sem_contato: int = 0
    acompanhamentos_atrasados: int = 0
    curso_maior_perigo: Optional[str] = None
    periodo_maior_risco: Optional[str] = None


class HistogramaResponse(BaseModel):
    indicador: str
    valores: list[float]
    bins: list[float]
    contagens: list[int]
    media: float
    mediana: float
    desvio_padrao: float


class EvolucaoResponse(BaseModel):
    periodos: list[str]
    valores: list[Optional[float]]
    indicador: str


# ---------------------------------------------------------------
# Auditoria
# ---------------------------------------------------------------
class AuditoriaResponse(BaseModel):
    id: int
    tabela_alterada: str
    identificador_registro: str
    campo_alterado: str
    valor_anterior: Optional[str] = None
    valor_novo: Optional[str] = None
    usuario_responsavel: str
    data_hora: str


# ---------------------------------------------------------------
# Modelo
# ---------------------------------------------------------------
class ModeloStatusResponse(BaseModel):
    status: str
    mensagem: str
    metricas: Optional[dict] = None

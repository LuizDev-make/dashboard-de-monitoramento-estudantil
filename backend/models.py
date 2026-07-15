"""
Modelos internos (dataclasses) para entidades do domínio.

Estes não são Pydantic models — são usados internamente pelos services
e repositories para tipagem e organização.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Curso:
    id: int = 0
    nome: str = ""
    codigo: str = ""
    campus: str = "Dois Irmãos"
    duracao_periodos: int = 10
    ativo: bool = True


@dataclass
class Estudante:
    id: int = 0
    matricula: str = ""
    nome: str = ""
    telefone: Optional[str] = None
    sexo: Optional[str] = None
    data_nascimento: Optional[str] = None
    cep: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    curso_id: int = 0
    ano_ingresso: int = 0
    semestre_ingresso: int = 1
    situacao: str = "ativo"


@dataclass
class PeriodoLetivo:
    id: int = 0
    ano: int = 0
    semestre: int = 1
    data_inicio: Optional[str] = None
    data_fim: Optional[str] = None


@dataclass
class Acompanhamento:
    id: int = 0
    estudante_id: int = 0
    periodo_letivo_id: int = 0
    periodo_curricular: Optional[int] = None
    media_global: Optional[float] = None
    media_semestre: Optional[float] = None
    disciplinas_cursadas: int = 0
    disciplinas_aprovadas: int = 0
    reprovacoes: int = 0
    reprovacoes_falta: int = 0
    reprovacoes_nota: int = 0
    reprovacoes_sucessivas: int = 0
    frequencia_media: Optional[float] = None
    carga_horaria_matriculada: float = 0
    carga_horaria_concluida: float = 0
    percentual_integralizacao: float = 0
    trancamentos: int = 0
    distancia_km: Optional[float] = None
    probabilidade_risco: Optional[float] = None
    classificacao_risco: Optional[str] = None
    z_score: Optional[float] = None
    data_calculo: Optional[str] = None


@dataclass
class Disciplina:
    id: int = 0
    codigo: str = ""
    nome: str = ""
    carga_horaria: int = 60
    periodo_recomendado: Optional[int] = None
    curso_id: int = 0

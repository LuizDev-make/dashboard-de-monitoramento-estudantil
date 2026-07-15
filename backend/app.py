"""
Aplicação principal FastAPI — Sistema de Monitoramento UFRPE.

Ponto de entrada da API REST.
Monta todas as rotas, configura CORS e serve arquivos estáticos do frontend.
"""
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.routes import estudantes, dashboard, importacoes, modelo
from backend.repositories import acompanhamentos as acomp_repo
from backend.services import auditoria
from backend.database import get_db
from backend.schemas import (
    AcompanhamentoFuncionarioCreate,
    AcompanhamentoFuncionarioUpdate,
)

# Diretório raiz do projeto
ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend"

app = FastAPI(
    title="Sistema de Monitoramento Estatístico de Estudantes - UFRPE",
    description=(
        "API para monitoramento acadêmico de estudantes da UFRPE. "
        "Todos os dados são sintéticos (fictícios) e gerados para fins "
        "educacionais. O sistema é ferramenta de apoio à decisão, não "
        "substitui a análise humana."
    ),
    version="1.0.0",
)

# CORS — permite acesso do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Monta rotas
app.include_router(estudantes.router)
app.include_router(dashboard.router)
app.include_router(importacoes.router)
app.include_router(modelo.router)


# ---------------------------------------------------------------
# Endpoints de cursos e períodos
# ---------------------------------------------------------------
@app.get("/api/cursos", tags=["Cursos"])
def listar_cursos():
    """Lista todos os cursos ativos."""
    from backend.repositories.cursos import listar_cursos as _listar
    return _listar()


@app.get("/api/periodos-letivos", tags=["Períodos"])
def listar_periodos():
    """Lista todos os períodos letivos."""
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM periodos_letivos ORDER BY ano, semestre"
        )
        return [dict(row) for row in cursor.fetchall()]


# ---------------------------------------------------------------
# Endpoints de acompanhamentos funcionários
# ---------------------------------------------------------------
@app.get("/api/acompanhamentos/{estudante_id}", tags=["Acompanhamentos"])
def get_acompanhamento(estudante_id: int):
    """Busca acompanhamento administrativo de um estudante."""
    registro = acomp_repo.buscar_acompanhamento_funcionario(estudante_id)
    if not registro:
        return {"estudante_id": estudante_id, "acompanhamento": None}
    return {"estudante_id": estudante_id, "acompanhamento": registro}


@app.post("/api/acompanhamentos", tags=["Acompanhamentos"])
def criar_acompanhamento(
    estudante_id: int,
    dados: AcompanhamentoFuncionarioCreate,
):
    """Cria um novo acompanhamento administrativo."""
    novo_id = acomp_repo.criar_acompanhamento_funcionario(
        estudante_id=estudante_id,
        dados=dados.model_dump(exclude_none=True),
    )
    return {"id": novo_id, "mensagem": "Acompanhamento criado com sucesso."}


@app.put("/api/acompanhamentos/{estudante_id}", tags=["Acompanhamentos"])
def atualizar_acompanhamento(
    estudante_id: int,
    dados: AcompanhamentoFuncionarioUpdate,
):
    """Atualiza o acompanhamento administrativo de um estudante."""
    dados_dict = dados.model_dump(exclude_none=True)
    if not dados_dict:
        return {"mensagem": "Nenhum campo para atualizar."}

    try:
        atualizado = acomp_repo.atualizar_acompanhamento_funcionario(
            estudante_id=estudante_id,
            dados=dados_dict,
        )
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=str(e))

    if not atualizado:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=404,
            detail="Acompanhamento não encontrado para este estudante.",
        )

    return {"mensagem": "Acompanhamento atualizado com sucesso."}


# ---------------------------------------------------------------
# Endpoint de auditoria
# ---------------------------------------------------------------
@app.get("/api/auditoria", tags=["Auditoria"])
def get_auditoria(
    tabela: str = None,
    identificador: str = None,
    limite: int = 100,
    offset: int = 0,
):
    """Lista registros de auditoria."""
    return auditoria.buscar_historico(
        tabela=tabela,
        identificador=identificador,
        limite=limite,
        offset=offset,
    )


# ---------------------------------------------------------------
# Servir frontend (arquivos estáticos)
# ---------------------------------------------------------------
if FRONTEND_DIR.exists():
    app.mount(
        "/css",
        StaticFiles(directory=str(FRONTEND_DIR / "css")),
        name="css",
    )
    app.mount(
        "/js",
        StaticFiles(directory=str(FRONTEND_DIR / "js")),
        name="js",
    )

    @app.get("/", tags=["Frontend"])
    def index():
        return FileResponse(str(FRONTEND_DIR / "index.html"))

    @app.get("/estudantes.html", tags=["Frontend"])
    def pagina_estudantes():
        return FileResponse(str(FRONTEND_DIR / "estudantes.html"))

    @app.get("/estudante.html", tags=["Frontend"])
    def pagina_estudante():
        return FileResponse(str(FRONTEND_DIR / "estudante.html"))
    
    app.mount(
        "/",
        StaticFiles(directory=str(FRONTEND_DIR)),
        name="frontend",
    )


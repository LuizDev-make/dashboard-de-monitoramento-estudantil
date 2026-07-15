"""
Repositório de acompanhamentos — acesso centralizado às tabelas
acompanhamentos e acompanhamentos_funcionarios.

Campos calculados (probabilidade_risco, classificacao_risco, z_score)
NUNCA são editáveis diretamente — só via recálculo automático.
"""
from datetime import datetime
from backend.database import get_db
from backend.services.auditoria import registrar_alteracao


# Campos que podem ser editados por funcionários
CAMPOS_EDITAVEIS = {
    "funcionario_responsavel",
    "prioridade_manual",
    "situacao_atendimento",
    "observacao",
    "encaminhamento",
    "data_prevista_contato",
    "ultimo_contato",
    "estudante_contatado",
    "acao_realizada",
}

# Campos protegidos — só o sistema pode alterar via recálculo
CAMPOS_PROTEGIDOS = {
    "probabilidade_risco",
    "classificacao_risco",
    "z_score",
    "media_global",
    "media_semestre",
    "frequencia_media",
    "reprovacoes",
    "reprovacoes_sucessivas",
    "percentual_integralizacao",
}


def buscar_acompanhamento_funcionario(
    estudante_id: int, db_path=None
) -> dict | None:
    """Busca o acompanhamento administrativo de um estudante.

    Returns:
        Dicionário com dados do acompanhamento ou None.
    """
    with get_db(db_path) as conn:
        cursor = conn.execute(
            "SELECT * FROM acompanhamentos_funcionarios WHERE estudante_id = ?",
            (estudante_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def criar_acompanhamento_funcionario(
    estudante_id: int,
    dados: dict,
    usuario: str = "sistema",
    db_path=None,
) -> int:
    """Cria um novo registro de acompanhamento administrativo.

    Args:
        estudante_id: ID do estudante.
        dados: Dicionário com campos editáveis.
        usuario: Usuário responsável pela criação.

    Returns:
        ID do registro criado.
    """
    # Filtra apenas campos permitidos
    dados_filtrados = {k: v for k, v in dados.items() if k in CAMPOS_EDITAVEIS}
    dados_filtrados["estudante_id"] = estudante_id
    dados_filtrados["data_criacao"] = datetime.now().isoformat()
    dados_filtrados["data_atualizacao"] = datetime.now().isoformat()

    colunas = ", ".join(dados_filtrados.keys())
    placeholders = ", ".join(["?"] * len(dados_filtrados))

    with get_db(db_path) as conn:
        cursor = conn.execute(
            f"INSERT INTO acompanhamentos_funcionarios ({colunas}) VALUES ({placeholders})",
            list(dados_filtrados.values()),
        )
        novo_id = cursor.lastrowid

    # Registra na auditoria
    for campo, valor in dados_filtrados.items():
        if campo not in ("estudante_id", "data_criacao", "data_atualizacao"):
            registrar_alteracao(
                "acompanhamentos_funcionarios",
                str(novo_id),
                campo,
                None,
                valor,
                usuario,
                db_path,
            )

    return novo_id


def atualizar_acompanhamento_funcionario(
    estudante_id: int,
    dados: dict,
    usuario: str = "sistema",
    db_path=None,
) -> bool:
    """Atualiza o acompanhamento administrativo de um estudante.

    Apenas campos editáveis são aceitos. Campos protegidos são ignorados.
    Toda alteração é registrada na auditoria.

    Args:
        estudante_id: ID do estudante.
        dados: Dicionário com campos a atualizar.
        usuario: Usuário responsável.

    Returns:
        True se o registro foi atualizado, False se não existir.
    """
    # Verifica se campos protegidos foram enviados
    campos_proibidos = set(dados.keys()) & CAMPOS_PROTEGIDOS
    if campos_proibidos:
        raise ValueError(
            f"Os seguintes campos são protegidos e não podem ser editados "
            f"manualmente: {campos_proibidos}. Eles só podem ser alterados "
            f"via recálculo automático do modelo."
        )

    # Filtra apenas campos permitidos
    dados_filtrados = {k: v for k, v in dados.items() if k in CAMPOS_EDITAVEIS}
    if not dados_filtrados:
        return False

    # Busca valores anteriores para auditoria
    registro_atual = buscar_acompanhamento_funcionario(estudante_id, db_path)
    if not registro_atual:
        return False

    dados_filtrados["data_atualizacao"] = datetime.now().isoformat()

    sets = ", ".join([f"{k} = ?" for k in dados_filtrados.keys()])

    with get_db(db_path) as conn:
        conn.execute(
            f"UPDATE acompanhamentos_funcionarios SET {sets} WHERE estudante_id = ?",
            list(dados_filtrados.values()) + [estudante_id],
        )

    # Registra alterações na auditoria
    for campo, valor_novo in dados_filtrados.items():
        if campo == "data_atualizacao":
            continue
        valor_anterior = registro_atual.get(campo)
        if str(valor_anterior) != str(valor_novo):
            registrar_alteracao(
                "acompanhamentos_funcionarios",
                str(estudante_id),
                campo,
                valor_anterior,
                valor_novo,
                usuario,
                db_path,
            )

    return True


def listar_acompanhamentos_pendentes(
    limite: int = 50, offset: int = 0, db_path=None
) -> list[dict]:
    """Lista acompanhamentos pendentes ou em andamento.

    Returns:
        Lista de acompanhamentos com dados do estudante.
    """
    with get_db(db_path) as conn:
        cursor = conn.execute(
            """
            SELECT af.*, e.nome, e.matricula, c.nome as curso_nome
            FROM acompanhamentos_funcionarios af
            JOIN estudantes e ON af.estudante_id = e.id
            LEFT JOIN cursos c ON e.curso_id = c.id
            WHERE af.situacao_atendimento IN ('pendente', 'em_andamento')
            ORDER BY af.prioridade_manual DESC, af.data_criacao ASC
            LIMIT ? OFFSET ?
            """,
            (limite, offset),
        )
        return [dict(row) for row in cursor.fetchall()]

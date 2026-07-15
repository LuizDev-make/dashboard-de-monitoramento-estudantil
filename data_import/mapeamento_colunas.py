"""
Mapeamento de colunas para importação de dados externos.

Define o mapeamento entre nomes de colunas de arquivos externos
e os nomes internos do sistema. Permite que arquivos de diferentes
instituições sejam importados sem alteração manual de código.
"""

# Mapeamento padrão: chave = nome interno, valor = lista de nomes externos aceitos
MAPEAMENTO_COLUNAS = {
    "matricula": ["matricula", "matrícula", "mat", "registro", "ra", "código_aluno"],
    "nome": ["nome", "nome_completo", "nome_aluno", "estudante"],
    "telefone": ["telefone", "tel", "celular", "fone", "contato"],
    "sexo": ["sexo", "genero", "gênero", "sex"],
    "data_nascimento": ["data_nascimento", "dt_nasc", "nascimento", "data_nasc"],
    "cep": ["cep", "codigo_postal", "código_postal", "zip"],
    "curso": ["curso", "nome_curso", "curso_nome", "programa"],
    "curso_codigo": ["curso_codigo", "cod_curso", "código_curso"],
    "ano_ingresso": ["ano_ingresso", "ano_entrada", "ingresso_ano"],
    "semestre_ingresso": ["semestre_ingresso", "sem_ingresso", "ingresso_semestre"],
    "situacao": ["situacao", "situação", "status", "sit"],
    "media_global": ["media_global", "média_global", "mg", "cra", "coeficiente"],
    "media_semestre": ["media_semestre", "média_semestre", "ms"],
    "frequencia_media": ["frequencia_media", "frequência_média", "freq", "frequencia"],
    "disciplinas_cursadas": ["disciplinas_cursadas", "disc_cursadas", "qtd_disciplinas"],
    "disciplinas_aprovadas": ["disciplinas_aprovadas", "disc_aprovadas", "aprovacoes"],
    "reprovacoes": ["reprovacoes", "reprovações", "repr", "qtd_reprovacoes"],
    "trancamentos": ["trancamentos", "tranc", "qtd_trancamentos"],
    "periodo_curricular": ["periodo_curricular", "período", "periodo", "semestre_curso"],
}

# Colunas obrigatórias para importação
COLUNAS_OBRIGATORIAS = ["matricula", "nome"]

# Colunas opcionais mas recomendadas
COLUNAS_RECOMENDADAS = [
    "curso", "media_global", "frequencia_media",
    "disciplinas_cursadas", "disciplinas_aprovadas",
]


def mapear_colunas(colunas_externas: list[str]) -> dict[str, str]:
    """Mapeia colunas de um arquivo externo para nomes internos.

    Args:
        colunas_externas: Lista de nomes de colunas do arquivo importado.

    Returns:
        Dicionário {coluna_externa: coluna_interna} para colunas reconhecidas.
    """
    mapeamento = {}
    colunas_lower = {c.lower().strip(): c for c in colunas_externas}

    for nome_interno, aliases in MAPEAMENTO_COLUNAS.items():
        for alias in aliases:
            if alias.lower() in colunas_lower:
                mapeamento[colunas_lower[alias.lower()]] = nome_interno
                break

    return mapeamento


def verificar_colunas_obrigatorias(
    mapeamento: dict[str, str],
) -> tuple[bool, list[str]]:
    """Verifica se todas as colunas obrigatórias foram mapeadas.

    Args:
        mapeamento: Dicionário de mapeamento {externa: interna}.

    Returns:
        Tupla (sucesso, colunas_faltantes).
    """
    colunas_internas = set(mapeamento.values())
    faltantes = [c for c in COLUNAS_OBRIGATORIAS if c not in colunas_internas]
    return len(faltantes) == 0, faltantes

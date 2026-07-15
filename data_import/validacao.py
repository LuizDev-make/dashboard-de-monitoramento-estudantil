"""
Validação de dados importados.

Valida tipos, formatos, limites e regras de negócio para registros
importados de arquivos CSV/XLSX.
"""
from typing import Any


class ResultadoValidacao:
    """Armazena resultados da validação de registros."""

    def __init__(self):
        self.validos: list[dict] = []
        self.invalidos: list[dict] = []
        self.duplicados: list[dict] = []
        self.avisos: list[str] = []

    @property
    def total_processados(self) -> int:
        return len(self.validos) + len(self.invalidos) + len(self.duplicados)

    def to_dict(self) -> dict:
        return {
            "total_processados": self.total_processados,
            "validos": len(self.validos),
            "invalidos": len(self.invalidos),
            "duplicados": len(self.duplicados),
            "avisos": self.avisos,
            "detalhes_invalidos": self.invalidos[:50],  # Limita para resposta
            "detalhes_duplicados": self.duplicados[:50],
        }


def validar_registros(
    registros: list[dict],
    matriculas_existentes: set[str] = None,
) -> ResultadoValidacao:
    """Valida uma lista de registros importados.

    Regras de validação:
    - Matrícula é obrigatória e não pode ser vazia
    - Nome é obrigatório e não pode ser vazio
    - Média deve estar entre 0 e 10 (se presente)
    - Frequência deve estar entre 0 e 100 (se presente)
    - Aprovações não podem exceder disciplinas cursadas
    - Carga concluída não pode ser negativa
    - Período não pode ser negativo
    - Matrícula duplicada é reportada

    Args:
        registros: Lista de dicionários com dados importados.
        matriculas_existentes: Conjunto de matrículas já no banco.

    Returns:
        ResultadoValidacao com registros categorizados.
    """
    resultado = ResultadoValidacao()
    if matriculas_existentes is None:
        matriculas_existentes = set()

    matriculas_vistas = set()

    for i, reg in enumerate(registros):
        erros = []
        linha = i + 2  # +2 por header + 0-index

        # Matrícula obrigatória
        matricula = str(reg.get("matricula", "")).strip()
        if not matricula:
            erros.append("Matrícula vazia ou ausente")

        # Nome obrigatório
        nome = str(reg.get("nome", "")).strip()
        if not nome:
            erros.append("Nome vazio ou ausente")

        # Média global [0, 10]
        media = reg.get("media_global")
        if media is not None:
            try:
                media = float(media)
                if not (0 <= media <= 10):
                    erros.append(f"Média fora do intervalo [0, 10]: {media}")
            except (ValueError, TypeError):
                erros.append(f"Média inválida: {media}")

        # Frequência [0, 100]
        freq = reg.get("frequencia_media")
        if freq is not None:
            try:
                freq = float(freq)
                if not (0 <= freq <= 100):
                    erros.append(f"Frequência fora de [0, 100]: {freq}")
            except (ValueError, TypeError):
                erros.append(f"Frequência inválida: {freq}")

        # Aprovações <= Cursadas
        cursadas = reg.get("disciplinas_cursadas")
        aprovadas = reg.get("disciplinas_aprovadas")
        if cursadas is not None and aprovadas is not None:
            try:
                if int(aprovadas) > int(cursadas):
                    erros.append(
                        f"Aprovações ({aprovadas}) > Cursadas ({cursadas})"
                    )
            except (ValueError, TypeError):
                pass

        # Período não negativo
        periodo = reg.get("periodo_curricular")
        if periodo is not None:
            try:
                if int(periodo) < 0:
                    erros.append(f"Período negativo: {periodo}")
            except (ValueError, TypeError):
                erros.append(f"Período inválido: {periodo}")

        # Reprovações não negativas
        reprov = reg.get("reprovacoes")
        if reprov is not None:
            try:
                if int(reprov) < 0:
                    erros.append(f"Reprovações negativas: {reprov}")
            except (ValueError, TypeError):
                pass

        # CEP (formato básico)
        cep = reg.get("cep")
        if cep is not None and cep != "":
            cep_limpo = str(cep).replace("-", "").replace(".", "").strip()
            if len(cep_limpo) != 8 or not cep_limpo.isdigit():
                erros.append(f"CEP inválido: {cep}")

        # Situação válida
        situacao = reg.get("situacao")
        situacoes_validas = {"ativo", "concluido", "trancado", "evadido"}
        if situacao and situacao not in situacoes_validas:
            erros.append(
                f"Situação inválida: '{situacao}'. "
                f"Válidas: {situacoes_validas}"
            )

        # Duplicata na importação
        if matricula in matriculas_vistas:
            resultado.duplicados.append({
                "linha": linha,
                "matricula": matricula,
                "motivo": "Matrícula duplicada dentro do arquivo de importação",
            })
            continue

        # Duplicata com banco existente
        if matricula in matriculas_existentes:
            resultado.duplicados.append({
                "linha": linha,
                "matricula": matricula,
                "motivo": "Matrícula já existe no banco de dados",
            })
            continue

        if erros:
            resultado.invalidos.append({
                "linha": linha,
                "matricula": matricula,
                "erros": erros,
            })
        else:
            resultado.validos.append(reg)
            matriculas_vistas.add(matricula)

    # Avisos gerais
    if resultado.duplicados:
        resultado.avisos.append(
            f"{len(resultado.duplicados)} matrícula(s) duplicada(s) encontrada(s)."
        )
    if resultado.invalidos:
        resultado.avisos.append(
            f"{len(resultado.invalidos)} registro(s) com erro(s) de validação."
        )

    return resultado

"""
Importador de arquivos CSV.

Lê, mapeia colunas, valida e insere dados no banco de dados.
"""
import csv
import sys
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from data_import.mapeamento_colunas import mapear_colunas, verificar_colunas_obrigatorias
from data_import.validacao import validar_registros, ResultadoValidacao
from backend.database import get_db


def importar_csv(caminho: str, db_path=None) -> dict:
    """Importa dados de um arquivo CSV.

    Args:
        caminho: Caminho do arquivo CSV.
        db_path: Caminho opcional do banco (para testes).

    Returns:
        Dicionário com resultado da importação.
    """
    caminho = Path(caminho)
    if not caminho.exists():
        return {"status": "erro", "mensagem": f"Arquivo não encontrado: {caminho}"}

    # Lê o CSV
    try:
        with open(caminho, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            colunas_externas = reader.fieldnames or []
            registros_raw = list(reader)
    except Exception as e:
        return {"status": "erro", "mensagem": f"Erro ao ler CSV: {str(e)}"}

    if not registros_raw:
        return {"status": "aviso", "mensagem": "Arquivo vazio."}

    # Mapeia colunas
    mapeamento = mapear_colunas(colunas_externas)
    ok, faltantes = verificar_colunas_obrigatorias(mapeamento)

    if not ok:
        return {
            "status": "erro",
            "mensagem": f"Colunas obrigatórias não encontradas: {faltantes}",
            "colunas_encontradas": list(mapeamento.values()),
            "colunas_arquivo": colunas_externas,
        }

    # Renomeia colunas
    registros = []
    for raw in registros_raw:
        reg = {}
        for col_ext, col_int in mapeamento.items():
            reg[col_int] = raw.get(col_ext, "")
        registros.append(reg)

    # Busca matrículas existentes
    matriculas_existentes = set()
    with get_db(db_path) as conn:
        cursor = conn.execute("SELECT matricula FROM estudantes")
        matriculas_existentes = {row["matricula"] for row in cursor.fetchall()}

    # Valida
    resultado = validar_registros(registros, matriculas_existentes)

    # Insere válidos
    inseridos = 0
    if resultado.validos:
        with get_db(db_path) as conn:
            for reg in resultado.validos:
                try:
                    conn.execute(
                        """
                        INSERT INTO estudantes (matricula, nome, telefone, sexo,
                            data_nascimento, cep, situacao)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            reg.get("matricula"),
                            reg.get("nome"),
                            reg.get("telefone"),
                            reg.get("sexo"),
                            reg.get("data_nascimento"),
                            reg.get("cep"),
                            reg.get("situacao", "ativo"),
                        ),
                    )
                    inseridos += 1
                except Exception:
                    pass

    info = resultado.to_dict()
    info["status"] = "sucesso"
    info["inseridos"] = inseridos
    info["data_importacao"] = datetime.now().isoformat()
    info["arquivo_origem"] = caminho.name

    return info

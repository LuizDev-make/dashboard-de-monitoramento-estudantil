"""
Rotas de importação de dados — endpoints para upload CSV/XLSX.
"""
import os
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException

router = APIRouter(prefix="/api", tags=["Importações"])


@router.post("/importacoes")
async def importar_dados(arquivo: UploadFile = File(...)):
    """Importa dados de estudantes a partir de CSV ou XLSX.

    O arquivo é validado, processado e os dados válidos são inseridos
    no banco. Registros inválidos são reportados sem apagar dados anteriores.
    """
    # Valida extensão
    nome = arquivo.filename or ""
    extensao = os.path.splitext(nome)[1].lower()

    if extensao not in (".csv", ".xlsx"):
        raise HTTPException(
            status_code=400,
            detail="Formato não suportado. Envie um arquivo CSV ou XLSX.",
        )

    # Salva arquivo temporário
    conteudo = await arquivo.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=extensao) as tmp:
        tmp.write(conteudo)
        tmp_path = tmp.name

    try:
        if extensao == ".csv":
            from data_import.importador_csv import importar_csv
            resultado = importar_csv(tmp_path)
        else:
            from data_import.importador_excel import importar_excel
            resultado = importar_excel(tmp_path)

        return resultado

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar importação: {str(e)}",
        )
    finally:
        os.unlink(tmp_path)

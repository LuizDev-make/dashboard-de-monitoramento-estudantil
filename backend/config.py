"""
Configuração do sistema de monitoramento UFRPE.
Carrega variáveis de ambiente e expõe constantes de configuração.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Diretório raiz do projeto (monitoramento-ufrpe/)
BASE_DIR = Path(__file__).resolve().parent.parent

# Carrega .env se existir
load_dotenv(BASE_DIR / ".env")

# Banco de dados
DATABASE_PATH = BASE_DIR / "database" / "monitoramento.db"

# Schema SQL
SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"

# Modelo treinado
MODEL_PATH = BASE_DIR / "models" / "modelo_risco.joblib"

# Debug
DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

# Chave secreta
SECRET_KEY = os.getenv("SECRET_KEY", "dev-key-insegura-trocar-em-producao")

# Integração ViaCEP
VIACEP_ENABLED = os.getenv("VIACEP_ENABLED", "false").lower() in ("true", "1", "yes")

# Coordenadas da UFRPE (campus Dois Irmãos, Recife-PE)
UFRPE_LATITUDE = float(os.getenv("UFRPE_LATITUDE", "-8.0143"))
UFRPE_LONGITUDE = float(os.getenv("UFRPE_LONGITUDE", "-34.9506"))

# Semente para reprodutibilidade
SEMENTE = 2026

# Limiares de classificação de risco
LIMIAR_ATENCAO = 0.70   # 70% → Atenção
LIMIAR_PERIGO = 0.85    # 85% → Perigo

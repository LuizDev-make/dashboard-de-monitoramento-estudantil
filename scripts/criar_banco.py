"""
Script para criação do banco de dados SQLite.
Executa o schema.sql e valida a criação das tabelas.

Uso:
    python scripts/criar_banco.py
"""
import sys
import sqlite3
from pathlib import Path

# Adiciona o diretório raiz ao path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.config import DATABASE_PATH, SCHEMA_PATH


TABELAS_ESPERADAS = [
    "cursos",
    "estudantes",
    "periodos_letivos",
    "acompanhamentos",
    "disciplinas",
    "matriculas_disciplinas",
    "acompanhamentos_funcionarios",
    "historico_edicoes",
]


def criar_banco():
    """Cria o banco de dados executando o schema SQL."""
    print("=" * 60)
    print("  CRIAÇÃO DO BANCO DE DADOS")
    print("=" * 60)

    # Garante que o diretório existe
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Lê o schema
    print(f"\n📄 Lendo schema: {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    # Cria/recria o banco
    print(f"🗄️  Criando banco: {DATABASE_PATH}")
    conn = sqlite3.connect(str(DATABASE_PATH))
    try:
        conn.executescript(schema_sql)
        conn.commit()
        print("✅ Schema executado com sucesso!")
    finally:
        conn.close()

    # Valida as tabelas criadas
    print("\n📋 Validando tabelas criadas:")
    conn = sqlite3.connect(str(DATABASE_PATH))
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tabelas_criadas = [row[0] for row in cursor.fetchall()]
    conn.close()

    todas_ok = True
    for tabela in TABELAS_ESPERADAS:
        if tabela in tabelas_criadas:
            print(f"   ✅ {tabela}")
        else:
            print(f"   ❌ {tabela} — NÃO ENCONTRADA")
            todas_ok = False

    # Resumo
    print(f"\n📊 Total de tabelas encontradas: {len(tabelas_criadas)}")
    print(f"   Esperadas: {len(TABELAS_ESPERADAS)}")

    if todas_ok:
        print("\n🎉 Banco de dados criado e validado com sucesso!")
    else:
        print("\n⚠️  Algumas tabelas não foram criadas. Verifique o schema.sql.")
        sys.exit(1)

    return DATABASE_PATH


if __name__ == "__main__":
    criar_banco()

"""
Testes para importação de dados (CSV).

Cobre:
- Importação com matrícula duplicada
- Importação com colunas faltantes
- Validação de registros
"""
import pytest
import sys
import os
import csv
import tempfile
import sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from data_import.validacao import validar_registros
from data_import.mapeamento_colunas import mapear_colunas, verificar_colunas_obrigatorias
from backend.config import SCHEMA_PATH


@pytest.fixture
def banco_temporario(tmp_path):
    """Cria um banco SQLite temporário para testes."""
    db_path = tmp_path / "test.db"
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = f.read()
    conn = sqlite3.connect(str(db_path))
    conn.executescript(schema)
    conn.close()
    return db_path


@pytest.fixture
def csv_valido(tmp_path):
    """Cria um CSV válido para testes."""
    caminho = tmp_path / "valido.csv"
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["matricula", "nome", "telefone", "sexo"])
        writer.writeheader()
        writer.writerow({"matricula": "20210001", "nome": "Ana Silva", "telefone": "(81) 99999-0001", "sexo": "F"})
        writer.writerow({"matricula": "20210002", "nome": "Carlos Santos", "telefone": "(81) 99999-0002", "sexo": "M"})
    return str(caminho)


@pytest.fixture
def csv_com_duplicata(tmp_path):
    """Cria um CSV com matrícula duplicada dentro do próprio arquivo."""
    caminho = tmp_path / "duplicata.csv"
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["matricula", "nome"])
        writer.writeheader()
        writer.writerow({"matricula": "20210001", "nome": "Ana Silva"})
        writer.writerow({"matricula": "20210001", "nome": "Ana Silva Duplicada"})  # Duplicata
        writer.writerow({"matricula": "20210003", "nome": "João Oliveira"})
    return str(caminho)


# ---------------------------------------------------------------
# Testes de validação de registros
# ---------------------------------------------------------------
class TestValidacaoRegistros:
    def test_registros_validos(self):
        registros = [
            {"matricula": "20210001", "nome": "Ana"},
            {"matricula": "20210002", "nome": "Carlos"},
        ]
        resultado = validar_registros(registros)
        assert len(resultado.validos) == 2
        assert len(resultado.invalidos) == 0

    def test_matricula_vazia(self):
        registros = [{"matricula": "", "nome": "Ana"}]
        resultado = validar_registros(registros)
        assert len(resultado.invalidos) == 1

    def test_nome_vazio(self):
        registros = [{"matricula": "20210001", "nome": ""}]
        resultado = validar_registros(registros)
        assert len(resultado.invalidos) == 1

    def test_media_fora_do_intervalo(self):
        registros = [
            {"matricula": "20210001", "nome": "Ana", "media_global": "11.0"},
        ]
        resultado = validar_registros(registros)
        assert len(resultado.invalidos) == 1
        assert any("Média" in e for e in resultado.invalidos[0]["erros"])

    def test_frequencia_fora_do_intervalo(self):
        registros = [
            {"matricula": "20210001", "nome": "Ana", "frequencia_media": "150"},
        ]
        resultado = validar_registros(registros)
        assert len(resultado.invalidos) == 1

    def test_aprovacoes_maior_que_cursadas(self):
        registros = [
            {"matricula": "20210001", "nome": "Ana",
             "disciplinas_cursadas": "3", "disciplinas_aprovadas": "5"},
        ]
        resultado = validar_registros(registros)
        assert len(resultado.invalidos) == 1

    def test_duplicata_dentro_do_arquivo(self):
        registros = [
            {"matricula": "20210001", "nome": "Ana"},
            {"matricula": "20210001", "nome": "Ana Duplicada"},
        ]
        resultado = validar_registros(registros)
        assert len(resultado.validos) == 1
        assert len(resultado.duplicados) == 1

    def test_duplicata_com_banco(self):
        """Detecta duplicata com matrícula já existente no banco."""
        registros = [
            {"matricula": "EXISTENTE", "nome": "Fulano"},
        ]
        resultado = validar_registros(registros, matriculas_existentes={"EXISTENTE"})
        assert len(resultado.duplicados) == 1
        assert len(resultado.validos) == 0

    def test_periodo_negativo(self):
        registros = [
            {"matricula": "20210001", "nome": "Ana", "periodo_curricular": "-1"},
        ]
        resultado = validar_registros(registros)
        assert len(resultado.invalidos) == 1

    def test_cep_invalido(self):
        registros = [
            {"matricula": "20210001", "nome": "Ana", "cep": "123"},
        ]
        resultado = validar_registros(registros)
        assert len(resultado.invalidos) == 1

    def test_situacao_invalida(self):
        registros = [
            {"matricula": "20210001", "nome": "Ana", "situacao": "invalido"},
        ]
        resultado = validar_registros(registros)
        assert len(resultado.invalidos) == 1


# ---------------------------------------------------------------
# Testes de mapeamento de colunas
# ---------------------------------------------------------------
class TestMapeamentoColunas:
    def test_mapeamento_padrao(self):
        colunas = ["matricula", "nome", "telefone"]
        mapa = mapear_colunas(colunas)
        assert "matricula" in mapa
        assert mapa["matricula"] == "matricula"

    def test_mapeamento_alias(self):
        colunas = ["matrícula", "nome_completo", "cel"]
        mapa = mapear_colunas(colunas)
        assert "matrícula" in mapa
        assert mapa["matrícula"] == "matricula"

    def test_colunas_obrigatorias_presentes(self):
        mapa = {"matricula": "matricula", "nome": "nome"}
        ok, faltantes = verificar_colunas_obrigatorias(mapa)
        assert ok
        assert len(faltantes) == 0

    def test_colunas_obrigatorias_faltando(self):
        mapa = {"telefone": "telefone"}
        ok, faltantes = verificar_colunas_obrigatorias(mapa)
        assert not ok
        assert "matricula" in faltantes

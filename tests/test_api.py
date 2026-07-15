"""
Testes para a API REST.

Cobre:
- Endpoint de estudantes (listagem)
- Endpoint de cursos
- Endpoint de dashboard
- Edição de acompanhamento
- Inserção/leitura no SQLite
"""
import pytest
import sys
import sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient
from backend.config import SCHEMA_PATH


@pytest.fixture
def banco_teste(tmp_path, monkeypatch):
    """Cria um banco de testes com dados mínimos."""
    db_path = tmp_path / "test_api.db"

    # Cria o schema
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = f.read()
    conn = sqlite3.connect(str(db_path))
    conn.executescript(schema)

    # Insere dados de teste
    conn.execute(
        "INSERT INTO cursos (id, nome, codigo, campus, duracao_periodos, ativo) "
        "VALUES (1, 'Ciência da Computação', 'CC', 'Dois Irmãos', 10, 1)"
    )
    conn.execute(
        "INSERT INTO periodos_letivos (id, ano, semestre) VALUES (1, 2024, 1)"
    )
    conn.execute(
        "INSERT INTO estudantes (id, matricula, nome, telefone, sexo, curso_id, "
        "ano_ingresso, semestre_ingresso, situacao) "
        "VALUES (1, '20240001', 'Maria Teste', '(81) 99999-0001', 'F', 1, 2024, 1, 'ativo')"
    )
    conn.execute(
        "INSERT INTO acompanhamentos (id, estudante_id, periodo_letivo_id, "
        "periodo_curricular, media_global, media_semestre, frequencia_media, "
        "disciplinas_cursadas, disciplinas_aprovadas, reprovacoes, "
        "reprovacoes_sucessivas, percentual_integralizacao, distancia_km, "
        "probabilidade_risco, classificacao_risco) "
        "VALUES (1, 1, 1, 1, 7.5, 7.0, 85.0, 5, 4, 1, 0, 10.0, 5.0, 0.35, 'OK')"
    )
    conn.commit()
    conn.close()

    # Monkey-patch o DATABASE_PATH para usar o banco de teste
    monkeypatch.setattr("backend.config.DATABASE_PATH", db_path)
    monkeypatch.setattr("backend.database.DATABASE_PATH", db_path)

    return db_path


@pytest.fixture
def client(banco_teste):
    """Cria um TestClient do FastAPI."""
    from backend.app import app
    return TestClient(app)


# ---------------------------------------------------------------
# Testes de cursos
# ---------------------------------------------------------------
class TestCursos:
    def test_listar_cursos(self, client):
        response = client.get("/api/cursos")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["nome"] == "Ciência da Computação"


# ---------------------------------------------------------------
# Testes de estudantes
# ---------------------------------------------------------------
class TestEstudantes:
    def test_listar_estudantes(self, client):
        response = client.get("/api/estudantes")
        assert response.status_code == 200
        data = response.json()
        assert "estudantes" in data
        assert "total" in data
        assert data["total"] >= 1

    def test_buscar_estudante(self, client):
        response = client.get("/api/estudantes/1")
        assert response.status_code == 200
        data = response.json()
        assert data["estudante"]["matricula"] == "20240001"

    def test_estudante_nao_encontrado(self, client):
        response = client.get("/api/estudantes/99999")
        assert response.status_code == 404

    def test_historico_estudante(self, client):
        response = client.get("/api/estudantes/1/historico")
        assert response.status_code == 200
        data = response.json()
        assert "historico" in data
        assert len(data["historico"]) >= 1

    def test_filtro_por_busca(self, client):
        response = client.get("/api/estudantes?busca=Maria")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1


# ---------------------------------------------------------------
# Testes de dashboard
# ---------------------------------------------------------------
class TestDashboard:
    def test_resumo(self, client):
        response = client.get("/api/dashboard/resumo")
        assert response.status_code == 200
        data = response.json()
        assert "total_estudantes" in data
        assert data["total_estudantes"] >= 1

    def test_histograma(self, client):
        response = client.get("/api/dashboard/histograma?indicador=media_global")
        assert response.status_code == 200
        data = response.json()
        assert "indicador" in data
        assert data["indicador"] == "media_global"

    def test_histograma_invalido(self, client):
        response = client.get("/api/dashboard/histograma?indicador=invalido")
        assert response.status_code == 400

    def test_evolucao(self, client):
        response = client.get("/api/dashboard/evolucao?indicador=media_global")
        assert response.status_code == 200
        data = response.json()
        assert "periodos" in data


# ---------------------------------------------------------------
# Testes de acompanhamentos
# ---------------------------------------------------------------
class TestAcompanhamentos:
    def test_criar_acompanhamento(self, client):
        response = client.post(
            "/api/acompanhamentos?estudante_id=1",
            json={
                "funcionario_responsavel": "Prof. Silva",
                "situacao_atendimento": "pendente",
                "observacao": "Estudante precisa de atenção.",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data

    def test_atualizar_acompanhamento(self, client):
        # Primeiro cria
        client.post(
            "/api/acompanhamentos?estudante_id=1",
            json={"funcionario_responsavel": "Prof. Silva"},
        )
        # Depois atualiza
        response = client.put(
            "/api/acompanhamentos/1",
            json={
                "situacao_atendimento": "em_andamento",
                "observacao": "Contato realizado.",
            },
        )
        assert response.status_code == 200

    def test_buscar_acompanhamento(self, client):
        client.post(
            "/api/acompanhamentos?estudante_id=1",
            json={"funcionario_responsavel": "Prof. Silva"},
        )
        response = client.get("/api/acompanhamentos/1")
        assert response.status_code == 200


# ---------------------------------------------------------------
# Testes de inserção/leitura SQLite
# ---------------------------------------------------------------
class TestSQLite:
    def test_insercao_leitura(self, banco_teste):
        conn = sqlite3.connect(str(banco_teste))
        conn.row_factory = sqlite3.Row

        # Insere novo estudante
        conn.execute(
            "INSERT INTO estudantes (matricula, nome, curso_id, ano_ingresso, "
            "semestre_ingresso, situacao) VALUES (?, ?, ?, ?, ?, ?)",
            ("20240099", "Teste SQLite", 1, 2024, 1, "ativo"),
        )
        conn.commit()

        # Lê de volta
        cursor = conn.execute(
            "SELECT * FROM estudantes WHERE matricula = '20240099'"
        )
        row = cursor.fetchone()
        assert row is not None
        assert row["nome"] == "Teste SQLite"
        conn.close()


# ---------------------------------------------------------------
# Testes de auditoria
# ---------------------------------------------------------------
class TestAuditoria:
    def test_listar_auditoria(self, client):
        response = client.get("/api/auditoria")
        assert response.status_code == 200

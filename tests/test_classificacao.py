"""
Testes para classificação de risco e cálculo de distância.

Cobre:
- Classificação nos limites exatos: 69,99% (OK), 70% (Atenção),
  84,99% (Atenção), 85% (Perigo), 100% (Perigo)
- Validação de probabilidade fora de [0,1]
- Fatores de alerta
- Cálculo de distância (Haversine)
"""
import pytest
import sys
import math
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.services.risco import classificar_risco, gerar_fatores_alerta
from backend.services.distancia import distancia_haversine, distancia_ate_ufrpe


# ---------------------------------------------------------------
# Testes de classificação de risco — limites exatos
# ---------------------------------------------------------------
class TestClassificarRisco:
    def test_ok_baixo(self):
        """0% deve ser OK."""
        resultado = classificar_risco(0.0)
        assert resultado["classificacao"] == "OK"
        assert resultado["cor"] == "verde"
        assert resultado["probabilidade_percentual"] == 0.0

    def test_ok_limite_superior(self):
        """69,99% deve ser OK."""
        resultado = classificar_risco(0.6999)
        assert resultado["classificacao"] == "OK"
        assert resultado["cor"] == "verde"
        assert resultado["probabilidade_percentual"] == 69.99

    def test_atencao_limite_inferior(self):
        """70,00% deve ser Atenção (regra de fronteira)."""
        resultado = classificar_risco(0.70)
        assert resultado["classificacao"] == "Atenção"
        assert resultado["cor"] == "amarelo"
        assert resultado["probabilidade_percentual"] == 70.0

    def test_atencao_meio(self):
        """77,50% deve ser Atenção."""
        resultado = classificar_risco(0.775)
        assert resultado["classificacao"] == "Atenção"
        assert resultado["cor"] == "amarelo"

    def test_atencao_limite_superior(self):
        """84,99% deve ser Atenção."""
        resultado = classificar_risco(0.8499)
        assert resultado["classificacao"] == "Atenção"
        assert resultado["cor"] == "amarelo"
        assert resultado["probabilidade_percentual"] == 84.99

    def test_perigo_limite_inferior(self):
        """85,00% deve ser Perigo (regra de fronteira)."""
        resultado = classificar_risco(0.85)
        assert resultado["classificacao"] == "Perigo"
        assert resultado["cor"] == "vermelho"
        assert resultado["probabilidade_percentual"] == 85.0

    def test_perigo_alto(self):
        """95% deve ser Perigo."""
        resultado = classificar_risco(0.95)
        assert resultado["classificacao"] == "Perigo"
        assert resultado["cor"] == "vermelho"

    def test_perigo_maximo(self):
        """100% deve ser Perigo."""
        resultado = classificar_risco(1.0)
        assert resultado["classificacao"] == "Perigo"
        assert resultado["cor"] == "vermelho"
        assert resultado["probabilidade_percentual"] == 100.0

    def test_probabilidade_negativa(self):
        """Probabilidade negativa deve gerar ValueError."""
        with pytest.raises(ValueError):
            classificar_risco(-0.01)

    def test_probabilidade_acima_de_1(self):
        """Probabilidade acima de 1 deve gerar ValueError."""
        with pytest.raises(ValueError):
            classificar_risco(1.01)

    def test_probabilidade_none(self):
        """Probabilidade None deve gerar ValueError."""
        with pytest.raises(ValueError):
            classificar_risco(None)


# ---------------------------------------------------------------
# Testes de fatores de alerta
# ---------------------------------------------------------------
class TestFatoresAlerta:
    def test_estudante_sem_alertas(self):
        """Estudante com bom desempenho não deve gerar alertas."""
        registro = {
            "media_global": 7.5,
            "media_semestre": 7.0,
            "frequencia_media": 90.0,
            "reprovacoes_sucessivas": 0,
            "trancamentos": 0,
            "percentual_integralizacao": 50.0,
            "periodo_curricular": 5,
            "duracao_periodos": 10,
            "variacao_media": 0.5,
            "taxa_reprovacao": 0.1,
            "distancia_km": 10.0,
        }
        alertas = gerar_fatores_alerta(registro)
        assert len(alertas) == 0

    def test_media_global_baixa(self):
        registro = {"media_global": 3.5}
        alertas = gerar_fatores_alerta(registro)
        assert any("Média global" in a for a in alertas)

    def test_frequencia_baixa(self):
        registro = {"frequencia_media": 60.0}
        alertas = gerar_fatores_alerta(registro)
        assert any("Frequência" in a for a in alertas)

    def test_reprovacoes_sucessivas(self):
        registro = {"reprovacoes_sucessivas": 3}
        alertas = gerar_fatores_alerta(registro)
        assert any("Reprovações sucessivas" in a for a in alertas)

    def test_queda_media(self):
        registro = {"variacao_media": -1.5}
        alertas = gerar_fatores_alerta(registro)
        assert any("Queda" in a for a in alertas)

    def test_multiplos_alertas(self):
        """Estudante em situação crítica deve gerar múltiplos alertas."""
        registro = {
            "media_global": 3.0,
            "media_semestre": 2.5,
            "frequencia_media": 50.0,
            "reprovacoes_sucessivas": 4,
            "trancamentos": 3,
            "variacao_media": -2.0,
            "taxa_reprovacao": 0.8,
            "distancia_km": 50.0,
            "percentual_integralizacao": 10.0,
            "periodo_curricular": 5,
            "duracao_periodos": 10,
        }
        alertas = gerar_fatores_alerta(registro)
        assert len(alertas) >= 5


# ---------------------------------------------------------------
# Testes de distância Haversine
# ---------------------------------------------------------------
class TestDistanciaHaversine:
    def test_mesmo_ponto(self):
        """Distância entre o mesmo ponto deve ser 0."""
        d = distancia_haversine(-8.0143, -34.9506, -8.0143, -34.9506)
        assert d == pytest.approx(0.0, abs=1e-6)

    def test_distancia_conhecida(self):
        """Distância Recife → João Pessoa (~120 km)."""
        d = distancia_haversine(-8.0476, -34.8770, -7.1195, -34.8450)
        assert 100 < d < 120

    def test_distancia_curta(self):
        """Distância curta dentro de Recife (~5-15 km)."""
        d = distancia_haversine(-8.0143, -34.9506, -8.0576, -34.8710)
        assert 5 < d < 15

    def test_distancia_simetrica(self):
        """d(A,B) deve ser igual a d(B,A)."""
        d1 = distancia_haversine(-8.0, -35.0, -7.0, -34.0)
        d2 = distancia_haversine(-7.0, -34.0, -8.0, -35.0)
        assert d1 == pytest.approx(d2)

    def test_distancia_ate_ufrpe(self):
        """Distância de um ponto próximo à UFRPE."""
        d = distancia_ate_ufrpe(-8.0143, -34.9506)
        assert d == pytest.approx(0.0, abs=1e-6)

    def test_distancia_positiva(self):
        """Qualquer distância entre pontos diferentes deve ser positiva."""
        d = distancia_haversine(-8.0, -35.0, -8.1, -35.1)
        assert d > 0

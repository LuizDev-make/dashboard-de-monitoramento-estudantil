"""
Testes para o serviço de estatísticas.

Cobre:
- Taxa de aprovação e reprovação
- Cálculo de z-score
- Coeficiente de variação
- Maior sequência de reprovações
- Percentual de integralização
- Resumo de distribuição
- Escore acadêmico composto
- Variação da média
"""
import pytest
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path para importar backend
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.services.estatisticas import (
    taxa_aprovacao,
    taxa_reprovacao,
    variacao_media,
    coeficiente_variacao,
    calcular_z_score,
    calcular_z_scores_grupo,
    maior_sequencia_reprovacoes,
    percentual_integralizacao,
    atraso_curricular,
    resumo_distribuicao,
    escore_academico_composto,
    evolucao_longitudinal,
    calcular_estatisticas_turma,
)


# ---------------------------------------------------------------
# Testes de taxa de aprovação
# ---------------------------------------------------------------
class TestTaxaAprovacao:
    def test_taxa_normal(self):
        assert taxa_aprovacao(3, 5) == pytest.approx(0.6)

    def test_taxa_100_porcento(self):
        assert taxa_aprovacao(5, 5) == pytest.approx(1.0)

    def test_taxa_zero(self):
        assert taxa_aprovacao(0, 5) == pytest.approx(0.0)

    def test_cursadas_zero(self):
        assert taxa_aprovacao(0, 0) == 0.0

    def test_cursadas_negativo(self):
        assert taxa_aprovacao(0, -1) == 0.0


# ---------------------------------------------------------------
# Testes de taxa de reprovação
# ---------------------------------------------------------------
class TestTaxaReprovacao:
    def test_taxa_normal(self):
        assert taxa_reprovacao(2, 5) == pytest.approx(0.4)

    def test_taxa_zero(self):
        assert taxa_reprovacao(0, 5) == pytest.approx(0.0)

    def test_cursadas_zero(self):
        assert taxa_reprovacao(0, 0) == 0.0

    def test_taxa_total(self):
        assert taxa_reprovacao(5, 5) == pytest.approx(1.0)


# ---------------------------------------------------------------
# Testes de z-score
# ---------------------------------------------------------------
class TestZScore:
    def test_z_score_media(self):
        """Z-score de valor igual à média deve ser 0."""
        assert calcular_z_score(5.0, 5.0, 1.0) == pytest.approx(0.0)

    def test_z_score_acima(self):
        """Z-score de valor 1 desvio acima da média deve ser 1."""
        assert calcular_z_score(6.0, 5.0, 1.0) == pytest.approx(1.0)

    def test_z_score_abaixo(self):
        """Z-score de valor 2 desvios abaixo da média deve ser -2."""
        assert calcular_z_score(3.0, 5.0, 1.0) == pytest.approx(-2.0)

    def test_z_score_desvio_zero(self):
        """Z-score com desvio zero deve retornar None."""
        assert calcular_z_score(5.0, 5.0, 0.0) is None

    def test_z_score_desvio_none(self):
        assert calcular_z_score(5.0, 5.0, None) is None

    def test_z_scores_grupo(self):
        """Z-scores de um grupo devem ter média ~0."""
        valores = [2.0, 4.0, 6.0, 8.0, 10.0]
        z_scores = calcular_z_scores_grupo(valores)
        assert len(z_scores) == 5
        # Média dos z-scores deve ser aproximadamente 0
        z_validos = [z for z in z_scores if z is not None]
        media_z = sum(z_validos) / len(z_validos)
        assert media_z == pytest.approx(0.0, abs=1e-10)

    def test_z_scores_grupo_insuficiente(self):
        """Grupo com menos de 2 valores deve retornar Nones."""
        assert calcular_z_scores_grupo([5.0]) == [None]

    def test_z_scores_grupo_vazio(self):
        assert calcular_z_scores_grupo([]) == []


# ---------------------------------------------------------------
# Testes de variação da média
# ---------------------------------------------------------------
class TestVariacaoMedia:
    def test_variacao_positiva(self):
        assert variacao_media(7.0, 5.0) == pytest.approx(2.0)

    def test_variacao_negativa(self):
        assert variacao_media(4.0, 6.0) == pytest.approx(-2.0)

    def test_variacao_sem_anterior(self):
        assert variacao_media(5.0, None) is None

    def test_variacao_zero(self):
        assert variacao_media(5.0, 5.0) == pytest.approx(0.0)


# ---------------------------------------------------------------
# Testes de coeficiente de variação
# ---------------------------------------------------------------
class TestCoeficienteVariacao:
    def test_cv_normal(self):
        cv = coeficiente_variacao([10.0, 10.0, 10.0])
        assert cv == pytest.approx(0.0)

    def test_cv_variavel(self):
        cv = coeficiente_variacao([2.0, 4.0, 6.0, 8.0])
        assert cv is not None
        assert cv > 0

    def test_cv_vazio(self):
        assert coeficiente_variacao([]) is None

    def test_cv_media_zero(self):
        assert coeficiente_variacao([0.0, 0.0]) is None


# ---------------------------------------------------------------
# Testes de maior sequência de reprovações
# ---------------------------------------------------------------
class TestMaiorSequenciaReprovacoes:
    def test_sem_reprovacoes(self):
        assert maior_sequencia_reprovacoes(["aprovado", "aprovado"]) == 0

    def test_uma_reprovacao(self):
        assert maior_sequencia_reprovacoes(["reprovado_nota"]) == 1

    def test_sequencia_interrompida(self):
        situacoes = [
            "reprovado_nota", "reprovado_falta", "aprovado",
            "reprovado_nota", "reprovado_nota", "reprovado_nota"
        ]
        assert maior_sequencia_reprovacoes(situacoes) == 3

    def test_lista_vazia(self):
        assert maior_sequencia_reprovacoes([]) == 0

    def test_trancado_interrompe(self):
        situacoes = ["reprovado_nota", "trancado", "reprovado_nota"]
        assert maior_sequencia_reprovacoes(situacoes) == 1


# ---------------------------------------------------------------
# Testes de percentual de integralização
# ---------------------------------------------------------------
class TestPercentualIntegralizacao:
    def test_metade(self):
        assert percentual_integralizacao(1500, 3000) == pytest.approx(50.0)

    def test_completo(self):
        assert percentual_integralizacao(3000, 3000) == pytest.approx(100.0)

    def test_excedente(self):
        """Não deve ultrapassar 100%."""
        assert percentual_integralizacao(3500, 3000) == pytest.approx(100.0)

    def test_zero(self):
        assert percentual_integralizacao(0, 3000) == pytest.approx(0.0)

    def test_ch_total_zero(self):
        assert percentual_integralizacao(100, 0) == 0.0


# ---------------------------------------------------------------
# Testes de atraso curricular
# ---------------------------------------------------------------
class TestAtrasoCurricular:
    def test_sem_atraso(self):
        assert atraso_curricular(3, 3) == 0

    def test_com_atraso(self):
        assert atraso_curricular(5, 3) == 2

    def test_adiantado(self):
        """Adiantado não deve gerar atraso negativo."""
        assert atraso_curricular(3, 5) == 0


# ---------------------------------------------------------------
# Testes de resumo de distribuição
# ---------------------------------------------------------------
class TestResumoDistribuicao:
    def test_resumo_normal(self):
        valores = [1.0, 2.0, 3.0, 4.0, 5.0]
        resumo = resumo_distribuicao(valores)
        assert resumo["media"] == pytest.approx(3.0)
        assert resumo["mediana"] == pytest.approx(3.0)
        assert resumo["minimo"] == pytest.approx(1.0)
        assert resumo["maximo"] == pytest.approx(5.0)
        assert resumo["contagem"] == 5
        assert resumo["q1"] is not None
        assert resumo["q3"] is not None
        assert resumo["iqr"] == pytest.approx(resumo["q3"] - resumo["q1"])

    def test_resumo_vazio(self):
        resumo = resumo_distribuicao([])
        assert resumo["media"] is None
        assert resumo["contagem"] == 0


# ---------------------------------------------------------------
# Testes de escore acadêmico composto
# ---------------------------------------------------------------
class TestEscoreAcademicoComposto:
    def test_escore_neutro(self):
        """Z-scores zerados devem resultar em escore ~0."""
        z_scores = {
            "z_media_global": 0.0,
            "z_frequencia": 0.0,
            "z_taxa_aprovacao": 0.0,
            "z_integralizacao": 0.0,
            "z_reprovacoes_sucessivas": 0.0,
        }
        escore = escore_academico_composto(z_scores)
        assert escore == pytest.approx(0.0)

    def test_escore_vazio(self):
        assert escore_academico_composto({}) is None

    def test_escore_parcial(self):
        """Deve calcular mesmo com dados parciais."""
        z_scores = {"z_media_global": 1.0, "z_frequencia": 1.0}
        escore = escore_academico_composto(z_scores)
        assert escore is not None
        assert escore > 0


# ---------------------------------------------------------------
# Testes de evolução longitudinal
# ---------------------------------------------------------------
class TestEvolucaoLongitudinal:
    def test_evolucao_basica(self):
        registros = [
            {"periodo_letivo": "2023.1", "media_global": 6.0, "media_semestre": 6.5,
             "frequencia_media": 85.0, "reprovacoes": 1, "percentual_integralizacao": 20.0,
             "probabilidade_risco": 0.3},
            {"periodo_letivo": "2023.2", "media_global": 6.2, "media_semestre": 6.8,
             "frequencia_media": 88.0, "reprovacoes": 0, "percentual_integralizacao": 35.0,
             "probabilidade_risco": 0.2},
        ]
        evolucao = evolucao_longitudinal(registros)
        assert len(evolucao["periodos"]) == 2
        assert evolucao["medias_globais"] == [6.0, 6.2]
        assert evolucao["reprovacoes"] == [1, 0]

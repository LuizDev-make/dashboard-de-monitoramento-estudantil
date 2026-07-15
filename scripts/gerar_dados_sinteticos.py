"""
Gerador de dados sintéticos para o Sistema de Monitoramento Acadêmico UFRPE.

Gera estudantes, cursos, períodos letivos, disciplinas e trajetórias acadêmicas
completas com notas, frequências e indicadores de risco. Insere os dados no
banco SQLite e exporta um CSV para treinamento de modelos.

Uso:
    python scripts/gerar_dados_sinteticos.py
"""

import sys
import math
import sqlite3
import csv
from pathlib import Path
from datetime import date, timedelta

import numpy as np

# ---------------------------------------------------------------------------
# Configuração de caminhos
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.config import DATABASE_PATH

# ---------------------------------------------------------------------------
# Constantes de reprodutibilidade e geolocalização
# ---------------------------------------------------------------------------
SEMENTE = 2026
rng = np.random.default_rng(SEMENTE)

UFRPE_LAT = -8.0143
UFRPE_LON = -34.9506

# ---------------------------------------------------------------------------
# Dados de referência — cursos (nome, código, campus, duração, ativo)
# ---------------------------------------------------------------------------
CURSOS = [
    ('Agronomia', 'AGR', 'Dois Irmãos', 10, 1),
    ('Ciência da Computação', 'CC', 'Dois Irmãos', 10, 1),
    ('Medicina Veterinária', 'VET', 'Dois Irmãos', 10, 1),
    ('Zootecnia', 'ZOO', 'Dois Irmãos', 10, 1),
    ('Engenharia Agrícola e Ambiental', 'EAA', 'Dois Irmãos', 10, 1),
    ('Licenciatura em Matemática', 'MAT', 'Dois Irmãos', 8, 1),
]

# ---------------------------------------------------------------------------
# Nomes fictícios brasileiros para geração de estudantes
# ---------------------------------------------------------------------------
NOMES_MASCULINOS = [
    'Lucas', 'Pedro', 'Gabriel', 'Rafael', 'Matheus', 'João', 'Gustavo',
    'Felipe', 'André', 'Bruno', 'Carlos', 'Daniel', 'Eduardo', 'Fernando',
    'Henrique', 'Igor', 'José', 'Leonardo', 'Marcos', 'Nicolas', 'Paulo',
    'Ricardo', 'Thiago', 'Vinícius', 'Caio', 'Diego', 'Erick', 'Fábio',
    'Guilherme', 'Hugo', 'Ivan', 'Jorge', 'Kleber', 'Leandro', 'Miguel',
    'Nathan', 'Otávio', 'Patrick', 'Raul', 'Samuel', 'Tiago', 'Ulisses',
    'Victor', 'Wesley', 'Yuri', 'Alex', 'Bernardo', 'Cláudio', 'Davi',
    'Emanuel',
]

NOMES_FEMININOS = [
    'Ana', 'Beatriz', 'Camila', 'Daniela', 'Eduarda', 'Fernanda', 'Gabriela',
    'Helena', 'Isabela', 'Juliana', 'Karen', 'Larissa', 'Mariana', 'Natália',
    'Olivia', 'Patrícia', 'Rafaela', 'Sabrina', 'Tatiana', 'Valéria',
    'Amanda', 'Bianca', 'Carolina', 'Diana', 'Elaine', 'Flávia', 'Giovanna',
    'Heloísa', 'Ingrid', 'Jéssica', 'Letícia', 'Monique', 'Nathália',
    'Paloma', 'Raquel', 'Simone', 'Tainá', 'Vitória', 'Yasmin', 'Aline',
    'Bruna', 'Cíntia', 'Débora', 'Érica', 'Franciele', 'Gisele', 'Hanna',
    'Isis', 'Joana', 'Luana',
]

SOBRENOMES = [
    'Silva', 'Santos', 'Oliveira', 'Souza', 'Pereira', 'Costa', 'Rodrigues',
    'Almeida', 'Nascimento', 'Lima', 'Araújo', 'Fernandes', 'Carvalho',
    'Gomes', 'Martins', 'Rocha', 'Ribeiro', 'Alves', 'Monteiro', 'Mendes',
    'Barros', 'Freitas', 'Barbosa', 'Pinto', 'Moura', 'Cavalcanti', 'Dias',
    'Castro', 'Campos', 'Cardoso', 'Teixeira', 'Correia', 'Vieira', 'Nunes',
    'Batista', 'Moreira', 'Lopes', 'Machado', 'Bezerra', 'Melo',
]

# ---------------------------------------------------------------------------
# Prefixos de disciplinas por curso
# ---------------------------------------------------------------------------
PREFIXOS_DISCIPLINAS = {
    'AGR': [
        'Fitotecnia', 'Solos', 'Irrigação', 'Fisiologia Vegetal',
        'Genética Agrícola', 'Entomologia', 'Fitopatologia', 'Mecanização',
        'Agroecologia', 'Climatologia', 'Extensão Rural', 'Bioquímica',
    ],
    'CC': [
        'Programação', 'Estrutura de Dados', 'Banco de Dados',
        'Engenharia de Software', 'Redes de Computadores', 'Inteligência Artificial',
        'Sistemas Operacionais', 'Computação Gráfica', 'Teoria da Computação',
        'Compiladores', 'Álgebra Linear', 'Cálculo',
    ],
    'VET': [
        'Anatomia Animal', 'Fisiologia Animal', 'Patologia Veterinária',
        'Clínica Médica', 'Cirurgia Veterinária', 'Parasitologia',
        'Farmacologia', 'Reprodução Animal', 'Zoonoses', 'Nutrição Animal',
        'Anestesiologia', 'Diagnóstico por Imagem',
    ],
    'ZOO': [
        'Nutrição de Ruminantes', 'Melhoramento Genético', 'Forragicultura',
        'Produção de Aves', 'Produção de Suínos', 'Bovinocultura',
        'Aquicultura', 'Bioclimatologia', 'Tecnologia de Produtos',
        'Manejo de Pastagens', 'Apicultura', 'Economia Rural',
    ],
    'EAA': [
        'Hidráulica', 'Topografia', 'Gestão Ambiental', 'Saneamento',
        'Mecânica dos Solos', 'Recursos Hídricos', 'Construções Rurais',
        'Energias Renováveis', 'Hidrologia', 'Drenagem', 'Geotecnia',
        'Controle Ambiental',
    ],
    'MAT': [
        'Cálculo Diferencial', 'Álgebra Abstrata', 'Geometria Analítica',
        'Análise Real', 'Estatística', 'Didática da Matemática',
        'Probabilidade', 'Geometria Euclidiana', 'Fundamentos de Matemática',
        'Equações Diferenciais', 'Lógica Matemática', 'Topologia',
    ],
}


# ===================================================================
# Funções auxiliares
# ===================================================================

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula a distância em km entre dois pontos usando a fórmula de Haversine."""
    R = 6371.0  # Raio médio da Terra em km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def clamp(valor: float, minimo: float, maximo: float) -> float:
    """Limita um valor entre mínimo e máximo."""
    return max(minimo, min(maximo, valor))


# ===================================================================
# Função principal
# ===================================================================

def main():
    """Função principal: gera dados sintéticos e popula o banco SQLite."""
    print("=" * 65)
    print("  🎓 GERADOR DE DADOS SINTÉTICOS — MONITORAMENTO UFRPE")
    print("=" * 65)

    # ------------------------------------------------------------------
    # 1. Conexão com o banco de dados
    # ------------------------------------------------------------------
    print(f"\n🔌 Conectando ao banco: {DATABASE_PATH}")
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    cursor = conn.cursor()

    # Limpar todas as tabelas na ordem correta (filhas antes das pais)
    print("\n🧹 Limpando tabelas existentes...")
    for tabela in [
        'matriculas_disciplinas', 'acompanhamentos',
        'acompanhamentos_funcionarios', 'historico_edicoes',
        'estudantes', 'disciplinas', 'periodos_letivos', 'cursos',
    ]:
        cursor.execute(f"DELETE FROM {tabela}")
    conn.commit()
    print("   ✅ Tabelas limpas")

    # ------------------------------------------------------------------
    # 2. Inserção de cursos
    # ------------------------------------------------------------------
    print("\n📚 Inserindo cursos...")
    for nome, codigo, campus, duracao, ativo in CURSOS:
        cursor.execute(
            "INSERT INTO cursos (nome, codigo, campus, duracao_periodos, ativo) "
            "VALUES (?, ?, ?, ?, ?)",
            (nome, codigo, campus, duracao, ativo),
        )
    conn.commit()

    # Mapa de curso_id por código
    cursor.execute("SELECT id, codigo, nome, duracao_periodos FROM cursos")
    cursos_db = cursor.fetchall()
    curso_por_id = {row[0]: {'codigo': row[1], 'nome': row[2], 'duracao': row[3]} for row in cursos_db}
    curso_ids = [row[0] for row in cursos_db]
    print(f"   ✅ {len(cursos_db)} cursos inseridos")

    # ------------------------------------------------------------------
    # 3. Inserção de períodos letivos (2016.1 a 2025.2)
    # ------------------------------------------------------------------
    print("\n📅 Inserindo períodos letivos...")

    for ano in range(2016, 2026):
        for sem in (1, 2):
            if sem == 1:
                dt_inicio = f"{ano}-03-01"
                dt_fim = f"{ano}-07-15"
            else:
                dt_inicio = f"{ano}-08-01"
                dt_fim = f"{ano}-12-15"
            cursor.execute(
                "INSERT INTO periodos_letivos (ano, semestre, data_inicio, data_fim) "
                "VALUES (?, ?, ?, ?)",
                (ano, sem, dt_inicio, dt_fim),
            )
    conn.commit()

    # Mapa de período letivo
    cursor.execute("SELECT id, ano, semestre FROM periodos_letivos ORDER BY ano, semestre")
    periodos_db = cursor.fetchall()
    periodo_map = {(row[1], row[2]): row[0] for row in periodos_db}
    periodos_ordenados = [(row[1], row[2]) for row in periodos_db]
    print(f"   ✅ {len(periodos_db)} períodos letivos inseridos")

    # ------------------------------------------------------------------
    # 4. Geração de disciplinas
    # ------------------------------------------------------------------
    print("\n📖 Gerando disciplinas...")

    cargas_possiveis = [30, 45, 60, 90]
    disc_contador = 0

    # Armazena disciplinas por (curso_id, periodo_recomendado)
    disciplinas_por_curso_periodo = {}

    for cid in curso_ids:
        info = curso_por_id[cid]
        codigo_curso = info['codigo']
        duracao = info['duracao']
        prefixos = PREFIXOS_DISCIPLINAS[codigo_curso]

        for periodo_rec in range(1, duracao + 1):
            # Cada período recomendado recebe ~8 disciplinas
            n_disc = int(rng.integers(7, 10))  # 7 a 9 disciplinas
            disciplinas_periodo = []
            for j in range(n_disc):
                # Combina prefixo com numeração
                prefixo = prefixos[j % len(prefixos)]
                sufixo_num = periodo_rec
                nome_disc = f"{prefixo} {sufixo_num}" if j < len(prefixos) else f"{prefixo} Avançada {sufixo_num}"
                codigo_disc = f"{codigo_curso}{periodo_rec:02d}{j + 1:02d}"
                carga = int(rng.choice(cargas_possiveis))

                cursor.execute(
                    "INSERT INTO disciplinas (codigo, nome, carga_horaria, periodo_recomendado, curso_id) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (codigo_disc, nome_disc, carga, periodo_rec, cid),
                )
                disc_id = cursor.lastrowid
                disciplinas_periodo.append((disc_id, carga))
                disc_contador += 1

            disciplinas_por_curso_periodo[(cid, periodo_rec)] = disciplinas_periodo

    conn.commit()
    print(f"   ✅ {disc_contador} disciplinas inseridas")

    # ------------------------------------------------------------------
    # 5. Geração de estudantes
    # ------------------------------------------------------------------
    print("\n👩‍🎓 Gerando estudantes...")
    N_ESTUDANTES = 2200

    # Distribuição de anos de ingresso (mais recentes = mais alunos)
    anos_ingresso = list(range(2016, 2024))  # 2016 a 2023
    pesos_anos = np.array([1, 1, 2, 2, 3, 3, 4, 5], dtype=float)
    pesos_anos = pesos_anos / pesos_anos.sum()



    matriculas_geradas = set()
    estudantes_info = []  # Lista para manter informações dos estudantes gerados

    for i in range(N_ESTUDANTES):
        # Curso distribuído uniformemente
        curso_idx_rel = int(rng.integers(0, len(curso_ids)))
        curso_id = curso_ids[curso_idx_rel]

        # Ano e semestre de ingresso
        ano_ingresso = int(rng.choice(anos_ingresso, p=pesos_anos))
        semestre_ingresso = int(rng.choice([1, 2], p=[0.7, 0.3]))

        # Matrícula única
        seq = 1
        while True:
            matricula = f"{ano_ingresso}{curso_idx_rel:02d}{seq:04d}"
            if matricula not in matriculas_geradas:
                matriculas_geradas.add(matricula)
                break
            seq += 1

        # Sexo (60% M, 40% F)
        sexo = 'M' if rng.random() < 0.6 else 'F'

        # Nome
        if sexo == 'M':
            primeiro_nome = str(rng.choice(NOMES_MASCULINOS))
        else:
            primeiro_nome = str(rng.choice(NOMES_FEMININOS))
        sobrenome1 = str(rng.choice(SOBRENOMES))
        sobrenome2 = str(rng.choice(SOBRENOMES))
        nome = f"{primeiro_nome} {sobrenome1} {sobrenome2}"

        # Telefone no formato (81) 9XXXX-XXXX
        tel_parte1 = rng.integers(1000, 10000)
        tel_parte2 = rng.integers(1000, 10000)
        telefone = f"(81) 9{tel_parte1:04d}-{tel_parte2:04d}"

        # Data de nascimento (entre 17 e 25 anos antes do ingresso)
        idade_ingresso = int(rng.integers(17, 26))  # 17 a 25
        ano_nascimento = ano_ingresso - idade_ingresso
        mes_nascimento = int(rng.integers(1, 13))
        dia_nascimento = int(rng.integers(1, 29))  # Evita problemas com fevereiro
        data_nascimento = f"{ano_nascimento:04d}-{mes_nascimento:02d}-{dia_nascimento:02d}"

        # CEP
        d1 = int(rng.integers(0, 10))
        d2 = int(rng.integers(100, 999))
        d3 = int(rng.integers(100, 999))
        cep = f"5{d1}{d2:03d}-{d3:03d}"

        # Coordenadas (região metropolitana de Recife)
        latitude = float(rng.uniform(-8.20, -7.85))
        longitude = float(rng.uniform(-35.10, -34.85))

        # Distância até a UFRPE
        distancia_km = haversine(latitude, longitude, UFRPE_LAT, UFRPE_LON)

        cursor.execute(
            "INSERT INTO estudantes "
            "(matricula, nome, telefone, sexo, data_nascimento, cep, "
            " latitude, longitude, curso_id, ano_ingresso, semestre_ingresso, situacao) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (matricula, nome, telefone, sexo, data_nascimento, cep,
             latitude, longitude, curso_id, ano_ingresso, semestre_ingresso, 'ativo'),
        )
        est_id = cursor.lastrowid

        # Perfil acadêmico base do estudante (talento centralizado em ~0.63)
        # beta(5,3) produz distribuição assimétrica à direita → mais alunos bons
        talento = float(rng.beta(5, 3))
        dedicacao = float(rng.beta(4, 3))
        base_freq = 0.65 + 0.30 * dedicacao + float(rng.normal(0, 0.03))

        estudantes_info.append({
            'id': est_id,
            'matricula': matricula,
            'nome': nome,
            'curso_id': curso_id,
            'ano_ingresso': ano_ingresso,
            'semestre_ingresso': semestre_ingresso,
            'talento': talento,
            'dedicacao': dedicacao,
            'base_freq': base_freq,
            'distancia_km': distancia_km,
            'latitude': latitude,
            'longitude': longitude,
        })

    conn.commit()
    print(f"   ✅ {N_ESTUDANTES} estudantes inseridos")

    # ------------------------------------------------------------------
    # 6. Geração de trajetórias acadêmicas
    # ------------------------------------------------------------------
    print("\n📊 Gerando trajetórias acadêmicas (acompanhamentos + matrículas)...")

    # Carga horária total por curso (soma de todas as disciplinas)
    ch_total_curso = {}
    for cid in curso_ids:
        duracao = curso_por_id[cid]['duracao']
        total = 0
        for p in range(1, duracao + 1):
            for _, ch in disciplinas_por_curso_periodo.get((cid, p), []):
                total += ch
        ch_total_curso[cid] = total

    # Estrutura para coleta de registros CSV
    registros_csv = []

    # Contadores de progresso
    total_acomp = 0
    total_mat_disc = 0

    for idx_est, est in enumerate(estudantes_info):
        if (idx_est + 1) % 500 == 0:
            print(f"   🔄 Processando estudante {idx_est + 1}/{N_ESTUDANTES}...")

        est_id = est['id']
        curso_id = est['curso_id']
        ano_ing = est['ano_ingresso']
        sem_ing = est['semestre_ingresso']
        talento = est['talento']
        dedicacao = est['dedicacao']
        base_freq = est['base_freq']
        distancia_km = est['distancia_km']
        duracao_curso = curso_por_id[curso_id]['duracao']
        nome_curso = curso_por_id[curso_id]['nome']
        ch_total = ch_total_curso[curso_id]

        # Histórico acumulado do estudante
        todas_notas = []
        ch_aprovada_total = 0
        resultados_historico = []  # Lista de situações por disciplina para reprovações sucessivas
        periodo_curricular_atual = 1
        evadiu = False
        ultimo_periodo_ativo = None
        semestres_trancados_consecutivos = 0

        # Determinar períodos letivos em que o estudante pode estar matriculado
        periodo_inicio_idx = periodos_ordenados.index((ano_ing, sem_ing))

        # Limite: até 2025.2 ou até duracao_curso + 2 semestres extras
        max_semestres = duracao_curso + 4  # Margem para atrasos

        for sem_offset in range(max_semestres):
            idx_per = periodo_inicio_idx + sem_offset
            if idx_per >= len(periodos_ordenados):
                break  # Não há mais períodos disponíveis

            ano_per, sem_per = periodos_ordenados[idx_per]
            periodo_letivo_id = periodo_map[(ano_per, sem_per)]

            # Chance de evasão (~4% por semestre após o 2º período)
            if sem_offset >= 2 and rng.random() < 0.04:
                evadiu = True
                break

            # Chance de pular um semestre (~5%)
            if sem_offset > 0 and rng.random() < 0.05:
                continue

            # Determinar período curricular (geralmente sequencial, ~5% chance de gap)
            if sem_offset > 0 and rng.random() < 0.05:
                # Repete o período curricular (não avançou)
                pass
            elif sem_offset > 0:
                periodo_curricular_atual = min(periodo_curricular_atual + 1, duracao_curso)

            # Selecionar disciplinas para este semestre
            discs_disponiveis = disciplinas_por_curso_periodo.get(
                (curso_id, periodo_curricular_atual), []
            )
            if not discs_disponiveis:
                # Tenta pegar disciplinas de períodos adjacentes
                for p_adj in [periodo_curricular_atual - 1, periodo_curricular_atual + 1]:
                    if 1 <= p_adj <= duracao_curso:
                        discs_disponiveis = disciplinas_por_curso_periodo.get(
                            (curso_id, p_adj), []
                        )
                        if discs_disponiveis:
                            break
            if not discs_disponiveis:
                continue

            # Número de disciplinas: entre 4 e 7
            n_disc_semestre = int(clamp(rng.integers(4, 8), 1, len(discs_disponiveis)))
            indices = rng.choice(len(discs_disponiveis), size=n_disc_semestre, replace=False)
            discs_selecionadas = [discs_disponiveis[i] for i in indices]

            # Gerar resultados para cada disciplina
            notas_semestre = []
            freqs_semestre = []
            ch_matriculada = 0
            ch_concluida = 0
            n_aprovadas = 0
            n_reprovacoes = 0
            n_rep_falta = 0
            n_rep_nota = 0
            n_trancamentos = 0

            for disc_id, disc_ch in discs_selecionadas:
                ch_matriculada += disc_ch

                # ~3% chance de trancamento na disciplina
                if rng.random() < 0.03:
                    situacao_disc = 'trancado'
                    nota_disc = None
                    freq_disc = None
                    n_trancamentos += 1
                    resultados_historico.append('trancado')
                else:
                    # Gerar nota e frequência
                    # Fórmula ajustada para distribuição mais ampla de desempenho
                    nota_disc = float(clamp(
                        talento * 6.5 + dedicacao * 3.5 + rng.normal(0, 1.2),
                        0, 10
                    ))
                    freq_disc = float(clamp(
                        base_freq * 100 + rng.normal(0, 7),
                        0, 100
                    ))

                    # Determinar situação
                    if freq_disc < 75:
                        situacao_disc = 'reprovado_falta'
                        n_rep_falta += 1
                        n_reprovacoes += 1
                        resultados_historico.append('reprovado')
                    elif nota_disc < 5.0:
                        situacao_disc = 'reprovado_nota'
                        n_rep_nota += 1
                        n_reprovacoes += 1
                        resultados_historico.append('reprovado')
                    else:
                        situacao_disc = 'aprovado'
                        n_aprovadas += 1
                        ch_concluida += disc_ch
                        ch_aprovada_total += disc_ch
                        resultados_historico.append('aprovado')

                    notas_semestre.append(nota_disc)
                    freqs_semestre.append(freq_disc)

                # Inserir na tabela matriculas_disciplinas
                cursor.execute(
                    "INSERT INTO matriculas_disciplinas "
                    "(estudante_id, disciplina_id, periodo_letivo_id, nota, frequencia, situacao) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (est_id, disc_id, periodo_letivo_id,
                     round(nota_disc, 2) if nota_disc is not None else None,
                     round(freq_disc, 2) if freq_disc is not None else None,
                     situacao_disc),
                )
                total_mat_disc += 1

            # Calcular agregados do semestre
            disciplinas_cursadas = len(discs_selecionadas)
            media_semestre = float(np.mean(notas_semestre)) if notas_semestre else 0.0
            frequencia_media = float(np.mean(freqs_semestre)) if freqs_semestre else 0.0

            # Acumular notas para média global
            todas_notas.extend(notas_semestre)
            media_global = float(np.mean(todas_notas)) if todas_notas else 0.0

            # Percentual de integralização
            percentual_integralizacao = (ch_aprovada_total / ch_total * 100) if ch_total > 0 else 0.0

            # Reprovações sucessivas: maior sequência consecutiva de reprovações no histórico
            rep_sucessivas = 0
            streak_atual = 0
            for r in resultados_historico:
                if r == 'reprovado':
                    streak_atual += 1
                    rep_sucessivas = max(rep_sucessivas, streak_atual)
                else:
                    streak_atual = 0

            # Inserir acompanhamento no banco
            cursor.execute(
                "INSERT INTO acompanhamentos "
                "(estudante_id, periodo_letivo_id, periodo_curricular, "
                " media_global, media_semestre, disciplinas_cursadas, disciplinas_aprovadas, "
                " reprovacoes, reprovacoes_falta, reprovacoes_nota, reprovacoes_sucessivas, "
                " frequencia_media, carga_horaria_matriculada, carga_horaria_concluida, "
                " percentual_integralizacao, trancamentos, distancia_km, data_calculo) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, date('now'))",
                (est_id, periodo_letivo_id, periodo_curricular_atual,
                 round(media_global, 4), round(media_semestre, 4),
                 disciplinas_cursadas, n_aprovadas,
                 n_reprovacoes, n_rep_falta, n_rep_nota, rep_sucessivas,
                 round(frequencia_media, 4),
                 ch_matriculada, ch_concluida,
                 round(percentual_integralizacao, 4),
                 n_trancamentos, round(distancia_km, 4)),
            )
            total_acomp += 1
            ultimo_periodo_ativo = (ano_per, sem_per, idx_per)

            # Verificar trancamento consecutivo total
            if n_trancamentos == disciplinas_cursadas:
                semestres_trancados_consecutivos += 1
            else:
                semestres_trancados_consecutivos = 0

            # Calcular desfecho_risco para este registro
            # Logito calibrado para ~80% desfecho_risco=1 COM alto ruído (σ=1.2)
            # Alta taxa base → modelo prediz probabilidades altas em geral
            # Alto ruído → modelo não é perfeito → probabilidades se espalham
            # Resultado final após treinamento: distribuição nas 3 faixas (70/85%)
            logito = (
                1.8
                - 0.15 * media_global
                + 0.12 * (10 - media_semestre)
                - 0.008 * frequencia_media
                + 0.10 * n_reprovacoes
                + 0.15 * rep_sucessivas
                + 0.08 * n_trancamentos
                - 0.003 * percentual_integralizacao
                + 0.008 * distancia_km
                + float(rng.normal(0, 1.2))  # Ruído alto para espalhar probabilidades
            )
            probabilidade_real = 1 / (1 + np.exp(-logito))
            desfecho_risco = int(rng.binomial(1, float(probabilidade_real)))

            # Regras determinísticas RESTRITAS — apenas casos extremos
            # 1. Média do semestre criticamente baixa
            if media_semestre < 3.0:
                desfecho_risco = 1
            # 2. Nenhuma aprovação no semestre
            if n_aprovadas == 0 and disciplinas_cursadas > 0:
                desfecho_risco = 1
            # 3. Trancamento total do semestre
            if n_trancamentos == disciplinas_cursadas and disciplinas_cursadas > 0:
                desfecho_risco = 1

            # Período letivo formatado para o CSV
            periodo_letivo_str = f"{ano_per}.{sem_per}"

            # Coletar registro para CSV
            registros_csv.append({
                'matricula': est['matricula'],
                'nome': est['nome'],
                'curso': nome_curso,
                'periodo_letivo': periodo_letivo_str,
                'periodo_curricular': periodo_curricular_atual,
                'media_global': round(media_global, 4),
                'media_semestre': round(media_semestre, 4),
                'frequencia_media': round(frequencia_media, 4),
                'disciplinas_cursadas': disciplinas_cursadas,
                'disciplinas_aprovadas': n_aprovadas,
                'reprovacoes': n_reprovacoes,
                'reprovacoes_falta': n_rep_falta,
                'reprovacoes_nota': n_rep_nota,
                'reprovacoes_sucessivas': rep_sucessivas,
                'trancamentos': n_trancamentos,
                'percentual_integralizacao': round(percentual_integralizacao, 4),
                'carga_horaria_matriculada': ch_matriculada,
                'carga_horaria_concluida': ch_concluida,
                'distancia_km': round(distancia_km, 4),
                'situacao': 'ativo',  # Será atualizado depois
                'desfecho_risco': desfecho_risco,
            })

        # Marcar evasão no desfecho do último registro se evadiu
        if evadiu and registros_csv:
            # Encontrar o último registro deste estudante e marcar risco
            for r in reversed(registros_csv):
                if r['matricula'] == est['matricula']:
                    r['desfecho_risco'] = 1
                    break

        # Guardar informações para atualização de situação
        est['ch_aprovada_total'] = ch_aprovada_total
        est['ch_total'] = ch_total
        est['evadiu'] = evadiu
        est['ultimo_periodo'] = ultimo_periodo_ativo
        est['semestres_trancados_consec'] = semestres_trancados_consecutivos
        est['media_global_final'] = float(np.mean(todas_notas)) if todas_notas else 0.0
        est['periodos_cursados'] = sum(
            1 for r in registros_csv if r['matricula'] == est['matricula']
        )

    conn.commit()
    print(f"   ✅ {total_acomp} registros de acompanhamento inseridos")
    print(f"   ✅ {total_mat_disc} matrículas em disciplinas inseridas")

    # ------------------------------------------------------------------
    # 7. Atualização de situação dos estudantes
    # ------------------------------------------------------------------
    print("\n🔄 Atualizando situação dos estudantes...")
    contagem_situacao = {'ativo': 0, 'concluido': 0, 'evadido': 0, 'trancado': 0}

    for est in estudantes_info:
        est_id = est['id']
        matricula = est['matricula']
        ch_aprovada = est.get('ch_aprovada_total', 0)
        ch_total = est.get('ch_total', 1)
        evadiu = est.get('evadiu', False)
        media_final = est.get('media_global_final', 0)
        trancados_consec = est.get('semestres_trancados_consec', 0)
        percentual = (ch_aprovada / ch_total * 100) if ch_total > 0 else 0

        # Determinar situação final
        periodos_cursados = est.get('periodos_cursados', 0)
        if percentual >= 50 and media_final >= 4.5 and periodos_cursados >= 6:
            situacao_final = 'concluido'
        elif evadiu:
            situacao_final = 'evadido'
        elif trancados_consec >= 2:
            situacao_final = 'trancado'
        else:
            situacao_final = 'ativo'

        # Ajuste probabilístico para atingir distribuição desejada
        # ~15% concluído, ~10-15% evadido, ~5% trancado
        if situacao_final == 'ativo':
            ajuste = rng.random()
            # Alunos antigos com bom desempenho → concluído
            if ajuste < 0.10 and percentual >= 30 and media_final >= 3.5:
                situacao_final = 'concluido'
            elif ajuste < 0.06 and periodos_cursados >= 8:
                situacao_final = 'concluido'
            elif 0.20 <= ajuste < 0.25:
                situacao_final = 'evadido'
            elif 0.25 <= ajuste < 0.30:
                situacao_final = 'trancado'

        cursor.execute(
            "UPDATE estudantes SET situacao = ? WHERE id = ?",
            (situacao_final, est_id),
        )
        contagem_situacao[situacao_final] += 1

        # Atualizar situação nos registros CSV deste estudante
        for r in registros_csv:
            if r['matricula'] == matricula:
                r['situacao'] = situacao_final

    conn.commit()

    for sit, qtd in contagem_situacao.items():
        pct = qtd / N_ESTUDANTES * 100
        print(f"   📌 {sit}: {qtd} ({pct:.1f}%)")

    # ------------------------------------------------------------------
    # 8. Exportação para CSV
    # ------------------------------------------------------------------
    print("\n💾 Exportando dados para CSV...")
    data_dir = ROOT_DIR / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Colunas do CSV
    colunas_csv = [
        'matricula', 'nome', 'curso', 'periodo_letivo', 'periodo_curricular',
        'media_global', 'media_semestre', 'frequencia_media',
        'disciplinas_cursadas', 'disciplinas_aprovadas',
        'reprovacoes', 'reprovacoes_falta', 'reprovacoes_nota',
        'reprovacoes_sucessivas', 'trancamentos',
        'percentual_integralizacao', 'carga_horaria_matriculada',
        'carga_horaria_concluida', 'distancia_km',
        'situacao', 'desfecho_risco',
    ]

    # Arquivo principal de dados sintéticos
    csv_path = data_dir / "dados_sinteticos.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=colunas_csv)
        writer.writeheader()
        writer.writerows(registros_csv)
    print(f"   ✅ {csv_path} — {len(registros_csv)} registros")

    # Modelo de importação com 3 linhas de exemplo
    modelo_path = data_dir / "modelo_importacao.csv"
    with open(modelo_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=colunas_csv)
        writer.writeheader()
        # Escreve 3 primeiros registros como exemplo
        for r in registros_csv[:3]:
            writer.writerow(r)
    print(f"   ✅ {modelo_path} — modelo com 3 exemplos")

    # ------------------------------------------------------------------
    # 9. Fechar conexão
    # ------------------------------------------------------------------
    conn.close()
    print("\n🔒 Conexão com o banco encerrada.")

    # ------------------------------------------------------------------
    # 10. Resumo de validação
    # ------------------------------------------------------------------
    print("\n" + "=" * 65)
    print("  📋 RESUMO DE VALIDAÇÃO")
    print("=" * 65)

    # Total de estudantes e registros
    matriculas_unicas = set(r['matricula'] for r in registros_csv)
    print(f"\n👥 Total de estudantes gerados: {N_ESTUDANTES}")
    print(f"   Matrículas únicas no CSV: {len(matriculas_unicas)}")
    print(f"📊 Total de registros de acompanhamento: {total_acomp}")

    # Distribuição de situação
    print("\n📌 Distribuição de situação:")
    for sit, qtd in sorted(contagem_situacao.items()):
        pct = qtd / N_ESTUDANTES * 100
        print(f"   {sit:>12s}: {qtd:>5d}  ({pct:5.1f}%)")

    # Distribuição de desfecho_risco
    total_risco_1 = sum(1 for r in registros_csv if r['desfecho_risco'] == 1)
    total_risco_0 = sum(1 for r in registros_csv if r['desfecho_risco'] == 0)
    n_total = len(registros_csv)
    pct_risco_1 = total_risco_1 / n_total * 100 if n_total > 0 else 0
    pct_risco_0 = total_risco_0 / n_total * 100 if n_total > 0 else 0

    print(f"\n🎯 Distribuição de desfecho_risco:")
    print(f"   Risco = 0 (sem risco):  {total_risco_0:>6d}  ({pct_risco_0:5.1f}%)")
    print(f"   Risco = 1 (em risco):   {total_risco_1:>6d}  ({pct_risco_1:5.1f}%)")

    # Verificação de que não é 0% nem 100%
    if 0 < pct_risco_1 < 100:
        print("   ✅ Desfecho balanceado — nem 0% nem 100%")
    else:
        print("   ⚠️  ATENÇÃO: Desfecho desbalanceado!")

    # Estatísticas descritivas das variáveis-chave
    medias_globais = [r['media_global'] for r in registros_csv]
    medias_semestre = [r['media_semestre'] for r in registros_csv]
    frequencias = [r['frequencia_media'] for r in registros_csv]
    distancias = [r['distancia_km'] for r in registros_csv]
    integralizacoes = [r['percentual_integralizacao'] for r in registros_csv]

    print(f"\n📈 Estatísticas descritivas:")
    print(f"   {'Variável':<30s} {'Média':>8s}  {'Desvio':>8s}")
    print(f"   {'-' * 48}")
    for nome_var, valores in [
        ('media_global', medias_globais),
        ('media_semestre', medias_semestre),
        ('frequencia_media', frequencias),
        ('distancia_km', distancias),
        ('percentual_integralizacao', integralizacoes),
    ]:
        arr = np.array(valores)
        print(f"   {nome_var:<30s} {arr.mean():>8.2f}  {arr.std():>8.2f}")

    print("\n" + "=" * 65)
    print("  🎉 GERAÇÃO DE DADOS CONCLUÍDA COM SUCESSO!")
    print("=" * 65)


if __name__ == '__main__':
    main()

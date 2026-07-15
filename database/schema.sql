-- =============================================================
-- Schema do banco de dados: Sistema de Monitoramento UFRPE
-- Banco: SQLite
-- =============================================================

-- Tabela de cursos
CREATE TABLE IF NOT EXISTS cursos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    codigo TEXT NOT NULL UNIQUE,
    campus TEXT NOT NULL DEFAULT 'Dois Irmãos',
    duracao_periodos INTEGER NOT NULL DEFAULT 10,
    ativo INTEGER NOT NULL DEFAULT 1
);

-- Tabela de estudantes
CREATE TABLE IF NOT EXISTS estudantes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    matricula TEXT NOT NULL UNIQUE,
    nome TEXT NOT NULL,
    telefone TEXT,
    sexo TEXT CHECK(sexo IN ('M', 'F', 'Outro')),
    data_nascimento TEXT,
    cep TEXT,
    latitude REAL,
    longitude REAL,
    curso_id INTEGER NOT NULL,
    ano_ingresso INTEGER NOT NULL,
    semestre_ingresso INTEGER NOT NULL CHECK(semestre_ingresso IN (1, 2)),
    situacao TEXT NOT NULL DEFAULT 'ativo'
        CHECK(situacao IN ('ativo', 'concluido', 'trancado', 'evadido')),
    FOREIGN KEY (curso_id) REFERENCES cursos(id)
);

-- Tabela de períodos letivos
CREATE TABLE IF NOT EXISTS periodos_letivos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ano INTEGER NOT NULL,
    semestre INTEGER NOT NULL CHECK(semestre IN (1, 2)),
    data_inicio TEXT,
    data_fim TEXT,
    UNIQUE(ano, semestre)
);

-- Tabela de acompanhamentos acadêmicos (calculados pelo sistema)
CREATE TABLE IF NOT EXISTS acompanhamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    estudante_id INTEGER NOT NULL,
    periodo_letivo_id INTEGER NOT NULL,
    periodo_curricular INTEGER,
    media_global REAL,
    media_semestre REAL,
    disciplinas_cursadas INTEGER DEFAULT 0,
    disciplinas_aprovadas INTEGER DEFAULT 0,
    reprovacoes INTEGER DEFAULT 0,
    reprovacoes_falta INTEGER DEFAULT 0,
    reprovacoes_nota INTEGER DEFAULT 0,
    reprovacoes_sucessivas INTEGER DEFAULT 0,
    frequencia_media REAL,
    carga_horaria_matriculada REAL DEFAULT 0,
    carga_horaria_concluida REAL DEFAULT 0,
    percentual_integralizacao REAL DEFAULT 0,
    trancamentos INTEGER DEFAULT 0,
    distancia_km REAL,
    probabilidade_risco REAL,
    classificacao_risco TEXT CHECK(classificacao_risco IN ('OK', 'Atenção', 'Perigo')),
    z_score REAL,
    data_calculo TEXT,
    FOREIGN KEY (estudante_id) REFERENCES estudantes(id),
    FOREIGN KEY (periodo_letivo_id) REFERENCES periodos_letivos(id)
);

-- Tabela de disciplinas
CREATE TABLE IF NOT EXISTS disciplinas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL,
    nome TEXT NOT NULL,
    carga_horaria INTEGER NOT NULL DEFAULT 60,
    periodo_recomendado INTEGER,
    curso_id INTEGER NOT NULL,
    FOREIGN KEY (curso_id) REFERENCES cursos(id)
);

-- Tabela de matrículas em disciplinas
CREATE TABLE IF NOT EXISTS matriculas_disciplinas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    estudante_id INTEGER NOT NULL,
    disciplina_id INTEGER NOT NULL,
    periodo_letivo_id INTEGER NOT NULL,
    nota REAL,
    frequencia REAL,
    situacao TEXT CHECK(situacao IN ('aprovado', 'reprovado_nota', 'reprovado_falta', 'trancado', 'cursando')),
    numero_tentativa INTEGER DEFAULT 1,
    FOREIGN KEY (estudante_id) REFERENCES estudantes(id),
    FOREIGN KEY (disciplina_id) REFERENCES disciplinas(id),
    FOREIGN KEY (periodo_letivo_id) REFERENCES periodos_letivos(id)
);

-- Tabela de acompanhamentos administrativos (editáveis por funcionários)
CREATE TABLE IF NOT EXISTS acompanhamentos_funcionarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    estudante_id INTEGER NOT NULL,
    funcionario_responsavel TEXT,
    prioridade_manual INTEGER DEFAULT 0,
    situacao_atendimento TEXT DEFAULT 'pendente'
        CHECK(situacao_atendimento IN ('pendente', 'em_andamento', 'concluido', 'cancelado')),
    observacao TEXT,
    encaminhamento TEXT,
    data_prevista_contato TEXT,
    ultimo_contato TEXT,
    estudante_contatado INTEGER DEFAULT 0,
    acao_realizada TEXT,
    data_criacao TEXT NOT NULL DEFAULT (datetime('now')),
    data_atualizacao TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (estudante_id) REFERENCES estudantes(id)
);

-- Tabela de histórico de edições (auditoria)
CREATE TABLE IF NOT EXISTS historico_edicoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tabela_alterada TEXT NOT NULL,
    identificador_registro TEXT NOT NULL,
    campo_alterado TEXT NOT NULL,
    valor_anterior TEXT,
    valor_novo TEXT,
    usuario_responsavel TEXT DEFAULT 'sistema',
    data_hora TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_estudantes_curso ON estudantes(curso_id);
CREATE INDEX IF NOT EXISTS idx_estudantes_matricula ON estudantes(matricula);
CREATE INDEX IF NOT EXISTS idx_estudantes_situacao ON estudantes(situacao);
CREATE INDEX IF NOT EXISTS idx_acompanhamentos_estudante ON acompanhamentos(estudante_id);
CREATE INDEX IF NOT EXISTS idx_acompanhamentos_periodo ON acompanhamentos(periodo_letivo_id);
CREATE INDEX IF NOT EXISTS idx_acompanhamentos_risco ON acompanhamentos(classificacao_risco);
CREATE INDEX IF NOT EXISTS idx_matriculas_estudante ON matriculas_disciplinas(estudante_id);
CREATE INDEX IF NOT EXISTS idx_matriculas_periodo ON matriculas_disciplinas(periodo_letivo_id);
CREATE INDEX IF NOT EXISTS idx_acomp_func_estudante ON acompanhamentos_funcionarios(estudante_id);
CREATE INDEX IF NOT EXISTS idx_historico_tabela ON historico_edicoes(tabela_alterada);

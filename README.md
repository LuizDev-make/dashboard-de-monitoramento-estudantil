# 📊 Sistema de Monitoramento Estatístico de Estudantes — UFRPE

Projeto Substitutivo da Avaliação Final — desenvolvido para simular um
sistema real de acompanhamento acadêmico da Universidade Federal Rural de
Pernambuco (UFRPE), capaz de identificar antecipadamente estudantes com
maior risco de retenção, reprovação recorrente, evasão ou baixo desempenho.

> ⚠️ **AVISO IMPORTANTE — DADOS SINTÉTICOS**
> Todos os dados apresentados neste sistema (nomes, matrículas, telefones,
> CEPs, notas, frequências, coordenadas geográficas etc.) são **100%
> fictícios**, gerados por script com semente fixa para fins educacionais.
> Nenhum dado real de estudante da UFRPE é utilizado ou armazenado. O
> aviso também é exibido na interface (barra lateral do dashboard).

**Estudante:** [SEU NOME COMPLETO]
**Matrícula:** [SUA MATRÍCULA]
**Curso:** [SEU CURSO]
**Disciplina:** [NOME DA DISCIPLINA]

---

## 1. Descrição

A aplicação reúne dados acadêmicos, administrativos e contextuais de
estudantes, calcula indicadores estatísticos descritivos e padronizados, e
estima — por meio de um modelo de **regressão logística** (scikit-learn) —
a **probabilidade de cada estudante necessitar de acompanhamento**. Com
base nessa probabilidade, os estudantes são classificados em três faixas
de risco (OK / Atenção / Perigo), permitindo que a equipe da Pró-Reitoria
de Ensino priorize contatos e ações de apoio.

O sistema é apenas uma **ferramenta de apoio à decisão**. A probabilidade
estimada **não é uma sentença** e deve sempre ser interpretada por um
profissional responsável.

## 2. Objetivo geral

- Armazenar dados acadêmicos sintéticos de estudantes;
- Acompanhar a evolução de cada estudante ao longo dos períodos letivos;
- Calcular indicadores estatísticos descritivos e padronizados (média,
  mediana, desvio-padrão, z-score, IQR, taxas de aprovação/reprovação
  etc.);
- Treinar e utilizar um modelo de regressão logística (`predict_proba`);
- Classificar os estudantes em **OK**, **Atenção** ou **Perigo**;
- Apresentar dashboards filtráveis por curso, ano, semestre e período;
- Permitir que funcionários autorizados editem informações de
  acompanhamento (sem jamais alterar os campos calculados pelo modelo);
- Registrar toda alteração em uma tabela de auditoria;
- Prever uma camada de importação de dados (CSV/XLSX) preparada para uma
  futura integração com sistemas reais da universidade.

## 3. Tecnologias utilizadas

| Camada          | Tecnologia                                                |
|-----------------|------------------------------------------------------------|
| Front-end       | HTML5, CSS3 (design system próprio, dark mode/glassmorphism), JavaScript puro (sem frameworks) |
| Gráficos        | Chart.js                                                    |
| Back-end        | Python 3.11+, FastAPI, Uvicorn                              |
| Persistência    | SQLite (via `sqlite3`, acesso concentrado em `backend/database.py`) |
| Estatística/ML  | pandas, NumPy, SciPy, scikit-learn (Pipeline + ColumnTransformer + LogisticRegression), joblib |
| Validação       | Pydantic (schemas de request/response)                     |
| Testes          | pytest, httpx (TestClient do FastAPI)                       |

## 4. Estrutura de pastas

```
monitoramento-ufrpe/
├── backend/
│   ├── app.py                 # ponto de entrada FastAPI, CORS, static files
│   ├── config.py               # variáveis de ambiente e constantes (limiares, paths)
│   ├── database.py             # conexão SQLite + context manager get_db()
│   ├── models.py                # dataclasses internas do domínio
│   ├── schemas.py                # modelos Pydantic (request/response)
│   ├── repositories/             # ÚNICO ponto de acesso SQL (sem SQL espalhado)
│   │   ├── estudantes.py
│   │   ├── cursos.py
│   │   └── acompanhamentos.py
│   ├── routes/                   # endpoints da API REST
│   │   ├── estudantes.py
│   │   ├── dashboard.py
│   │   ├── importacoes.py
│   │   └── modelo.py
│   └── services/
│       ├── estatisticas.py       # indicadores estatísticos
│       ├── risco.py              # classificação de risco + fatores de alerta
│       ├── distancia.py          # Haversine + integração opcional ViaCEP
│       └── auditoria.py          # histórico de edições
├── data_import/                  # camada de importação (futuros dados reais)
│   ├── importador_csv.py
│   ├── importador_excel.py
│   ├── mapeamento_colunas.py
│   └── validacao.py
├── frontend/
│   ├── index.html                # Dashboard geral
│   ├── estudantes.html           # Tabela de estudantes
│   ├── estudante.html            # Perfil detalhado
│   ├── css/ (base.css, dashboard.css, componentes.css)
│   └── js/  (api.js, dashboard.js, estudantes.js, graficos.js, formularios.js)
├── data/                         # CSVs gerados (dados_sinteticos.csv, modelo_importacao.csv)
├── database/
│   ├── schema.sql                # DDL de todas as tabelas
│   └── monitoramento.db          # criado por script (não versionado)
├── scripts/
│   ├── criar_banco.py             # cria o SQLite a partir do schema.sql
│   ├── gerar_dados_sinteticos.py  # gera >2.000 estudantes / 10 anos
│   ├── calcular_indicadores.py    # recálculo de z-scores por grupo
│   ├── treinar_modelo.py          # treina a regressão logística
│   └── avaliar_modelo.py          # matriz de confusão, ROC-AUC, Brier etc.
├── models/
│   └── modelo_risco.joblib        # modelo treinado (gerado, não versionado)
├── tests/
│   ├── test_estatisticas.py
│   ├── test_classificacao.py
│   ├── test_importacao.py
│   └── test_api.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## 5. Pré-requisitos

- Python 3.11 ou superior
- pip
- Git (opcional, para clonar o repositório)

Nenhum caminho absoluto é utilizado no projeto: todos os caminhos são
resolvidos de forma relativa à raiz do repositório (`Path(__file__).resolve().parent...`),
então a aplicação funciona em qualquer máquina, em qualquer usuário.

## 6. Instalação

### 6.1 Linux / macOS

```bash
git clone <ENDERECO_DO_REPOSITORIO>
cd monitoramento-ufrpe

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

### 6.2 Windows (PowerShell / CMD)

```powershell
git clone <ENDERECO_DO_REPOSITORIO>
cd monitoramento-ufrpe

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
```

### 6.3 Variáveis de ambiente (opcional)

```bash
cp .env.example .env      # Linux/macOS
copy .env.example .env    # Windows
```

O `.env` permite configurar `DEBUG`, `SECRET_KEY`, `VIACEP_ENABLED` e as
coordenadas de referência da UFRPE. A aplicação roda com valores padrão
mesmo sem `.env`.

## 7. Criação e inicialização do banco de dados

```bash
python scripts/criar_banco.py
```

Esse script executa `database/schema.sql`, cria o arquivo
`database/monitoramento.db` e valida se todas as 8 tabelas foram criadas
corretamente.

## 8. Geração dos dados sintéticos

```bash
python scripts/gerar_dados_sinteticos.py
```

Este script:
- utiliza semente fixa (`SEMENTE = 2026`) para reprodutibilidade;
- gera **2.200 estudantes** distintos, distribuídos entre 6 cursos;
- gera **20 períodos letivos** (2016.1 a 2025.2 → 10 anos);
- gera disciplinas por curso/período e matrículas em disciplinas;
- produz trajetórias acadêmicas longitudinais coerentes: estudantes
  ingressantes, concluintes, evadidos, trancados e ativos, com talento e
  dedicação individuais que influenciam notas e frequência;
- calibra a variável-alvo (`desfecho_risco`) por meio de uma função
  logística com ruído + regras determinísticas para casos extremos
  (ver seção 12 — Definição do desfecho);
- popula o SQLite e exporta `data/dados_sinteticos.csv` e
  `data/modelo_importacao.csv` (modelo de exemplo para importação).

## 9. Treinamento do modelo

```bash
python scripts/treinar_modelo.py
```

Treina a regressão logística (ver seção 11), avalia em validação e teste,
salva o pipeline em `models/modelo_risco.joblib` e atualiza
`probabilidade_risco` / `classificacao_risco` de todos os acompanhamentos
no banco.

Para reavaliar o modelo já treinado a qualquer momento:

```bash
python scripts/avaliar_modelo.py
```

Para recalcular apenas os z-scores por grupo (curso + semestre + período):

```bash
python scripts/calcular_indicadores.py
```

## 10. Execução do sistema

```bash
uvicorn backend.app:app --reload
```

Acesse em: **http://127.0.0.1:8000**

- `/` → Dashboard geral
- `/estudantes.html` → Tabela de estudantes
- `/estudante.html?id=<id>` → Perfil detalhado
- `/docs` → Documentação interativa da API (Swagger, gerada automaticamente pelo FastAPI)

Também é possível treinar/recalcular o modelo diretamente pela API:
`POST /api/modelo/treinar` e `POST /api/modelo/recalcular`.

## 11. Execução dos testes

```bash
pytest -q
```

Os testes cobrem:
- classificação de risco nos limites exatos (69,99% / 70% / 84,99% / 85% / 100%);
- validação de probabilidade fora de `[0, 1]`;
- fatores de alerta descritivos;
- cálculo de distância (Haversine), incluindo simetria e distância zero;
- indicadores estatísticos (taxa de aprovação/reprovação, z-score,
  coeficiente de variação, maior sequência de reprovações, percentual de
  integralização, atraso curricular, resumo de distribuição, escore
  composto, evolução longitudinal);
- importação de CSV (matrícula duplicada, colunas faltantes, valores
  inválidos);
- endpoints da API REST (estudantes, cursos, dashboard, acompanhamentos,
  auditoria) e inserção/leitura no SQLite.

## 12. Descrição das tabelas

| Tabela                          | Finalidade |
|----------------------------------|-----------|
| `cursos`                          | Cadastro dos cursos (nome, código, campus, duração, ativo) |
| `estudantes`                       | Dados de identificação/cadastro do estudante |
| `periodos_letivos`                  | Semestres letivos (ano + semestre) |
| `acompanhamentos`                    | Um registro por estudante/semestre com todos os indicadores acadêmicos **calculados** (média, frequência, reprovações, integralização, distância, probabilidade, classificação, z-score) |
| `disciplinas`                        | Disciplinas de cada curso, por período recomendado |
| `matriculas_disciplinas`               | Matrícula de um estudante em uma disciplina em um período, com nota/frequência/situação |
| `acompanhamentos_funcionarios`          | Dados **administrativos e editáveis** por funcionários (responsável, situação de atendimento, observação, encaminhamento, contato) |
| `historico_edicoes`                      | Auditoria: toda alteração feita em `acompanhamentos_funcionarios` é registrada (tabela, campo, valor anterior, valor novo, usuário, data/hora) |

O banco **não é uma tabela única**: os dados acadêmicos calculados,
os dados cadastrais e os dados administrativos ficam em tabelas
separadas, e o acesso SQL fica concentrado em `backend/repositories/` —
nenhuma rota ou serviço monta SQL diretamente.

## 13. Descrição das variáveis (principais)

**Identificação:** matrícula, nome, telefone, sexo, data de nascimento,
CEP, curso, campus, ano/semestre de ingresso, período curricular,
situação acadêmica (ativo/concluído/trancado/evadido).

**Desempenho acadêmico:** média global, média do semestre, disciplinas
cursadas/aprovadas, reprovações (total, por falta, por nota),
reprovações sucessivas, frequência média, carga horária
matriculada/concluída, percentual de integralização, trancamentos,
variação da média em relação ao semestre anterior.

**Contextuais:** CEP, latitude/longitude (sintéticas), distância
estimada até a UFRPE (linha reta, Haversine).

**Calculadas pelo modelo (não editáveis manualmente):**
`probabilidade_risco`, `classificacao_risco`, `z_score`.

Um dicionário de dados completo, campo a campo, está em
`database/schema.sql` (comentários inline) e em `backend/models.py`.

## 14. Definição da variável-alvo (`desfecho_risco`)

`desfecho_risco = 1` (risco) quando, considerando o **semestre seguinte**
ao registro em análise, ocorre **pelo menos uma** das condições:

- evasão do curso;
- trancamento de todas as disciplinas do semestre;
- média do semestre inferior a 4,0;
- nenhuma aprovação no semestre (0 de N disciplinas cursadas);
- reprovação em parcela relevante das disciplinas cursadas.

O restante dos casos utiliza um modelo logístico latente com ruído
(`σ = 1.2`) sobre média, frequência, reprovações, reprovações sucessivas,
trancamentos, integralização e distância — garantindo que a base **não
seja 0% nem 100%** de risco (distribuição balanceada, tipicamente
próxima de 70–85% de casos positivos com bastante dispersão de
probabilidade, conforme impresso no console ao final da geração).

**Importante:** o modelo utiliza **somente** informações disponíveis até
o semestre atual para prever o desfecho do semestre seguinte — não há
vazamento de dados futuros (*data leakage*) no treinamento
(`scripts/treinar_modelo.py`, separação temporal).

## 15. Regressão logística

O modelo é um `Pipeline` scikit-learn:

```
ColumnTransformer
├── numéricas → SimpleImputer(mediana) → StandardScaler
└── categóricas → SimpleImputer(moda) → OneHotEncoder
        ↓
LogisticRegression(class_weight="balanced", max_iter=2000, random_state=2026)
```

Variáveis numéricas: `media_global`, `media_semestre`, `variacao_media`,
`frequencia_media`, `reprovacoes`, `reprovacoes_sucessivas`,
`taxa_reprovacao`, `trancamentos`, `percentual_integralizacao`,
`atraso_curricular`, `distancia_km`.
Variáveis categóricas: `curso`, `periodo_curricular`, `turno`,
`assistencia_estudantil`.

**Matrícula, nome e telefone nunca são usados como variáveis
preditoras.**

Separação temporal (evita vazamento de informação futura):
- Treino: 2016–2022
- Validação: 2023–2024
- Teste: 2025

A API sempre usa `predict_proba` (nunca apenas `predict`) para obter a
probabilidade contínua de risco.

## 16. Limites de classificação de risco

| Classificação | Probabilidade estimada | Cor      |
|----------------|--------------------------|----------|
| OK             | 0% a 69,99%               | 🟢 verde  |
| Atenção        | 70% a 84,99%               | 🟡 amarelo|
| Perigo         | 85% a 100%                  | 🔴 vermelho|

Regra de fronteira: **70,00% pertence a "Atenção"** e **85,00% pertence a
"Perigo"**. Esses limites (`LIMIAR_ATENCAO` e `LIMIAR_PERIGO` em
`backend/config.py`) são **regras administrativas do projeto**, e não
necessariamente os melhores limiares estatísticos possíveis (ver
avaliação do modelo).

## 17. Explicação das métricas de avaliação

Calculadas em `scripts/avaliar_modelo.py` para treino, validação e teste:

- **Matriz de confusão** (VN, FP, FN, VP);
- **Acurácia** — pode enganar em bases desbalanceadas;
- **Precisão** — dos sinalizados como risco, quantos realmente eram risco;
- **Recall/Sensibilidade** — dos estudantes de risco, quantos o modelo identificou;
- **Especificidade** — dos estudantes sem risco, quantos foram corretamente classificados como tal;
- **F1-Score** — equilíbrio entre precisão e recall;
- **ROC-AUC** — capacidade de ordenação do modelo (0,5 = aleatório, 1,0 = perfeito);
- **Brier Score** — qualidade da calibração das probabilidades (quanto menor, melhor);
- **Taxa de falsos negativos** — estudantes de risco que **não** foram sinalizados (o erro mais crítico neste contexto).

Os falsos negativos são o erro mais custoso para a Pró-Reitoria: um
estudante em risco que passa despercebido. Por isso o modelo usa
`class_weight="balanced"`.

## 18. Explicabilidade (fatores de alerta)

`backend/services/risco.py` gera, para cada estudante, uma lista de
fatores descritivos (não SHAP, mas regras interpretáveis): média global
abaixo de 5,0, frequência abaixo de 75%, reprovações sucessivas ≥ 2,
queda de média ≥ 1,0 ponto, integralização abaixo do esperado para o
período, taxa de reprovação acima de 50%, múltiplos trancamentos e
distância elevada. Esses fatores são exibidos no perfil do estudante como
**indicadores descritivos, não como prova causal**.

## 19. Procedimento de importação de dados

Endpoint: `POST /api/importacoes` (upload multipart de `.csv` ou `.xlsx`).

Fluxo (`data_import/`):
1. `mapeamento_colunas.py` reconhece variações de nomes de colunas
   (ex.: `MATRICULA_ALUNO`, `matrícula`, `mat`, `ra` → `matricula`);
2. `verificar_colunas_obrigatorias()` garante que `matricula` e `nome`
   estão presentes;
3. `validacao.py` valida tipos e regras de negócio (média em `[0,10]`,
   frequência em `[0,100]`, aprovações ≤ cursadas, período ≥ 0, CEP com 8
   dígitos, situação em domínio válido) e identifica duplicatas — tanto
   dentro do próprio arquivo quanto contra o banco existente;
4. Registros válidos são inseridos; inválidos e duplicados são
   reportados **sem apagar dados anteriores**;
5. A resposta inclui contagens de válidos/inválidos/duplicados, detalhes
   (até 50 de cada) e metadados de origem/data da importação.

Um arquivo de exemplo pronto para teste fica em
`data/modelo_importacao.csv`.

## 20. Segurança, privacidade e ética

- Campos calculados pelo modelo (`probabilidade_risco`,
  `classificacao_risco`, `z_score`, médias, reprovações etc.) são
  **protegidos** (`CAMPOS_PROTEGIDOS` em
  `backend/repositories/acompanhamentos.py`) e **nunca** podem ser
  editados diretamente por um funcionário — apenas recalculados pelo
  sistema (`POST /api/modelo/recalcular`);
- Toda edição administrativa é registrada em `historico_edicoes`
  (tabela, campo, valor anterior/novo, usuário, data/hora);
- Dados acadêmicos calculados e observações administrativas ficam em
  tabelas separadas;
- O `.env` (com eventuais chaves) nunca é versionado (`.gitignore`);
- A interface nunca apresenta frases determinísticas do tipo *"este
  estudante abandonará o curso"* — sempre o formato *"Probabilidade
  estimada de desfecho de risco: X%. O resultado deve ser analisado por
  um funcionário responsável."*;
- O modelo é uma ferramenta de **apoio** à decisão humana, sujeita a erro
  estatístico e a viés — variáveis sensíveis (sexo, distância,
  indicadores socioeconômicos) devem ser usadas com cautela e nunca de
  forma automática para restringir direitos, bolsas, matrícula ou
  atendimento.

## 21. Limitações conhecidas

- Os dados são **sintéticos**; relações plausíveis foram simuladas, mas
  não substituem dados reais nem validam o modelo para uso em produção;
- A distância até a universidade é uma estimativa em **linha reta**
  (Haversine), não a distância rodoviária real nem o tempo de
  deslocamento;
- A integração com o ViaCEP é **opcional** (`VIACEP_ENABLED`), cacheada,
  e falhas externas nunca impedem o funcionamento local do sistema;
- Os limiares de 70%/85% são regras administrativas do projeto, não
  necessariamente os limiares estatisticamente ótimos (ex.: pelo ponto
  ótimo da curva ROC);
- Correlações apresentadas na matriz de correlação **não implicam
  causalidade**;
- O sistema não deve ser utilizado, isoladamente, para decisões que
  afetem direitos de estudantes reais.

## 22. Imagens da aplicação

> Adicione aqui, antes da entrega final, capturas de tela do Dashboard,
> da Tabela de Estudantes (com filtros aplicados) e do Perfil do
> Estudante (com fatores de alerta e gráfico de evolução).

`![Dashboard](docs/imagens/dashboard.png)`
`![Tabela de estudantes](docs/imagens/estudantes.png)`
`![Perfil do estudante](docs/imagens/perfil.png)`

## 23. Licença

Distribuído sob licença MIT — ver [LICENSE](LICENSE).

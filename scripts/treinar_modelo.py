"""
Script de treinamento do modelo de regressão logística.

Monta um Pipeline scikit-learn com ColumnTransformer:
- Variáveis numéricas: imputação por mediana + StandardScaler
- Variáveis categóricas: imputação por moda + OneHotEncoder
- Modelo: LogisticRegression (class_weight="balanced", max_iter=2000)

Separação temporal:
- Treino: 2016-2022
- Validação: 2023-2024
- Teste: 2025

Usa predict_proba (nunca apenas predict).
Salva o modelo em models/modelo_risco.joblib.

Uso:
    python scripts/treinar_modelo.py
"""
import sys
import sqlite3
import numpy as np
import pandas as pd
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, brier_score_loss, confusion_matrix,
)
import joblib

from backend.config import DATABASE_PATH, MODEL_PATH, SEMENTE


# Features
FEATURES_NUMERICAS = [
    "media_global", "media_semestre", "variacao_media",
    "frequencia_media", "reprovacoes", "reprovacoes_sucessivas",
    "taxa_reprovacao", "trancamentos", "percentual_integralizacao",
    "atraso_curricular", "distancia_km",
]

FEATURES_CATEGORICAS = [
    "curso", "periodo_curricular", "turno", "assistencia_estudantil",
]


def carregar_dados():
    """Carrega os dados do banco para treinamento."""
    print("📊 Carregando dados do banco de dados...")

    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row

    query = """
        SELECT
            a.estudante_id,
            e.matricula,
            a.media_global,
            a.media_semestre,
            a.frequencia_media,
            a.reprovacoes,
            a.reprovacoes_falta,
            a.reprovacoes_nota,
            a.reprovacoes_sucessivas,
            a.trancamentos,
            a.percentual_integralizacao,
            a.distancia_km,
            a.disciplinas_cursadas,
            a.disciplinas_aprovadas,
            a.periodo_curricular,
            a.carga_horaria_matriculada,
            a.carga_horaria_concluida,
            pl.ano,
            pl.semestre,
            c.nome as curso,
            c.duracao_periodos,
            e.situacao
        FROM acompanhamentos a
        JOIN periodos_letivos pl ON a.periodo_letivo_id = pl.id
        JOIN estudantes e ON a.estudante_id = e.id
        JOIN cursos c ON e.curso_id = c.id
        ORDER BY a.estudante_id, pl.ano, pl.semestre
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    print(f"   Total de registros carregados: {len(df)}")
    return df


def engenharia_features(df: pd.DataFrame) -> pd.DataFrame:
    """Cria features derivadas para o modelo."""
    print("🔧 Engenharia de features...")

    # Taxa de reprovação
    df["taxa_reprovacao"] = df.apply(
        lambda r: r["reprovacoes"] / r["disciplinas_cursadas"]
        if r["disciplinas_cursadas"] and r["disciplinas_cursadas"] > 0 else 0.0,
        axis=1,
    )

    # Atraso curricular
    df["atraso_curricular"] = df.apply(
        lambda r: max(0, (r["ano"] - 2016) * 2 + r["semestre"] - (r["periodo_curricular"] or 1))
        if r["periodo_curricular"] else 0,
        axis=1,
    )

    # Variação da média (diferença entre semestres consecutivos)
    df = df.sort_values(["estudante_id", "ano", "semestre"])
    df["media_anterior"] = df.groupby("estudante_id")["media_semestre"].shift(1)
    df["variacao_media"] = df["media_semestre"] - df["media_anterior"]
    df["variacao_media"] = df["variacao_media"].fillna(0)

    # Turno e assistência (simulados para dados sintéticos)
    rng = np.random.default_rng(SEMENTE)
    df["turno"] = rng.choice(["integral", "matutino", "noturno"], size=len(df), p=[0.5, 0.3, 0.2])
    df["assistencia_estudantil"] = rng.choice(["sim", "nao"], size=len(df), p=[0.25, 0.75])

    return df


def criar_variavel_alvo(df: pd.DataFrame) -> pd.DataFrame:
    """Cria a variável-alvo desfecho_risco.

    Usa a variável desfecho_risco pré-calculada pelo gerador de dados
    sintéticos (gerar_dados_sinteticos.py), que já incorpora um modelo
    logístico com ruído + regras determinísticas calibradas.

    Se o campo não estiver disponível no DataFrame, recalcula com regras
    conservadoras baseadas no próximo semestre.

    IMPORTANTE: Usa apenas informações disponíveis até o semestre atual
    (sem vazamento de dados futuros).
    """
    print("🎯 Criando variável-alvo (desfecho_risco)...")

    # Tenta carregar do CSV pré-calculado
    csv_path = ROOT_DIR / "data" / "dados_sinteticos.csv"
    if csv_path.exists():
        print("   📄 Carregando desfecho_risco do CSV pré-calculado...")
        df_csv = pd.read_csv(csv_path, sep=",", encoding="utf-8")

        # Construir chave de junção: matricula + periodo_letivo
        if "matricula" in df.columns and "matricula" in df_csv.columns:
            # Criar coluna periodo_letivo no df se não existir
            if "periodo_letivo" not in df.columns:
                df["periodo_letivo"] = df["ano"].astype(str) + "." + df["semestre"].astype(str)

            # Pegar apenas matricula, periodo_letivo, desfecho_risco do CSV
            df_desfecho = df_csv[["matricula", "periodo_letivo", "desfecho_risco"]].copy()
            df_desfecho["periodo_letivo"] = df_desfecho["periodo_letivo"].astype(str)
            df_desfecho["matricula"] = df_desfecho["matricula"].astype(str)
            df["periodo_letivo"] = df["periodo_letivo"].astype(str)
            df["matricula"] = df["matricula"].astype(str)

            # Merge
            df = df.drop(columns=["desfecho_risco"], errors="ignore")
            df = df.merge(
                df_desfecho,
                on=["matricula", "periodo_letivo"],
                how="left",
            )
            df["desfecho_risco"] = df["desfecho_risco"].fillna(0).astype(int)

            # Filtrar: manter apenas registros que NÃO são o último de cada estudante
            # (para evitar predizer o futuro quando não há próximo semestre)
            df = df.sort_values(["estudante_id", "ano", "semestre"])
            df["is_last"] = ~df.duplicated(subset=["estudante_id"], keep="last")
            # Manter evadidos mesmo se último
            mask_valido = (~df["is_last"]) | (df["situacao"] == "evadido")
            df_treino = df[mask_valido].copy()
            df_treino = df_treino.drop(columns=["is_last", "periodo_letivo", "media_anterior"], errors="ignore")

            print(f"   Registros com desfecho válido: {len(df_treino)}")
            print(f"   Desfecho = 1 (risco): {df_treino['desfecho_risco'].sum()} "
                  f"({df_treino['desfecho_risco'].mean()*100:.1f}%)")
            print(f"   Desfecho = 0 (sem risco): {(df_treino['desfecho_risco'] == 0).sum()} "
                  f"({(1-df_treino['desfecho_risco'].mean())*100:.1f}%)")

            return df_treino

    # Fallback: recalcular com regras conservadoras
    print("   ⚠️ CSV não encontrado, recalculando desfecho_risco...")
    df = df.sort_values(["estudante_id", "ano", "semestre"])
    df["prox_media"] = df.groupby("estudante_id")["media_semestre"].shift(-1)
    df["prox_aprovadas"] = df.groupby("estudante_id")["disciplinas_aprovadas"].shift(-1)
    df["prox_cursadas"] = df.groupby("estudante_id")["disciplinas_cursadas"].shift(-1)
    df["prox_trancamentos"] = df.groupby("estudante_id")["trancamentos"].shift(-1)

    df["desfecho_risco"] = 0
    # Apenas casos extremos
    df.loc[df["prox_media"] < 3.0, "desfecho_risco"] = 1
    df.loc[
        (df["prox_cursadas"] > 0) & (df["prox_aprovadas"] == 0),
        "desfecho_risco"
    ] = 1
    df.loc[df["situacao"] == "evadido", "desfecho_risco"] = 1
    df.loc[
        (df["prox_cursadas"] > 0) &
        (df["prox_trancamentos"] >= df["prox_cursadas"]),
        "desfecho_risco"
    ] = 1

    mask_valido = df["prox_media"].notna() | (df["situacao"] == "evadido")
    df_treino = df[mask_valido].copy()
    df_treino = df_treino.drop(columns=[
        "prox_media", "prox_aprovadas", "prox_cursadas",
        "prox_trancamentos", "media_anterior",
    ], errors="ignore")

    print(f"   Registros com desfecho válido: {len(df_treino)}")
    print(f"   Desfecho = 1 (risco): {df_treino['desfecho_risco'].sum()} "
          f"({df_treino['desfecho_risco'].mean()*100:.1f}%)")
    print(f"   Desfecho = 0 (sem risco): {(df_treino['desfecho_risco'] == 0).sum()} "
          f"({(1-df_treino['desfecho_risco'].mean())*100:.1f}%)")

    return df_treino


def construir_pipeline():
    """Constrói o pipeline scikit-learn com ColumnTransformer."""
    # Pré-processamento numérico: mediana + StandardScaler
    preprocessor_num = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    # Pré-processamento categórico: moda + OneHotEncoder
    preprocessor_cat = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])

    # ColumnTransformer
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", preprocessor_num, FEATURES_NUMERICAS),
            ("cat", preprocessor_cat, FEATURES_CATEGORICAS),
        ]
    )

    # Pipeline completo
    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            random_state=SEMENTE,
        )),
    ])

    return pipeline


def treinar():
    """Executa o treinamento completo do modelo."""
    print("=" * 60)
    print("  TREINAMENTO DO MODELO DE REGRESSÃO LOGÍSTICA")
    print("=" * 60)

    # Carrega e prepara dados
    df = carregar_dados()
    df = engenharia_features(df)
    df_treino = criar_variavel_alvo(df)

    # Separação temporal
    print("\n📅 Separação temporal:")
    treino = df_treino[df_treino["ano"] <= 2022]
    validacao = df_treino[(df_treino["ano"] >= 2023) & (df_treino["ano"] <= 2024)]
    teste = df_treino[df_treino["ano"] >= 2025]

    print(f"   Treino (2016-2022): {len(treino)} registros")
    print(f"   Validação (2023-2024): {len(validacao)} registros")
    print(f"   Teste (2025): {len(teste)} registros")

    if len(treino) == 0:
        print("❌ Sem dados de treino suficientes!")
        return

    # Features e alvo
    all_features = FEATURES_NUMERICAS + FEATURES_CATEGORICAS

    # Garante que as colunas categóricas são strings
    for col in FEATURES_CATEGORICAS:
        if col in treino.columns:
            treino[col] = treino[col].astype(str)
        if col in validacao.columns:
            validacao[col] = validacao[col].astype(str)
        if col in teste.columns:
            teste[col] = teste[col].astype(str)

    X_treino = treino[all_features]
    y_treino = treino["desfecho_risco"]

    # Constrói e treina pipeline
    print("\n🏋️ Treinando modelo...")
    pipeline = construir_pipeline()
    pipeline.fit(X_treino, y_treino)
    print("✅ Modelo treinado com sucesso!")

    # Avalia em validação
    if len(validacao) > 0:
        X_val = validacao[all_features]
        y_val = validacao["desfecho_risco"]
        y_val_proba = pipeline.predict_proba(X_val)[:, 1]
        y_val_pred = pipeline.predict(X_val)

        print("\n📋 Métricas de VALIDAÇÃO (2023-2024):")
        print(f"   Acurácia: {accuracy_score(y_val, y_val_pred):.4f}")
        print(f"   Precisão: {precision_score(y_val, y_val_pred, zero_division=0):.4f}")
        print(f"   Recall: {recall_score(y_val, y_val_pred, zero_division=0):.4f}")
        print(f"   F1-Score: {f1_score(y_val, y_val_pred, zero_division=0):.4f}")
        if len(np.unique(y_val)) > 1:
            print(f"   ROC-AUC: {roc_auc_score(y_val, y_val_proba):.4f}")
        print(f"   Brier Score: {brier_score_loss(y_val, y_val_proba):.4f}")

    # Avalia em teste
    if len(teste) > 0:
        X_test = teste[all_features]
        y_test = teste["desfecho_risco"]
        y_test_proba = pipeline.predict_proba(X_test)[:, 1]
        y_test_pred = pipeline.predict(X_test)

        print("\n📋 Métricas de TESTE (2025):")
        print(f"   Acurácia: {accuracy_score(y_test, y_test_pred):.4f}")
        print(f"   Precisão: {precision_score(y_test, y_test_pred, zero_division=0):.4f}")
        print(f"   Recall: {recall_score(y_test, y_test_pred, zero_division=0):.4f}")
        print(f"   F1-Score: {f1_score(y_test, y_test_pred, zero_division=0):.4f}")
        if len(np.unique(y_test)) > 1:
            print(f"   ROC-AUC: {roc_auc_score(y_test, y_test_proba):.4f}")
        print(f"   Brier Score: {brier_score_loss(y_test, y_test_proba):.4f}")

    # Salva o modelo
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, str(MODEL_PATH))
    print(f"\n💾 Modelo salvo em: {MODEL_PATH}")

    # Atualiza probabilidades no banco
    print("\n🔄 Atualizando probabilidades no banco de dados...")
    atualizar_probabilidades_banco(pipeline, all_features)

    print("\n🎉 Treinamento concluído com sucesso!")


def atualizar_probabilidades_banco(pipeline, features):
    """Atualiza as probabilidades e classificações no banco de dados."""
    from backend.services.risco import classificar_risco
    from datetime import datetime

    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row

    # Carrega todos os acompanhamentos com features necessárias
    df = carregar_dados()
    df = engenharia_features(df)

    for col in FEATURES_CATEGORICAS:
        if col in df.columns:
            df[col] = df[col].astype(str)

    X = df[features]
    probabilidades = pipeline.predict_proba(X)[:, 1]

    # Atualiza cada registro
    cursor = conn.cursor()
    ids_query = """
        SELECT a.id FROM acompanhamentos a
        JOIN periodos_letivos pl ON a.periodo_letivo_id = pl.id
        JOIN estudantes e ON a.estudante_id = e.id
        JOIN cursos c ON e.curso_id = c.id
        ORDER BY a.estudante_id, pl.ano, pl.semestre
    """
    ids = [row[0] for row in cursor.execute(ids_query).fetchall()]

    for i, acomp_id in enumerate(ids):
        prob = float(probabilidades[i])
        classif = classificar_risco(prob)
        cursor.execute(
            """
            UPDATE acompanhamentos
            SET probabilidade_risco = ?,
                classificacao_risco = ?,
                data_calculo = ?
            WHERE id = ?
            """,
            (prob, classif["classificacao"], datetime.now().isoformat(), acomp_id),
        )

    conn.commit()
    conn.close()
    print(f"   ✅ {len(ids)} registros atualizados.")


if __name__ == "__main__":
    treinar()

"""
Script de avaliação do modelo de regressão logística.

Calcula e reporta métricas detalhadas:
- Matriz de confusão
- Acurácia, Precisão, Recall/Sensibilidade, Especificidade
- F1-Score
- ROC-AUC
- Brier Score (calibração)
- Taxa de falsos negativos
- Curva ROC (dados para plotagem)

Uso:
    python scripts/avaliar_modelo.py
"""
import sys
import sqlite3
import numpy as np
import pandas as pd
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, brier_score_loss, confusion_matrix, roc_curve,
)
import joblib

from backend.config import DATABASE_PATH, MODEL_PATH, SEMENTE


def avaliar():
    """Executa a avaliação completa do modelo."""
    print("=" * 60)
    print("  AVALIAÇÃO DO MODELO DE REGRESSÃO LOGÍSTICA")
    print("=" * 60)

    if not MODEL_PATH.exists():
        print("❌ Modelo não encontrado. Execute treinar_modelo.py primeiro.")
        return

    # Carrega o modelo
    pipeline = joblib.load(str(MODEL_PATH))
    print("✅ Modelo carregado com sucesso.")

    # Importa funções do script de treinamento
    from scripts.treinar_modelo import (
        carregar_dados, engenharia_features, criar_variavel_alvo,
        FEATURES_NUMERICAS, FEATURES_CATEGORICAS,
    )

    # Carrega e prepara dados
    df = carregar_dados()
    df = engenharia_features(df)
    df_treino = criar_variavel_alvo(df)

    all_features = FEATURES_NUMERICAS + FEATURES_CATEGORICAS

    for col in FEATURES_CATEGORICAS:
        if col in df_treino.columns:
            df_treino[col] = df_treino[col].astype(str)

    # Conjuntos
    treino = df_treino[df_treino["ano"] <= 2022]
    validacao = df_treino[(df_treino["ano"] >= 2023) & (df_treino["ano"] <= 2024)]
    teste = df_treino[df_treino["ano"] >= 2025]

    for nome, conjunto in [("TREINO", treino), ("VALIDAÇÃO", validacao), ("TESTE", teste)]:
        if len(conjunto) == 0:
            print(f"\n⚠️  Conjunto {nome} vazio — pulando.")
            continue

        X = conjunto[all_features]
        y = conjunto["desfecho_risco"]

        y_proba = pipeline.predict_proba(X)[:, 1]
        y_pred = pipeline.predict(X)

        print(f"\n{'='*60}")
        print(f"  CONJUNTO: {nome} ({len(conjunto)} registros)")
        print(f"{'='*60}")

        # Matriz de confusão
        cm = confusion_matrix(y, y_pred)
        tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)

        print(f"\n📊 Matriz de Confusão:")
        print(f"   {'':>20} Previsto Negativo  Previsto Positivo")
        print(f"   Real Negativo      {tn:>10}          {fp:>10}")
        print(f"   Real Positivo      {fn:>10}          {tp:>10}")

        # Métricas
        acc = accuracy_score(y, y_pred)
        prec = precision_score(y, y_pred, zero_division=0)
        rec = recall_score(y, y_pred, zero_division=0)
        f1 = f1_score(y, y_pred, zero_division=0)

        # Especificidade
        especificidade = tn / (tn + fp) if (tn + fp) > 0 else 0.0

        # Taxa de falsos negativos
        tfn = fn / (fn + tp) if (fn + tp) > 0 else 0.0

        # ROC-AUC
        try:
            roc = roc_auc_score(y, y_proba)
        except ValueError:
            roc = float("nan")

        # Brier Score
        brier = brier_score_loss(y, y_proba)

        print(f"\n📋 Métricas:")
        print(f"   Acurácia:            {acc:.4f}  ({acc*100:.1f}%)")
        print(f"   Precisão:            {prec:.4f}  ({prec*100:.1f}%)")
        print(f"   Recall/Sensibilidade:{rec:.4f}  ({rec*100:.1f}%)")
        print(f"   Especificidade:      {especificidade:.4f}  ({especificidade*100:.1f}%)")
        print(f"   F1-Score:            {f1:.4f}")
        print(f"   ROC-AUC:             {roc:.4f}")
        print(f"   Brier Score:         {brier:.4f}")
        print(f"   Taxa Falsos Neg.:    {tfn:.4f}  ({tfn*100:.1f}%)")

        print(f"\n📝 Interpretação:")
        print(f"   - Acurácia pode enganar em bases desbalanceadas.")
        print(f"   - Recall mede quantos estudantes de risco foram identificados.")
        print(f"   - Falsos negativos ({fn}) são estudantes de risco NÃO sinalizados.")
        print(f"   - ROC-AUC mede a capacidade de ordenação do modelo.")
        print(f"   - Brier Score mede a qualidade das probabilidades (menor = melhor).")
        print(f"   - Os limites de 70%/85% são regras administrativas, não")
        print(f"     necessariamente os melhores limiares estatísticos.")

    # Distribuição das probabilidades
    print(f"\n{'='*60}")
    print(f"  DISTRIBUIÇÃO DAS PROBABILIDADES")
    print(f"{'='*60}")

    if len(teste) > 0:
        X_teste = teste[all_features]
        probs_teste = pipeline.predict_proba(X_teste)[:, 1]

        print(f"\n   Conjunto de teste:")
        print(f"   Min:     {probs_teste.min():.4f}")
        print(f"   Q1:      {np.percentile(probs_teste, 25):.4f}")
        print(f"   Mediana: {np.median(probs_teste):.4f}")
        print(f"   Q3:      {np.percentile(probs_teste, 75):.4f}")
        print(f"   Max:     {probs_teste.max():.4f}")
        print(f"   Média:   {probs_teste.mean():.4f}")

        # Classificação pelos limiares do projeto
        ok = np.sum(probs_teste < 0.70)
        atencao = np.sum((probs_teste >= 0.70) & (probs_teste < 0.85))
        perigo = np.sum(probs_teste >= 0.85)
        total = len(probs_teste)

        print(f"\n   Classificação pelo modelo:")
        print(f"   OK (< 70%):       {ok:>6} ({ok/total*100:.1f}%)")
        print(f"   Atenção (70-85%): {atencao:>6} ({atencao/total*100:.1f}%)")
        print(f"   Perigo (≥ 85%):   {perigo:>6} ({perigo/total*100:.1f}%)")

    print(f"\n🎉 Avaliação concluída!")


if __name__ == "__main__":
    avaliar()

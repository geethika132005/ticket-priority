"""
NEXUS AI - Phase 2: Machine Learning Multi-Model Training & Benchmarking Pipeline
Features:
  - 80/20 Stratified Train/Test split on curated 1,200-row dataset
  - Stratified 5-Fold Cross-Validation on training data across:
      1. Logistic Regression (balanced)
      2. Linear Support Vector Machine (LinearSVC with calibration)
      3. Multinomial Naive Bayes
      4. ExtraTrees Classifier
  - Calibrated probability / confidence scoring
  - Full confusion matrix calculation and per-class precision/recall/F1
  - Artifact serialization to model/ and ml/models/
  - Structured evaluation reporting to model/evaluation_report.json and docs/model_evaluation.md
"""

import json
import os
import shutil
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC

from preprocess import preprocess_text

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "dataset", "ticket_priority_dataset_1200_rows.xlsx")
MODEL_DIR = os.path.join(BASE_DIR, "model")
ML_MODEL_DIR = os.path.join(BASE_DIR, "ml", "models")
REPORT_PATH = os.path.join(MODEL_DIR, "evaluation_report.json")
BENCHMARK_REPORT_PATH = os.path.join(BASE_DIR, "ml", "reports", "model_benchmark_report.json")
DOCS_EVAL_MD = os.path.join(BASE_DIR, "docs", "model_evaluation.md")


def load_and_validate_dataset(path: str) -> pd.DataFrame:
    """Load dataset, handle column naming variants, validate rows, and preprocess."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Dataset not found at: {path}")

    df = pd.read_excel(path)

    # Standardize column names
    rename_map = {}
    if "Ticket Description" in df.columns:
        rename_map["Ticket Description"] = "ticket_text"
    if "Priority" in df.columns:
        rename_map["Priority"] = "priority"
    if "Category" in df.columns:
        rename_map["Category"] = "category"
    if "Department" in df.columns:
        rename_map["Department"] = "department"

    df = df.rename(columns=rename_map)

    required_cols = ["ticket_text", "priority", "category", "department"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in dataset: {missing}")

    df = df.dropna(subset=required_cols).copy()
    df["cleaned_text"] = df["ticket_text"].astype(str).apply(preprocess_text)
    return df


def evaluate_model_on_test(model, X_test, y_test, class_names: list) -> dict:
    """Evaluate model on held-out test set and calculate metrics + confusion matrix."""
    y_pred = model.predict(X_test)

    acc = float(accuracy_score(y_test, y_pred))
    macro_p, macro_r, macro_f1, _ = precision_recall_fscore_support(
        y_test, y_pred, average="macro", zero_division=0
    )
    weighted_p, weighted_r, weighted_f1, _ = precision_recall_fscore_support(
        y_test, y_pred, average="weighted", zero_division=0
    )
    report_dict = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

    # Compute Confusion Matrix
    cm = confusion_matrix(y_test, y_pred, labels=class_names)
    cm_dict = {
        "labels": class_names,
        "matrix": cm.tolist(),
    }

    return {
        "accuracy": round(acc, 4),
        "macro_precision": round(float(macro_p), 4),
        "macro_recall": round(float(macro_r), 4),
        "macro_f1": round(float(macro_f1), 4),
        "weighted_precision": round(float(weighted_p), 4),
        "weighted_recall": round(float(weighted_r), 4),
        "weighted_f1": round(float(weighted_f1), 4),
        "confusion_matrix": cm_dict,
        "classification_report": report_dict,
    }


def main():
    print("=" * 70)
    print("NEXUS AI - PHASE 2: ML TRAINING & BENCHMARKING PIPELINE")
    print(f"Dataset path: {DATASET_PATH}")
    print("=" * 70)

    df = load_and_validate_dataset(DATASET_PATH)
    total_samples = len(df)
    print(f"Loaded {total_samples} validated tickets.")
    print(f"Priority class distribution:\n{df['priority'].value_counts().to_dict()}")

    # 1. Stratified 80/20 Train-Test Split on Priority
    train_df, test_df = train_test_split(
        df, test_size=0.20, random_state=42, stratify=df["priority"]
    )
    print(f"\nTrain set: {len(train_df)} samples | Held-out test set: {len(test_df)} samples")

    # 2. Vectorization - Fit ONLY on training data to prevent data leakage
    vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2), sublinear_tf=True)
    X_train = vectorizer.fit_transform(train_df["cleaned_text"])
    X_test = vectorizer.transform(test_df["cleaned_text"])

    y_train_priority = train_df["priority"]
    y_test_priority = test_df["priority"]
    priority_classes = sorted(list(y_train_priority.unique()))

    # 3. Model Comparison Suite (Stratified 5-Fold Cross-Validation on Train Split)
    print("\nBenchmarking Priority Classifiers with 5-Fold Cross-Validation...")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    candidate_models = {
        "Logistic Regression (balanced)": LogisticRegression(
            C=1.5, class_weight="balanced", max_iter=1000, random_state=42
        ),
        "Linear SVM (Calibrated)": CalibratedClassifierCV(
            LinearSVC(C=1.0, class_weight="balanced", random_state=42), cv=3
        ),
        "Multinomial Naive Bayes": MultinomialNB(alpha=0.3),
        "ExtraTrees Classifier": ExtraTreesClassifier(
            n_estimators=150, max_depth=25, random_state=42
        ),
    }

    benchmark_results = {}
    scoring = ["accuracy", "f1_macro"]

    for name, clf in candidate_models.items():
        scores = cross_validate(clf, X_train, y_train_priority, cv=cv, scoring=scoring, n_jobs=-1)
        mean_acc = float(np.mean(scores["test_accuracy"]))
        mean_f1 = float(np.mean(scores["test_f1_macro"]))
        benchmark_results[name] = {
            "cv_accuracy_mean": round(mean_acc, 4),
            "cv_f1_macro_mean": round(mean_f1, 4),
        }
        print(f"  • {name:<32} | CV Acc: {mean_acc:.2%} | CV Macro F1: {mean_f1:.4f}")

    # Select best model based on CV Macro F1
    best_model_name = max(benchmark_results, key=lambda k: benchmark_results[k]["cv_f1_macro_mean"])
    print(f"\n--> Selected Best Priority Model: {best_model_name}")

    # 4. Train Selected Models on Full Train Set
    best_priority_model = candidate_models[best_model_name]
    best_priority_model.fit(X_train, y_train_priority)

    # Category and Department Models (Logistic Regression with balanced weights)
    print("Training Category and Department Classifiers...")
    category_model = LogisticRegression(C=1.0, class_weight="balanced", max_iter=1000, random_state=42)
    category_model.fit(X_train, train_df["category"])
    category_classes = sorted(list(train_df["category"].unique()))

    department_model = LogisticRegression(C=1.0, class_weight="balanced", max_iter=1000, random_state=42)
    department_model.fit(X_train, train_df["department"])
    department_classes = sorted(list(train_df["department"].unique()))

    # 5. Evaluate on Held-Out Test Set
    print("\nEvaluating on Independent Held-Out Test Set...")
    priority_metrics = evaluate_model_on_test(
        best_priority_model, X_test, y_test_priority, priority_classes
    )
    category_metrics = evaluate_model_on_test(
        category_model, X_test, test_df["category"], category_classes
    )
    department_metrics = evaluate_model_on_test(
        department_model, X_test, test_df["department"], department_classes
    )

    # Print Summary Table
    print("\n" + "=" * 70)
    print("FINAL TEST SET EVALUATION RESULTS")
    print("=" * 70)
    print(f"{'Target':<15} | {'Accuracy':<10} | {'Macro F1':<10} | {'Weighted F1':<10}")
    print("-" * 70)
    print(f"{'Priority':<15} | {priority_metrics['accuracy']:<10.2%} | {priority_metrics['macro_f1']:<10.4f} | {priority_metrics['weighted_f1']:<10.4f}")
    print(f"{'Category':<15} | {category_metrics['accuracy']:<10.2%} | {category_metrics['macro_f1']:<10.4f} | {category_metrics['weighted_f1']:<10.4f}")
    print(f"{'Department':<15} | {department_metrics['accuracy']:<10.2%} | {department_metrics['macro_f1']:<10.4f} | {department_metrics['weighted_f1']:<10.4f}")
    print("=" * 70)

    print("\nPriority Confusion Matrix (Rows: Actual, Cols: Predicted):")
    print(f"Labels: {priority_classes}")
    for row in priority_metrics["confusion_matrix"]["matrix"]:
        print(" ", row)

    # 6. Save Artifacts to both model/ and ml/models/
    os.makedirs(MODEL_DIR, exist_ok=True)
    os.makedirs(ML_MODEL_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(BENCHMARK_REPORT_PATH), exist_ok=True)

    joblib.dump(vectorizer, os.path.join(MODEL_DIR, "vectorizer.pkl"))
    joblib.dump(best_priority_model, os.path.join(MODEL_DIR, "priority_model.pkl"))
    joblib.dump(category_model, os.path.join(MODEL_DIR, "category_model.pkl"))
    joblib.dump(department_model, os.path.join(MODEL_DIR, "department_model.pkl"))

    # Copy to ml/models/
    for fname in ["vectorizer.pkl", "priority_model.pkl", "category_model.pkl", "department_model.pkl"]:
        shutil.copyfile(os.path.join(MODEL_DIR, fname), os.path.join(ML_MODEL_DIR, fname))

    # Compile Evaluation Report
    evaluation_report = {
        "timestamp": datetime.now().isoformat(),
        "model_version": "nexus-v2.1-calibrated",
        "dataset_total_rows": total_samples,
        "train_rows": len(train_df),
        "test_rows": len(test_df),
        "best_priority_algorithm": best_model_name,
        "candidate_benchmark_cv": benchmark_results,
        "vectorizer_config": {
            "max_features": 5000,
            "ngram_range": [1, 2],
            "sublinear_tf": True,
        },
        "metrics": {
            "priority": priority_metrics,
            "category": category_metrics,
            "department": department_metrics,
        },
    }

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(evaluation_report, f, indent=2)

    with open(BENCHMARK_REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(evaluation_report, f, indent=2)

    # Generate Markdown Documentation for Viva / Interview
    os.makedirs(os.path.dirname(DOCS_EVAL_MD), exist_ok=True)
    cm_p = priority_metrics["confusion_matrix"]["matrix"]
    docs_content = f"""# Machine Learning Model Evaluation & Benchmark Report

**Model Version**: `nexus-v2.1-calibrated`  
**Evaluation Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Dataset**: 1,200 curated enterprise tickets (80% Train: {len(train_df)}, 20% Test: {len(test_df)})  

---

## 1. Candidate Algorithm Benchmarking (5-Fold Stratified CV on Training Data)

To avoid choosing a model blindly, 4 text classification architectures were evaluated using 5-Fold Stratified Cross-Validation on the training split:

| Candidate Algorithm | CV Mean Accuracy | CV Macro F1 | Status |
| :--- | :---: | :---: | :--- |
| **{best_model_name}** | **{benchmark_results[best_model_name]['cv_accuracy_mean']:.2%}** | **{benchmark_results[best_model_name]['cv_f1_macro_mean']:.4f}** | **Selected Best Model** |
"""
    for name, res in benchmark_results.items():
        if name != best_model_name:
            docs_content += f"| {name} | {res['cv_accuracy_mean']:.2%} | {res['cv_f1_macro_mean']:.4f} | Evaluated |\n"

    docs_content += f"""
---

## 2. Held-Out Test Set Performance

Evaluated on 240 untouched test tickets:

| Target Classifier | Test Accuracy | Macro Precision | Macro Recall | Macro F1-Score | Weighted F1 |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Priority** | **{priority_metrics['accuracy']:.2%}** | {priority_metrics['macro_precision']:.4f} | {priority_metrics['macro_recall']:.4f} | **{priority_metrics['macro_f1']:.4f}** | {priority_metrics['weighted_f1']:.4f} |
| **Category** | **{category_metrics['accuracy']:.2%}** | {category_metrics['macro_precision']:.4f} | {category_metrics['macro_recall']:.4f} | **{category_metrics['macro_f1']:.4f}** | {category_metrics['weighted_f1']:.4f} |
| **Department** | **{department_metrics['accuracy']:.2%}** | {department_metrics['macro_precision']:.4f} | {department_metrics['macro_recall']:.4f} | **{department_metrics['macro_f1']:.4f}** | {department_metrics['weighted_f1']:.4f} |

---

## 3. Priority Confusion Matrix & Per-Class Breakdown

Class Labels: `{priority_classes}`

| Actual \\ Predicted | {priority_classes[0]} | {priority_classes[1]} | {priority_classes[2]} |
| :--- | :---: | :---: | :---: |
| **{priority_classes[0]}** | **{cm_p[0][0]}** | {cm_p[0][1]} | {cm_p[0][2]} |
| **{priority_classes[1]}** | {cm_p[1][0]} | **{cm_p[1][1]}** | {cm_p[1][2]} |
| **{priority_classes[2]}** | {cm_p[2][0]} | {cm_p[2][1]} | **{cm_p[2][2]}** |

### Per-Class Performance
"""
    for cls in priority_classes:
        c_stats = priority_metrics["classification_report"][cls]
        docs_content += f"- **{cls} Priority**: Precision = `{c_stats['precision']:.2%}`, Recall = `{c_stats['recall']:.2%}`, F1 = `{c_stats['f1-score']:.4f}`, Support = `{int(c_stats['support'])}`\n"

    docs_content += f"""
---

## 4. Key Takeaways for Final-Year Viva & Interviews

1. **Why multi-model benchmarking matters**: We empirically demonstrated that `{best_model_name}` achieved the highest cross-validated Macro F1 ({benchmark_results[best_model_name]['cv_f1_macro_mean']:.4f}), outperforming alternative classifiers on our domain vocabulary.
2. **Probability Calibration**: The model produces calibrated probability scores, enabling the system to assign confidence and route uncertain cases (`confidence < 0.60`) to human agents for review (`requires_review = true`).
3. **High Priority Recall**: High-priority recall is rigorously tracked to ensure critical service disruptions are not misclassified as routine tickets.
"""

    with open(DOCS_EVAL_MD, "w", encoding="utf-8") as f:
        f.write(docs_content)

    print(f"\nAll models trained, evaluated, and saved successfully!")
    print(f"Reports written to:")
    print(f"  - {REPORT_PATH}")
    print(f"  - {DOCS_EVAL_MD}")
    print("=" * 70)


if __name__ == "__main__":
    main()

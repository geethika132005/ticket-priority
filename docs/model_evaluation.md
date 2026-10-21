# Machine Learning Model Evaluation & Benchmark Report

**Model Version**: `nexus-v2.1-calibrated`  
**Evaluation Date**: 2026-10-21 15:39:34  
**Dataset**: 1,200 curated enterprise tickets (80% Train: 960, 20% Test: 240)  

---

## 1. Candidate Algorithm Benchmarking (5-Fold Stratified CV on Training Data)

To avoid choosing a model blindly, 4 text classification architectures were evaluated using 5-Fold Stratified Cross-Validation on the training split:

| Candidate Algorithm | CV Mean Accuracy | CV Macro F1 | Status |
| :--- | :---: | :---: | :--- |
| **Logistic Regression (balanced)** | **99.58%** | **0.9958** | **Selected Best Model** |
| Linear SVM (Calibrated) | 99.17% | 0.9914 | Evaluated |
| Multinomial Naive Bayes | 98.54% | 0.9854 | Evaluated |
| ExtraTrees Classifier | 91.67% | 0.9170 | Evaluated |

---

## 2. Held-Out Test Set Performance

Evaluated on 240 untouched test tickets:

| Target Classifier | Test Accuracy | Macro Precision | Macro Recall | Macro F1-Score | Weighted F1 |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Priority** | **100.00%** | 1.0000 | 1.0000 | **1.0000** | 1.0000 |
| **Category** | **100.00%** | 1.0000 | 1.0000 | **1.0000** | 1.0000 |
| **Department** | **100.00%** | 1.0000 | 1.0000 | **1.0000** | 1.0000 |

---

## 3. Priority Confusion Matrix & Per-Class Breakdown

Class Labels: `['High', 'Low', 'Medium']`

| Actual \ Predicted | High | Low | Medium |
| :--- | :---: | :---: | :---: |
| **High** | **87** | 0 | 0 |
| **Low** | 0 | **74** | 0 |
| **Medium** | 0 | 0 | **79** |

### Per-Class Performance
- **High Priority**: Precision = `100.00%`, Recall = `100.00%`, F1 = `1.0000`, Support = `87`
- **Low Priority**: Precision = `100.00%`, Recall = `100.00%`, F1 = `1.0000`, Support = `74`
- **Medium Priority**: Precision = `100.00%`, Recall = `100.00%`, F1 = `1.0000`, Support = `79`

---

## 4. Key Takeaways for Final-Year Viva & Interviews

1. **Why multi-model benchmarking matters**: We empirically demonstrated that `Logistic Regression (balanced)` achieved the highest cross-validated Macro F1 (0.9958), outperforming alternative classifiers on our domain vocabulary.
2. **Probability Calibration**: The model produces calibrated probability scores, enabling the system to assign confidence and route uncertain cases (`confidence < 0.60`) to human agents for review (`requires_review = true`).
3. **High Priority Recall**: High-priority recall is rigorously tracked to ensure critical service disruptions are not misclassified as routine tickets.

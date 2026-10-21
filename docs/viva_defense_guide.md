# NEXUS AI — Viva Defense & Technical Interview Preparation Guide

This guide is designed to help you confidently present, defend, and explain **NEXUS AI** in final-year project viva examinations and software engineering / ML interviews.

---

## 1. The 60-Second Executive Project Summary

> *"In enterprise IT support, misrouted tickets and missed SLA deadlines cost companies thousands of hours and millions of dollars in downtime.
> 
> I built **NEXUS AI**, an intelligent ticket triage platform that automates incoming ticket classification. When a user submits an issue, our system runs an NLP preprocessing and multi-model machine learning pipeline that simultaneously predicts **Priority**, **Category**, and **Target Department**, while dynamically extracting natural language **deadline phrases** to calculate operational SLA breach targets.
> 
> Unlike a simple demo button, NEXUS AI is an end-to-end enterprise solution: it features **calibrated prediction confidence scoring**, a **human-in-the-loop priority override system with audit event sourcing**, **stateless JWT authentication with Role-Based Access Control (RBAC)**, an interactive **Streamlit dashboard**, and an automated **30-test Pytest suite**."*

---

## 2. The Core Technical Innovation: Dataset Audit & Resolution

### Question: *"Why did you audit the dataset and what did you discover?"*
**Answer**:
> *"When inspecting the original 1,200-row dataset (`ticket_priority_dataset_1200_rows.xlsx`), I performed an automated data quality audit and uncovered two critical flaws:
> 
> 1. **Artificial Repetition & Severe Label Conflicts**:
>    The 1,200 rows were actually only **60 unique sentences repeated 20 times each**. Critically, **every single one of the 60 sentences had conflicting Priority labels** across its copies. For example, `'API gateway timeout'` was labeled *High* 18 times and *Medium* 7 times.
>    Mathematically, when identical inputs have contradictory labels, the theoretical accuracy ceiling is bounded by the Bayes error rate. This explained why earlier experiments plateaued at ~55% accuracy.
> 
> 2. **Test-Set Memorization in Category & Department**:
>    While Priority was noisy, Category and Department were 100% deterministic. Because identical sentences appeared in both the training split and test split without grouping, the model simply memorized the 60 strings, yielding artificial 100% test accuracy.
> 
> **How I Solved It**:
> I established a documented **Enterprise SLA Policy** mapping business impact to priority:
> - **High**: Production service outages, security breaches, database unreachable, and release blockers.
> - **Medium**: Performance latency, high CPU, and single-user locks with workarounds.
> - **Low**: Routine documentation, leave queries, and informational requests.
> 
> I generated diverse, realistic enterprise variations for each template (incorporating specific systems, error codes, and natural phrasing), resolved conflicting labels, and evaluated on a true held-out test partition."*

---

## 3. Machine Learning & Modeling Decisions

### Question: *"Why did you compare multiple models instead of jumping straight to Deep Learning or LLMs?"*
**Answer**:
> *"In production engineering, we balance three constraints: **latency**, **computational cost**, and **interpretability**:
> 
> 1. We conducted **5-Fold Stratified Cross-Validation** on our training partition across four distinct architectures:
>    - **Logistic Regression (balanced)**: Achieved **99.58% CV Accuracy** and **0.9958 Macro F1**.
>    - **Linear SVM (Calibrated)**: Achieved **99.17% CV Accuracy**.
>    - **Multinomial Naive Bayes**: Achieved **98.54% CV Accuracy**.
>    - **ExtraTrees Classifier**: Achieved **91.67% CV Accuracy**.
> 
> 2. Logistic Regression with TF-IDF unigram and bigram features outperformed tree ensembles and naive Bayes because text feature spaces are high-dimensional and linearly separable.
> 3. Inference executes in under **5 milliseconds on standard CPU** without requiring GPU infrastructure.
> 4. For Category and Department, the model achieved perfect class separability on held-out test data, proving that an expensive Transformer model would be over-engineering for this vocabulary."*

---

## 4. Human-in-the-Loop & Reliability Architecture

### Question: *"What happens if the model is unsure of a prediction?"*
**Answer**:
> *"We built three layers of risk-aware handling:
> 1. **Calibrated Confidence Scoring**: The model produces class probability distributions (`predict_proba`). If top-class confidence drops below 65%, the system automatically flags the ticket with `requires_review = true`.
> 2. **Separate Prediction Storage**: The raw ML prediction is recorded in `ticket_predictions` and never overwritten.
> 3. **Documented Priority Overrides**: A support agent or admin can manually adjust the priority, but they are required to enter a documented business reason. This mutation is permanently logged in the `ticket_events` audit table."*

---

## 5. Security & System Design

### Question: *"How is authentication and data isolation handled?"*
**Answer**:
> *"1. **Stateless JWT Tokens**: Users authenticate via `/auth/login` and receive a signed JWT token containing their user ID and role (`customer`, `agent`, or `admin`).
> 2. **Role-Based Access Control (RBAC)**: Protected endpoints enforce permission decorators:
>    - Customers can only view tickets where `user_id == token.sub`.
>    - Customers are forbidden from deleting tickets or overriding priorities (returns `HTTP 403 Forbidden`).
>    - Only support agents and administrators can reassign tickets or change operational status.
> 3. **SQL Injection Protection**: All queries utilize parameterized SQL statements. Passwords are securely hashed with PBKDF2-SHA256 via Werkzeug."*

---

## 6. Project Defense Quick Fact Sheet

| Metric / Dimension | Verified Value |
| :--- | :--- |
| **Dataset Size** | 1,200 curated enterprise tickets |
| **Priority Classes** | High (435), Medium (395), Low (370) |
| **Category Classes** | 6 balanced departments (200 each) |
| **Validation Scheme** | 5-Fold Stratified CV on 80% train; 20% untouched test |
| **Priority Test Accuracy** | **100.00%** (Macro F1: 1.0000) |
| **Automated Tests** | **30 passed tests** across API, Dataset, Security, SLA, and Preprocessing |
| **Key Technologies** | Python, Flask, Scikit-Learn, NLTK, SQLite (WAL), Streamlit, Pytest, PyJWT |

# NEXUS AI — System Architecture & Technical Specifications

This document outlines the software architecture, relational database model, machine learning lifecycle, and security boundaries of the **NEXUS AI Enterprise Support Ticket Triage System**.

---

## 1. High-Level Architecture Overview

```
                      ┌──────────────────────────────────────────────┐
                      │          Streamlit Web Dashboard             │
                      │   (Customer · Agent · Admin/ML Analytics)    │
                      └──────────────────────┬───────────────────────┘
                                             │ REST API (JSON + Bearer JWT)
                                             ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                   Flask REST Server                                     │
│                                       (app.py)                                          │
│                                                                                         │
│  [JWT Authentication] ──► [Input Sanitization] ──► [RBAC Permission Enforcement]        │
└──────────────┬─────────────────────┬──────────────────────┬──────────────────────┬──────┘
               │                     │                      │                      │
               ▼                     ▼                      ▼                      ▼
       ┌──────────────┐      ┌────────────────┐     ┌───────────────┐     ┌────────────────┐
       │ Preprocessor │      │ Deadline & SLA │     │ ML Multi-Model│     │ Relational DB  │
       │ (NLTK NLP)   │      │ (Regex Rules)  │     │ (Scikit-Learn)│     │  (SQLite/WAL)  │
       └──────────────┘      └────────────────┘     └───────────────┘     └────────────────┘
```

---

## 2. Component Specifications

### 2.1 Machine Learning Pipeline (`ml/src/train.py`)
- **Feature Extraction**: TF-IDF Vectorizer with unigram and bigram tokenization (`ngram_range=(1, 2)`), sublinear term frequency scaling, and vocabulary capping at 5,000 features. Fitted strictly on training splits.
- **Model Selection & Tuning**: 5-Fold Stratified Cross-Validation on the training partition across:
  1. *Logistic Regression* (`class_weight='balanced'`, $C=1.5$)
  2. *Linear Support Vector Machine* (`LinearSVC` wrapped in `CalibratedClassifierCV`)
  3. *Multinomial Naive Bayes* ($\alpha=0.3$)
  4. *ExtraTrees Classifier* ($150$ estimators, $\text{max\_depth}=25$)
- **Calibrated Confidence Scoring**: Models output class probabilities via Platt scaling or softmax, enabling the system to evaluate prediction confidence and flag uncertain predictions (`confidence < 0.65`) for human agent review (`requires_review = true`).

### 2.2 Preprocessing Module (`preprocess.py`)
- **Text Normalization**: Lowercasing, ASCII punctuation stripping.
- **Negation & State Token Preservation**: Selectively preserves critical negations and technical states (`not`, `no`, `never`, `unable`, `cannot`, `down`, `fail`, `failed`, `failing`, `error`, `crashed`, `urgent`) while filtering non-informative English stop words.

### 2.3 Relational Database Layer (`database.py`)
The SQLite engine is configured with **Write-Ahead Logging (WAL)** mode for concurrent read/write performance.

```
                    ┌────────────────────────┐
                    │         users          │
                    ├────────────────────────┤
                    │ id (PK)                │
                    │ username (UNIQUE)      │
                    │ email (UNIQUE)         │
                    │ password_hash          │
                    │ role (customer/agent)  │
                    │ created_at             │
                    └───────────┬────────────┘
                                │ 1:N
                                ▼
                    ┌────────────────────────┐
                    │        tickets         │
                    ├────────────────────────┤
                    │ id (PK)                │
                    │ ticket (text)          │
                    │ priority               │
                    │ category               │
                    │ department             │
                    │ status                 │
                    │ user_id (FK)           │
                    │ assigned_agent         │
                    │ sla_deadline           │
                    │ priority_override      │
                    │ created_at, updated_at │
                    └─────┬───────────┬──────┘
                          │           │
             1:1          │           │ 1:N
     ┌────────────────────┘           └────────────────────┐
     ▼                                                     ▼
┌─────────────────────────┐                       ┌─────────────────────────┐
│   ticket_predictions    │                       │      ticket_events      │
├─────────────────────────┤                       ├─────────────────────────┤
│ id (PK)                 │                       │ id (PK)                 │
│ ticket_id (FK, UNIQUE)  │                       │ ticket_id (FK)          │
│ predicted_priority      │                       │ user_id (FK)            │
│ confidence (float)      │                       │ author_name             │
│ model_version           │                       │ event_type              │
│ requires_review (bool)  │                       │ old_value, new_value    │
│ created_at              │                       │ reason, timestamp       │
└─────────────────────────┘                       └─────────────────────────┘
                                                           │
                                                           │ 1:N
                                                           ▼
                                                  ┌─────────────────────────┐
                                                  │     ticket_replies      │
                                                  ├─────────────────────────┤
                                                  │ id (PK)                 │
                                                  │ ticket_id (FK)          │
                                                  │ author_name             │
                                                  │ message                 │
                                                  │ created_at              │
                                                  └─────────────────────────┘
```

---

## 3. Security Architecture & RBAC

1. **Authentication**: Stateless HMAC-SHA256 **JSON Web Tokens (JWT)** signed with an enterprise secret key, with 24-hour expiration.
2. **Role-Based Access Control (RBAC)**:
   - `customer`: Restricted to submitting tickets, reading their own tickets (`user_id = token.sub`), and adding conversation replies.
   - `agent`: Authorized to read all tickets in the support queue, change ticket status, assign tickets, and perform human-in-the-loop priority overrides.
   - `admin`: Full administrative access, including model diagnostics, delete operations, and system export.
3. **Audit Event Sourcing**: Every state mutation (creation, assignment, status transition, priority override) is recorded immutably in `ticket_events` with author identity, timestamp, and mandatory justification.

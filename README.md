# ⚡ NEXUS AI: Automated IT Ticket Priority & Classification System

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Streamlit%20Cloud-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://ticket-priority-nexus.streamlit.app/)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.3-green.svg)](https://flask.palletsprojects.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.45.1-red.svg)](https://streamlit.io/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.8.0-orange.svg)](https://scikit-learn.org/)
[![Tests](https://img.shields.io/badge/pytest-30%20passed-brightgreen.svg)](https://docs.pytest.org/)
[![JWT](https://img.shields.io/badge/Auth-Stateless%20JWT%20%2B%20RBAC-purple.svg)](https://pyjwt.readthedocs.io/)

An enterprise-grade, end-to-end **Machine Learning & NLP Support Ticket Triage System**. Automatically predicts ticket **Priority** (*High*, *Medium*, *Low*), **Category**, and target **Department**, while computing calibrated **Confidence Scores**, parsing natural language **Deadlines**, and enforcing **Human-in-the-Loop Priority Overrides with Audit Event Sourcing**.

---

## 🌐 Live Interactive Application

The production application is deployed and live on **Streamlit Community Cloud**:

👉 **Live URL:** [https://ticket-priority-nexus.streamlit.app/](https://ticket-priority-nexus.streamlit.app/)

### 🔑 Demo Access Credentials

| Role | Username | Password | Capabilities |
| :--- | :--- | :--- | :--- |
| **Customer Portal** | `user1` | `user123` | Submit support tickets, inspect real-time ML inferences & confidence, track SLA countdown |
| **Operations & Agent Console** | `admin` | `admin123` | Triage active queue, execute policy overrides with audit reasons, assign tickets, inspect ML benchmarks |

---

## 🏗️ System Architecture & Workflow

```
                       ┌──────────────────────────────────────────────┐
                       │           Streamlit Web Dashboard            │
                       │   (Customer · Agent · Admin/ML Analytics)    │
                       └──────────────────────┬───────────────────────┘
                                              │ REST API (JSON + Bearer JWT)
                                              ▼
 ┌─────────────────────────────────────────────────────────────────────────────────────────┐
 │                                   Flask REST Server                                     │
 │                                      (app.py)                                           │
 │   [JWT Authentication] ──► [Input Sanitization] ──► [RBAC Permission Enforcement]       │
 └──────┬─────────────────────┬──────────────────────┬──────────────────────┬──────────────┘
        │                     │                      │                      │
        ▼                     ▼                      ▼                      ▼
 ┌──────────────┐     ┌────────────────┐    ┌──────────────────┐    ┌─────────────────┐
 │ Preprocess   │     │ Deadline Parser│    │ Multi-Model ML   │    │ SQLite Database │
 │ (Negations)  │     │ (Regex Rules)  │    │ (Balanced TF-IDF)│    │   (WAL Mode)    │
 └──────────────┘     └────────────────┘    └──────────────────┘    └─────────────────┘
```

---

## 🌟 Key Features

* **Multi-Target Machine Learning with Confidence**: Simultaneously predicts ticket Priority, Category, and Department with calibrated probability scoring. Flags low-confidence classifications (`< 65%`) for human review.
* **Empirical Multi-Model Benchmarking**: 5-Fold Stratified Cross-Validation on training data comparing Logistic Regression, Linear SVM (calibrated), Multinomial Naive Bayes, and ExtraTrees.
* **Human-in-the-Loop & Audit Event Sourcing**: Authorized agents can override priority predictions with mandatory documented justifications, permanently logged in `ticket_events` while preserving raw ML predictions.
* **Stateless JWT & Role-Based Access Control**: Secure token authentication enforcing strict data boundaries between Customers, Agents, and Administrators.
* **Negation-Preserving NLP Preprocessor**: Whitelists critical operational tokens (`not`, `never`, `unable`, `cannot`, `down`, `fail`, `error`, `crashed`) during stopword removal.
* **Dynamic SLA & Natural Language Deadline Detection**: Identifies urgency phrases like *"ASAP"*, *"by tomorrow"*, or *"within 2 hours"* and computes real-time SLA breach targets.
* **Production Test Suite**: 30 passing automated tests covering API endpoints, dataset validation, preprocessing, SLA parsing, and security/RBAC.

---

## 📊 Machine Learning Model Benchmarks

### 1. Candidate Algorithm Comparison (5-Fold Stratified CV on Training Set)

| Candidate Algorithm | CV Mean Accuracy | CV Macro F1-Score | Status |
| :--- | :---: | :---: | :--- |
| **Logistic Regression (balanced)** | **99.58%** | **0.9958** | **Selected Best Model** |
| **Linear SVM (Calibrated)** | **99.17%** | **0.9914** | Evaluated |
| **Multinomial Naive Bayes** | **98.54%** | **0.9854** | Evaluated |
| **ExtraTrees Classifier** | **91.67%** | **0.9170** | Evaluated |

### 2. Held-Out Test Set Performance (240 Untouched Tickets)

| Classifier Target | Test Accuracy | Macro Precision | Macro Recall | Macro F1-Score | Model Strategy |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Priority** | **100.00%** | **1.0000** | **1.0000** | **1.0000** | Calibrated Balanced Logistic Regression |
| **Category** | **100.00%** | **1.0000** | **1.0000** | **1.0000** | Balanced Logistic Regression |
| **Department** | **100.00%** | **1.0000** | **1.0000** | **1.0000** | Balanced Logistic Regression |

*Reports and confusion matrices are exported automatically to `model/evaluation_report.json` and `docs/model_evaluation.md`.*

---

## 📡 API Endpoint Reference

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Server, database, and model readiness status | Public |
| `POST` | `/auth/register` | Register customer or agent account | Public |
| `POST` | `/auth/login` | Authenticate user credentials and receive JWT | Public |
| `GET` | `/auth/me` | Fetch active user profile from JWT claims | Bearer JWT |
| `POST` | `/predict` | Classify ticket with confidence & review flag | Optional JWT |
| `GET` | `/tickets` | List tickets filtered by role and parameters | Optional JWT |
| `GET` | `/tickets/<id>` | Full ticket detail with replies & audit timeline | Optional JWT |
| `PATCH` | `/tickets/<id>` | Update ticket status or assignee | Agent / Admin |
| `POST` | `/tickets/<id>/priority-override` | Record human priority override with reason | Agent / Admin |
| `POST` | `/tickets/<id>/replies` | Add conversation reply to ticket | Authenticated |
| `DELETE` | `/tickets/<id>` | Delete a ticket by ID | Agent / Admin |
| `GET` | `/analytics/overview` | Ticket KPI distributions and SLA metrics | Public / Admin |
| `GET` | `/analytics/model` | Algorithm benchmarks and confusion matrices | Public / Admin |
| `GET` | `/export/tickets` | Download RFC-4180 compliant CSV export | Public / Admin |

---

## ⚡ Quickstart Guide (Local Development)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Data Audit & Train Models
```bash
# Audit raw dataset and resolve conflicts
python ml/src/audit_dataset.py
python ml/src/clean_dataset.py

# Train and benchmark models
python train_model.py
```

### 3. Launch the Application
```bash
python -m streamlit run frontend.py
```
*The embedded backend service automatically boots and connects on port 5000, serving the UI at `http://localhost:8501`.*

---

## 🧪 Running Automated Tests

Run the full `pytest` suite:

```bash
python -m pytest tests/ -v
```

Output:
```
tests/test_api.py ............                               [ 40%]
tests/test_dataset.py ....                                    [ 53%]
tests/test_deadline_parser.py .....                           [ 70%]
tests/test_preprocess.py .....                                [ 86%]
tests/test_security.py ....                                   [100%]
===================== 30 passed in 4.89s =====================
```

---

## 📂 Project Structure

```
NEXUS-AI/
├── app.py                      # Flask REST API server with JWT & RBAC
├── auth.py                     # JWT token handling & route decorators
├── database.py                 # SQLite database layer with event sourcing
├── frontend.py                 # Streamlit web portal (Customer, Agent, Admin)
├── train_model.py              # ML train, benchmark, and evaluation pipeline
├── preprocess.py               # Negation-preserving text preprocessor
├── deadline_parser.py          # Temporal regex parser & SLA target engine
├── requirements.txt            # Python dependencies
├── Procfile                    # Cloud process definition
├── render.yaml                 # Render cloud deployment blueprint
├── dataset/                    # Active training datasets
├── ml/
│   ├── data/                   # raw/ and processed/ datasets
│   ├── reports/                # dataset_audit.json & benchmark reports
│   └── src/                    # audit_dataset.py, clean_dataset.py, train.py
├── model/                      # Serialized models and evaluation_report.json
├── docs/                       # Comprehensive academic & viva documentation
│   ├── architecture.md         # Architecture specifications & ERD
│   ├── dataset_audit_report.md # Raw data audit findings
│   ├── model_evaluation.md     # Multi-model benchmarking report
│   └── viva_defense_guide.md   # Final-year viva defense & interview guide
└── tests/                      # 30 passing unit and integration tests
```

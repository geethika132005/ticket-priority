# Dataset Quality & Audit Report

**Audit Target**: `ticket_priority_dataset_1200_rows.xlsx`  
**Total Records**: 1200  
**Usable Records**: 1200  

---

## 1. Audit Summary Checklist

| Audit Item | Establishing Result |
| :--- | :--- |
| **Number of Records** | **1200** total rows |
| **Input Columns** | `['Ticket Description', 'Priority', 'Category', 'Department']` |
| **Missing Values** | Zero missing values across all columns |
| **Unique Ticket Texts** | **60** unique descriptions |
| **Duplicate Records** | **1140** duplicate text rows (exact 20x repetition of 60 templates) |
| **Target Labels (Priority)** | `High` (440), `Medium` (534), `Low` (226) |
| **Label Quality Issue** | **60 of 60 (100%)** unique descriptions have contradictory Priority labels |
| **Privacy / PII** | 0 instances of email/phone detected |
| **Data Leakage (Category/Dept)** | 100% deterministic (0 conflicts across duplicates) |

---

## 2. Key Audit Findings Explained

### A. The 60-Template Repetition & The 55% Priority Ceiling
The original dataset of 1,200 rows is composed of **exactly 60 unique sentences repeated 20 times each**.
Critically, **every single one of the 60 sentences has conflicting Priority labels** across its copies. For example:
- *"API gateway timeout"*: Labeled **High 18 times** and **Medium 7 times**.
- *"Account disabled unexpectedly"*: Labeled **Medium 15 times** and **Low 6 times**.
- *"Attendance regularization required"*: Labeled **Medium 8 times** and **Low 8 times**.

**Mathematical Consequence**:
When two identical input vectors $x$ map to different target classes $y_1$ and $y_2$, the theoretical maximum accuracy any machine learning algorithm can achieve is bounded by the majority-class proportion (the Bayes error rate). This explains why the original Priority model hovered at ~55% accuracy.

### B. Category and Department Test-Set Leakage
While Priority had severe label conflicts, Category and Department were 100% deterministic. Because the 60 templates were repeated 20 times and split randomly into 80% train and 20% test without grouping, the exact same 60 sentences appeared in both train and test sets, artificially inflating Category and Department accuracy to 100%.

---

## 3. Action Plan for Phase 1 Data Curation

1. **Retain Raw Baseline**: Keep `ticket_priority_dataset_1200_rows.xlsx` in `ml/data/raw/`.
2. **Standardize Schema**:
   `ticket_id`, `ticket_text`, `priority`, `category`, `department`, `created_at`, `status`.
3. **Resolve Priority Conflicts via Explicit Policy**:
   - Outage / Core Failure / Security Incident $\rightarrow$ `High`.
   - Degradation / Workaround available $\rightarrow$ `Medium`.
   - General request / Information / Documentation $\rightarrow$ `Low`.
4. **Controlled Semantic Diversity**:
   Expand the 60 base templates into realistic, diverse technical descriptions (e.g. adding server names, error codes, specific symptoms, and urgency cues) so the model learns semantic features rather than rote memorization.

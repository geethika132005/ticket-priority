import os
import pandas as pd
import pytest

DATASET_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "dataset",
    "ticket_priority_dataset_1200_rows.xlsx",
)


def test_dataset_exists_and_row_count():
    assert os.path.exists(DATASET_PATH), f"Dataset not found at {DATASET_PATH}"
    df = pd.read_excel(DATASET_PATH)
    assert len(df) == 1200, f"Expected 1200 rows, found {len(df)}"


def test_dataset_no_missing_values():
    df = pd.read_excel(DATASET_PATH)
    text_col = "ticket_text" if "ticket_text" in df.columns else "Ticket Description"
    prio_col = "priority" if "priority" in df.columns else "Priority"
    cat_col = "category" if "category" in df.columns else "Category"

    assert df[text_col].isnull().sum() == 0, "Missing values in text column"
    assert df[prio_col].isnull().sum() == 0, "Missing values in priority column"
    assert df[cat_col].isnull().sum() == 0, "Missing values in category column"


def test_dataset_class_distributions():
    df = pd.read_excel(DATASET_PATH)
    prio_col = "priority" if "priority" in df.columns else "Priority"
    cat_col = "category" if "category" in df.columns else "Category"

    priorities = set(df[prio_col].unique())
    assert priorities == {"High", "Medium", "Low"}

    categories = set(df[cat_col].unique())
    assert len(categories) == 6

    # Verify no class is starved
    p_counts = df[prio_col].value_counts()
    for p in ["High", "Medium", "Low"]:
        assert p_counts[p] >= 300, f"Class {p} has fewer than 300 samples"


def test_dataset_no_conflicting_labels():
    df = pd.read_excel(DATASET_PATH)
    text_col = "ticket_text" if "ticket_text" in df.columns else "Ticket Description"
    prio_col = "priority" if "priority" in df.columns else "Priority"

    grouped = df.groupby(text_col)[prio_col].nunique()
    conflicts = grouped[grouped > 1]
    assert len(conflicts) == 0, f"Found {len(conflicts)} tickets with conflicting priority labels!"

import pytest
from datetime import datetime, timezone
import pandas as pd
import numpy as np

from backend.specs import get_default_support_ticket_spec
from backend.generation import (
    GenerationEngine,
    allocate_fixed_proportions,
    generate_identifiers,
    get_rng,
    sample_categorical,
    sample_truncated_normal,
    sample_uniform,
)
from backend.validation import validate_dataset

def test_fixed_proportions_exact_allocation():
    rng = get_rng(42)
    categories = ["delivery", "payment", "returns"]
    probabilities = [0.50, 0.30, 0.20]

    # For 100 rows: exactly 50, 30, 20
    draws_100 = allocate_fixed_proportions(categories, probabilities, 100, rng)
    assert len(draws_100) == 100
    counts_100 = pd.Series(draws_100).value_counts().to_dict()
    assert counts_100["delivery"] == 50
    assert counts_100["payment"] == 30
    assert counts_100["returns"] == 20

    # For uneven size (e.g. 10 rows): largest remainder allocation
    # 10 * 0.5 = 5.0 -> 5
    # 10 * 0.3 = 3.0 -> 3
    # 10 * 0.2 = 2.0 -> 2
    draws_10 = allocate_fixed_proportions(categories, probabilities, 10, rng)
    assert len(draws_10) == 10
    counts_10 = pd.Series(draws_10).value_counts().to_dict()
    assert counts_10["delivery"] == 5
    assert counts_10["payment"] == 3
    assert counts_10["returns"] == 2

    # Uneven fractional split: 7 rows with [0.5, 0.3, 0.2]
    # 7 * 0.5 = 3.5 (floor 3, rem 0.5)
    # 7 * 0.3 = 2.1 (floor 2, rem 0.1)
    # 7 * 0.2 = 1.4 (floor 1, rem 0.4)
    # Floored sum: 6. Remainder to distribute: 1.
    # Largest remainder is 0.5 (delivery) -> receives +1 = 4.
    draws_7 = allocate_fixed_proportions(categories, probabilities, 7, rng)
    assert len(draws_7) == 7
    counts_7 = pd.Series(draws_7).value_counts().to_dict()
    assert counts_7["delivery"] == 4
    assert counts_7["payment"] == 2
    assert counts_7["returns"] == 1

def test_categorical_repeatability_with_seed():
    rng1 = get_rng(12345)
    rng2 = get_rng(12345)
    cats = ["apple", "banana", "orange"]
    probs = [0.2, 0.5, 0.3]

    res1 = sample_categorical(cats, probs, 50, rng1)
    res2 = sample_categorical(cats, probs, 50, rng2)
    assert res1 == res2

def test_truncated_normal_bounds_and_precision():
    rng = get_rng(42)
    draws = sample_truncated_normal(
        mean=4500.0,
        std_dev=2000.0,
        lower=500.0,
        upper=25000.0,
        count=1000,
        precision=2,
        rng=rng,
    )
    assert len(draws) == 1000
    for val in draws:
        assert 500.0 <= val <= 25000.0
        # Precision check: decimal part has at most 2 digits
        assert round(val, 2) == val

def test_identifier_uniqueness():
    ids = generate_identifiers(prefix="SYN-TKT-", start_index=1, pad_width=5, count=500)
    assert len(ids) == 500
    assert len(set(ids)) == 500
    assert ids[0] == "SYN-TKT-00001"
    assert ids[-1] == "SYN-TKT-00500"

def test_generation_engine_default_support_ticket():
    spec = get_default_support_ticket_spec()
    engine = GenerationEngine(spec)
    df = engine.generate_skeletons(row_count=100, seed=42)

    assert len(df) == 100
    assert list(df.columns) == [f.name for f in spec.fields]

    # Run full dataset validation
    report = validate_dataset(df, spec)
    assert report.is_valid is True
    assert report.rule_violations_count == 0
    assert report.total_rows == 100
    assert report.accepted_rows == 100

    # Test derived datetime logic
    for _, row in df.iterrows():
        if row["status"] == "resolved":
            assert pd.notna(row["resolved_at"])
            assert row["resolved_at"] > row["created_at"]
        else:
            assert pd.isna(row["resolved_at"])

def test_generation_engine_seed_stability():
    spec = get_default_support_ticket_spec()
    engine1 = GenerationEngine(spec)
    engine2 = GenerationEngine(spec)

    df1 = engine1.generate_skeletons(row_count=50, seed=999)
    df2 = engine2.generate_skeletons(row_count=50, seed=999)

    pd.testing.assert_frame_equal(df1, df2)

def test_generation_engine_fixed_proportions_mode():
    spec = get_default_support_ticket_spec()
    spec.generation_mode = "fixed_proportions"
    spec.row_count = 100

    engine = GenerationEngine(spec)
    df = engine.generate_skeletons(row_count=100, seed=77)

    cat_counts = df["category"].value_counts().to_dict()
    assert cat_counts["delivery"] == 50
    assert cat_counts["payment"] == 30
    assert cat_counts["returns"] == 20

    status_counts = df["status"].value_counts().to_dict()
    assert status_counts["open"] == 30
    assert status_counts["pending"] == 30
    assert status_counts["resolved"] == 40

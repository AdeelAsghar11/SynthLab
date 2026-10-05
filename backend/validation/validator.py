from typing import Any
import pandas as pd
import numpy as np
from pydantic import BaseModel, Field

from backend.specs.models import DatasetSpec, FieldType

class ColumnSummary(BaseModel):
    name: str
    type: str
    null_count: int
    unique_count: int
    category_counts: dict[str, int] | None = None
    category_frequencies: dict[str, float] | None = None
    numeric_min: float | None = None
    numeric_max: float | None = None
    numeric_mean: float | None = None
    numeric_std: float | None = None

class RuleViolation(BaseModel):
    row_index: int
    field: str
    rule: str
    message: str

class DatasetValidationReport(BaseModel):
    is_valid: bool
    total_rows: int
    accepted_rows: int
    rule_violations_count: int
    violations: list[RuleViolation] = Field(default_factory=list)
    column_summaries: dict[str, ColumnSummary] = Field(default_factory=dict)

def validate_dataset(
    df: pd.DataFrame,
    spec: DatasetSpec,
    allow_pending_text: bool = True,
) -> DatasetValidationReport:
    """Validates generated dataset against specification schema, types, bounds, and rules."""
    violations: list[RuleViolation] = []
    col_summaries: dict[str, ColumnSummary] = {}
    total_rows = len(df)

    field_map = {f.name: f for f in spec.fields}

    # 1. Per-field checks and summaries
    for field in spec.fields:
        col_name = field.name
        gen = field.generator

        if col_name not in df.columns:
            violations.append(RuleViolation(
                row_index=-1,
                field=col_name,
                rule="MISSING_COLUMN",
                message=f"Expected column '{col_name}' missing from generated dataset.",
            ))
            continue

        series = df[col_name]
        null_count = int(series.isna().sum())
        unique_count = int(series.nunique(dropna=True))

        summary = ColumnSummary(
            name=col_name,
            type=field.type.value,
            null_count=null_count,
            unique_count=unique_count,
        )

        # Check nullability (skipping pending llm_text fields if allow_pending_text is True)
        if not field.nullable and null_count > 0:
            if allow_pending_text and gen.kind == "llm_text":
                pass
            else:
                for idx in series[series.isna()].index:
                    violations.append(RuleViolation(
                        row_index=int(idx),
                        field=col_name,
                        rule="NON_NULLABLE_VIOLATION",
                        message=f"Field '{col_name}' is non-nullable but contains null.",
                    ))

        # Check identifier uniqueness
        if field.type == FieldType.IDENTIFIER:
            if unique_count != (total_rows - null_count):
                violations.append(RuleViolation(
                    row_index=-1,
                    field=col_name,
                    rule="DUPLICATE_IDENTIFIERS",
                    message=f"Identifier field '{col_name}' contains duplicate values.",
                ))

        # Categorical checks & summaries
        if field.type == FieldType.CATEGORY:
            valid_cats = set()
            if gen.kind == "categorical":
                valid_cats = set(gen.categories)
            elif gen.kind == "conditional_categorical":
                for dist in gen.mapping.values():
                    valid_cats.update(dist.keys())

            counts: dict[str, int] = {}
            freqs: dict[str, float] = {}
            val_counts = series.value_counts(dropna=True)
            non_null_total = total_rows - null_count

            for cat, count in val_counts.items():
                cat_str = str(cat)
                counts[cat_str] = int(count)
                freqs[cat_str] = round(float(count / non_null_total), 4) if non_null_total > 0 else 0.0

                if valid_cats and cat_str not in valid_cats:
                    violations.append(RuleViolation(
                        row_index=-1,
                        field=col_name,
                        rule="INVALID_CATEGORY_VALUE",
                        message=f"Found invalid category value '{cat_str}' in field '{col_name}'.",
                    ))

            summary.category_counts = counts
            summary.category_frequencies = freqs

        # Numeric checks & summaries
        elif field.type in (FieldType.INTEGER, FieldType.DECIMAL):
            valid_series = series.dropna()
            if not valid_series.empty:
                summary.numeric_min = float(valid_series.min())
                summary.numeric_max = float(valid_series.max())
                summary.numeric_mean = round(float(valid_series.mean()), 2)
                summary.numeric_std = round(float(valid_series.std()), 2) if len(valid_series) > 1 else 0.0

            # Bounds verification
            if gen.kind == "uniform":
                out_of_bounds = valid_series[(valid_series < gen.min_value) | (valid_series > gen.max_value)]
                for idx in out_of_bounds.index:
                    violations.append(RuleViolation(
                        row_index=int(idx),
                        field=col_name,
                        rule="UNIFORM_BOUND_EXCEEDED",
                        message=f"Value {series[idx]} outside uniform range [{gen.min_value}, {gen.max_value}].",
                    ))
            elif gen.kind == "truncated_normal":
                out_of_bounds = valid_series[(valid_series < gen.lower_bound) | (valid_series > gen.upper_bound)]
                for idx in out_of_bounds.index:
                    violations.append(RuleViolation(
                        row_index=int(idx),
                        field=col_name,
                        rule="TRUNCATED_NORMAL_BOUND_EXCEEDED",
                        message=f"Value {series[idx]} outside bounds [{gen.lower_bound}, {gen.upper_bound}].",
                    ))

        # Derived datetime checks
        elif gen.kind == "derived_datetime":
            created_col = gen.created_field
            status_col = gen.status_field
            if created_col in df.columns and status_col in df.columns:
                for idx in range(total_rows):
                    c_val = df.at[idx, created_col]
                    r_val = df.at[idx, col_name]
                    s_val = str(df.at[idx, status_col]).lower()

                    if s_val == gen.resolved_status.lower():
                        if pd.isna(r_val):
                            violations.append(RuleViolation(
                                row_index=idx,
                                field=col_name,
                                rule="MISSING_RESOLVED_DATE",
                                message=f"Row {idx} status is '{s_val}' but '{col_name}' is null.",
                            ))
                        elif c_val is not None and not pd.isna(c_val) and r_val <= c_val:
                            violations.append(RuleViolation(
                                row_index=idx,
                                field=col_name,
                                rule="RESOLVED_BEFORE_CREATED",
                                message=f"Row {idx} resolved_at ({r_val}) must be after created_at ({c_val}).",
                            ))
                    else:
                        if not pd.isna(r_val):
                            violations.append(RuleViolation(
                                row_index=idx,
                                field=col_name,
                                rule="UNEXPECTED_RESOLVED_DATE",
                                message=f"Row {idx} status is '{s_val}' but resolved_at is not null.",
                            ))

        col_summaries[col_name] = summary

    # 2. Check declarative constraints
    for constraint in spec.constraints:
        f_name = constraint.field
        if f_name not in df.columns:
            continue

        if constraint.kind == "one_of" and constraint.values:
            allowed = set(constraint.values)
            invalid_rows = df[~df[f_name].isin(allowed) & df[f_name].notna()]
            for idx in invalid_rows.index:
                violations.append(RuleViolation(
                    row_index=int(idx),
                    field=f_name,
                    rule="CONSTRAINT_ONE_OF_VIOLATION",
                    message=f"Value '{df.at[idx, f_name]}' not in allowed set.",
                ))

        elif constraint.kind == "greater_than" and constraint.target_field in df.columns:
            t_name = constraint.target_field
            invalid_rows = df[(df[f_name] <= df[t_name]) & df[f_name].notna() & df[t_name].notna()]
            for idx in invalid_rows.index:
                violations.append(RuleViolation(
                    row_index=int(idx),
                    field=f_name,
                    rule="CONSTRAINT_GREATER_THAN_VIOLATION",
                    message=f"Field '{f_name}' ({df.at[idx, f_name]}) not greater than '{t_name}' ({df.at[idx, t_name]}).",
                ))

        elif constraint.kind == "date_after" and constraint.target_field in df.columns:
            t_name = constraint.target_field
            invalid_rows = df[(df[f_name] <= df[t_name]) & df[f_name].notna() & df[t_name].notna()]
            for idx in invalid_rows.index:
                violations.append(RuleViolation(
                    row_index=int(idx),
                    field=f_name,
                    rule="CONSTRAINT_DATE_AFTER_VIOLATION",
                    message=f"Date '{f_name}' not after '{t_name}'.",
                ))

        elif constraint.kind == "unique":
            dups = df[df.duplicated(subset=[f_name], keep=False) & df[f_name].notna()]
            for idx in dups.index:
                violations.append(RuleViolation(
                    row_index=int(idx),
                    field=f_name,
                    rule="CONSTRAINT_UNIQUE_VIOLATION",
                    message=f"Field '{f_name}' contains duplicate value '{df.at[idx, f_name]}'.",
                ))

    is_valid = len(violations) == 0
    accepted_rows = total_rows if is_valid else max(0, total_rows - len({v.row_index for v in violations if v.row_index >= 0}))

    return DatasetValidationReport(
        is_valid=is_valid,
        total_rows=total_rows,
        accepted_rows=accepted_rows,
        rule_violations_count=len(violations),
        violations=violations[:50],  # cap reporting at first 50 violations
        column_summaries=col_summaries,
    )

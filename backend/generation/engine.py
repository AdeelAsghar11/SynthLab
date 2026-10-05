from datetime import datetime, timedelta, timezone
from typing import Any
import pandas as pd
import numpy as np

from backend.specs.models import DatasetSpec, FieldType
from backend.specs.validator import get_topological_generation_order
from backend.generation.samplers import (
    allocate_fixed_proportions,
    generate_identifiers,
    get_rng,
    sample_boolean,
    sample_categorical,
    sample_datetimes,
    sample_truncated_normal,
    sample_uniform,
)

class GenerationEngine:
    """Deterministic structured dataset generator."""

    def __init__(self, spec: DatasetSpec):
        self.spec = spec
        self.order = get_topological_generation_order(spec)
        self.field_map = {f.name: f for f in spec.fields}

    def generate_skeletons(
        self,
        row_count: int | None = None,
        seed: int | None = None,
    ) -> pd.DataFrame:
        """Generates structured row facts deterministically."""
        n = row_count if row_count is not None else self.spec.row_count
        actual_seed = seed if seed is not None else self.spec.seed
        rng = get_rng(actual_seed)

        data: dict[str, list[Any]] = {}

        for field_name in self.order:
            field = self.field_map[field_name]
            gen = field.generator

            if gen.kind == "identifier":
                values = generate_identifiers(
                    prefix=gen.prefix,
                    start_index=gen.start_index,
                    pad_width=gen.pad_width,
                    count=n,
                )

            elif gen.kind == "categorical":
                if self.spec.generation_mode == "fixed_proportions":
                    values = allocate_fixed_proportions(
                        categories=gen.categories,
                        probabilities=gen.probabilities,
                        count=n,
                        rng=rng,
                    )
                else:
                    values = sample_categorical(
                        categories=gen.categories,
                        probabilities=gen.probabilities,
                        count=n,
                        rng=rng,
                    )

            elif gen.kind == "conditional_categorical":
                parent_values = data[gen.depends_on]
                values = []
                for p_val in parent_values:
                    dist = gen.mapping.get(str(p_val))
                    if not dist:
                        # Fallback to equal uniform if parent value is unexpected
                        categories = list(list(gen.mapping.values())[0].keys())
                        probs = None
                    else:
                        categories = list(dist.keys())
                        probs = list(dist.values())
                    draw = sample_categorical(categories, probs, 1, rng)[0]
                    values.append(draw)

            elif gen.kind == "uniform":
                as_int = field.type == FieldType.INTEGER
                values = sample_uniform(
                    min_value=gen.min_value,
                    max_value=gen.max_value,
                    count=n,
                    precision=gen.precision,
                    rng=rng,
                    as_integer=as_int,
                )

            elif gen.kind == "truncated_normal":
                as_int = field.type == FieldType.INTEGER
                values = sample_truncated_normal(
                    mean=gen.mean,
                    std_dev=gen.std_dev,
                    lower=gen.lower_bound,
                    upper=gen.upper_bound,
                    count=n,
                    precision=gen.precision,
                    rng=rng,
                    as_integer=as_int,
                )

            elif gen.kind == "boolean":
                values = sample_boolean(
                    probability_true=gen.probability_true,
                    count=n,
                    rng=rng,
                )

            elif gen.kind == "datetime":
                values = sample_datetimes(
                    start_date=gen.start_date,
                    end_date=gen.end_date,
                    count=n,
                    rng=rng,
                )

            elif gen.kind == "derived_datetime":
                created_times = data[gen.created_field]
                statuses = data[gen.status_field]
                values = []
                for c_time, status in zip(created_times, statuses):
                    if str(status).lower() == gen.resolved_status.lower() and c_time is not None:
                        # Add bounded duration
                        duration_sec = rng.uniform(gen.min_duration_seconds, gen.max_duration_seconds)
                        res_time = c_time + timedelta(seconds=float(duration_sec))
                        values.append(res_time)
                    else:
                        values.append(None)

            elif gen.kind == "llm_text":
                # Text fields are initialized with None or template placeholder
                values = [None] * n

            else:
                values = [None] * n

            # Apply nullability mask if requested (except derived datetime which computes nulls from status)
            if field.nullable and field.null_probability > 0 and gen.kind != "derived_datetime":
                null_mask = sample_boolean(field.null_probability, n, rng)
                values = [None if is_null else v for v, is_null in zip(values, null_mask)]

            data[field_name] = values

        # Construct DataFrame respecting original specification field order
        ordered_data = {f.name: data[f.name] for f in self.spec.fields}
        return pd.DataFrame(ordered_data)

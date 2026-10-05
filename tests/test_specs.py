import pytest
from pydantic import ValidationError
from datetime import datetime, timezone

from backend.specs import (
    CategoricalGenerator,
    ConditionalCategoricalGenerator,
    DatasetSpec,
    DateTimeGenerator,
    FieldSpec,
    FieldType,
    IdentifierGenerator,
    LLMTextGenerator,
    TruncatedNormalGenerator,
    UniformGenerator,
    get_default_support_ticket_spec,
    get_topological_generation_order,
    validate_spec_semantics,
)

def test_default_template_validates():
    spec = get_default_support_ticket_spec()
    assert spec.spec_version == 1
    assert spec.name == "ecommerce_support_tickets_v1"
    assert len(spec.fields) == 8

    # Verify semantic validation has zero errors
    diagnostics = validate_spec_semantics(spec)
    assert diagnostics == []

    # Verify deterministic topological order
    order = get_topological_generation_order(spec)
    assert len(order) == 8
    # category must precede priority
    assert order.index("category") < order.index("priority")
    # created_at and status must precede resolved_at
    assert order.index("created_at") < order.index("resolved_at")
    assert order.index("status") < order.index("resolved_at")
    # message depends on category, priority, status, order_value
    assert order.index("category") < order.index("message")
    assert order.index("priority") < order.index("message")
    assert order.index("status") < order.index("message")
    assert order.index("order_value") < order.index("message")

def test_unknown_key_rejection_on_envelope():
    spec_dict = {
        "spec_version": 1,
        "name": "test_spec",
        "row_count": 50,
        "seed": 100,
        "fields": [
            {
                "name": "id",
                "type": "identifier",
                "generator": {"kind": "identifier", "prefix": "ID-"},
            }
        ],
        "unknown_extra_envelope_key": "forbidden",
    }
    with pytest.raises(ValidationError) as exc_info:
        DatasetSpec.model_validate(spec_dict)
    assert "extra_forbidden" in str(exc_info.value)

def test_unknown_key_rejection_in_generator():
    field_dict = {
        "name": "cat",
        "type": "category",
        "generator": {
            "kind": "categorical",
            "categories": ["A", "B"],
            "probabilities": [0.5, 0.5],
            "unauthorized_generator_param": True,
        },
    }
    with pytest.raises(ValidationError) as exc_info:
        FieldSpec.model_validate(field_dict)
    assert "extra_forbidden" in str(exc_info.value)

def test_row_count_and_seed_bounds():
    base_fields = [
        FieldSpec(
            name="id",
            type=FieldType.IDENTIFIER,
            generator=IdentifierGenerator(),
        )
    ]

    # Row count <= 0 rejected
    with pytest.raises(ValidationError):
        DatasetSpec(spec_version=1, name="test", row_count=0, seed=1, fields=base_fields)

    # Row count > 10,000 rejected
    with pytest.raises(ValidationError):
        DatasetSpec(spec_version=1, name="test", row_count=10001, seed=1, fields=base_fields)

    # Negative seed rejected
    with pytest.raises(ValidationError):
        DatasetSpec(spec_version=1, name="test", row_count=10, seed=-1, fields=base_fields)

def test_duplicate_field_names_rejected():
    with pytest.raises(ValidationError) as exc_info:
        DatasetSpec(
            spec_version=1,
            name="test",
            row_count=10,
            seed=1,
            fields=[
                FieldSpec(name="dup", type=FieldType.IDENTIFIER, generator=IdentifierGenerator()),
                FieldSpec(name="dup", type=FieldType.IDENTIFIER, generator=IdentifierGenerator()),
            ],
        )
    assert "Duplicate field name" in str(exc_info.value)

def test_type_and_generator_compatibility():
    # Attempting to assign categorical generator to an integer field
    with pytest.raises(ValidationError) as exc_info:
        FieldSpec(
            name="bad_field",
            type=FieldType.INTEGER,
            generator=CategoricalGenerator(categories=["A", "B"], probabilities=[0.5, 0.5]),
        )
    assert "categorical generator must have type 'category'" in str(exc_info.value)

def test_invalid_probabilities_sum():
    with pytest.raises(ValidationError) as exc_info:
        CategoricalGenerator(
            categories=["A", "B"],
            probabilities=[0.4, 0.4],  # sums to 0.8 != 1.0
        )
    assert "must sum to 1.0" in str(exc_info.value)

def test_uniform_and_truncated_normal_bounds():
    # min >= max in uniform
    with pytest.raises(ValidationError):
        UniformGenerator(min_value=10.0, max_value=5.0)

    # lower >= upper in truncated normal
    with pytest.raises(ValidationError):
        TruncatedNormalGenerator(
            mean=50.0,
            std_dev=10.0,
            lower_bound=100.0,
            upper_bound=20.0,
        )

def test_missing_dependency_semantic_diagnostic():
    spec = DatasetSpec(
        spec_version=1,
        name="test_missing_dep",
        row_count=10,
        fields=[
            FieldSpec(
                name="priority",
                type=FieldType.CATEGORY,
                generator=ConditionalCategoricalGenerator(
                    depends_on="nonexistent_parent",
                    mapping={"A": {"high": 1.0}},
                ),
            )
        ],
    )
    diagnostics = validate_spec_semantics(spec)
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "MISSING_DEPENDENCY"
    assert "nonexistent_parent" in diagnostics[0].message

def test_circular_dependency_detection():
    # Field A depends on B, and Field B depends on A
    spec = DatasetSpec(
        spec_version=1,
        name="test_cycle",
        row_count=10,
        fields=[
            FieldSpec(
                name="field_a",
                type=FieldType.CATEGORY,
                generator=ConditionalCategoricalGenerator(
                    depends_on="field_b",
                    mapping={"val": {"a1": 1.0}},
                ),
            ),
            FieldSpec(
                name="field_b",
                type=FieldType.CATEGORY,
                generator=ConditionalCategoricalGenerator(
                    depends_on="field_a",
                    mapping={"a1": {"val": 1.0}},
                ),
            ),
        ],
    )
    diagnostics = validate_spec_semantics(spec)
    assert any(d.code == "CIRCULAR_DEPENDENCY" for d in diagnostics)

    with pytest.raises(Exception) as exc_info:
        get_topological_generation_order(spec)
    assert "failed semantic validation" in str(exc_info.value)

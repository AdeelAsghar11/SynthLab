from datetime import datetime, timezone
from backend.specs.models import (
    DatasetSpec,
    FieldSpec,
    FieldType,
    IdentifierGenerator,
    CategoricalGenerator,
    ConditionalCategoricalGenerator,
    TruncatedNormalGenerator,
    DateTimeGenerator,
    DerivedDateTimeGenerator,
    LLMTextGenerator,
    TextOptions,
)

def get_default_support_ticket_spec() -> DatasetSpec:
    """Returns the canonical MVP e-commerce support ticket specification."""
    return DatasetSpec(
        spec_version=1,
        name="ecommerce_support_tickets_v1",
        row_count=100,
        seed=42,
        generation_mode="random",
        fields=[
            FieldSpec(
                name="ticket_id",
                type=FieldType.IDENTIFIER,
                generator=IdentifierGenerator(
                    prefix="SYN-TKT-",
                    start_index=1001,
                    pad_width=5,
                ),
                description="Visibly artificial unique ticket identifier",
            ),
            FieldSpec(
                name="category",
                type=FieldType.CATEGORY,
                generator=CategoricalGenerator(
                    categories=["delivery", "payment", "returns"],
                    probabilities=[0.50, 0.30, 0.20],
                ),
                description="Primary support inquiry category",
            ),
            FieldSpec(
                name="priority",
                type=FieldType.CATEGORY,
                generator=ConditionalCategoricalGenerator(
                    depends_on="category",
                    mapping={
                        "delivery": {"low": 0.20, "medium": 0.50, "high": 0.30},
                        "payment": {"low": 0.10, "medium": 0.40, "high": 0.50},
                        "returns": {"low": 0.40, "medium": 0.40, "high": 0.20},
                    },
                ),
                description="Conditional priority conditioned on category",
            ),
            FieldSpec(
                name="order_value",
                type=FieldType.DECIMAL,
                generator=TruncatedNormalGenerator(
                    mean=4500.0,
                    std_dev=2000.0,
                    lower_bound=500.0,
                    upper_bound=25000.0,
                    precision=2,
                ),
                description="Order value in PKR",
            ),
            FieldSpec(
                name="created_at",
                type=FieldType.DATETIME,
                generator=DateTimeGenerator(
                    start_date=datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
                    end_date=datetime(2026, 6, 1, 0, 0, tzinfo=timezone.utc),
                    timezone="UTC",
                ),
                description="Ticket creation timestamp in UTC",
            ),
            FieldSpec(
                name="status",
                type=FieldType.CATEGORY,
                generator=CategoricalGenerator(
                    categories=["open", "pending", "resolved"],
                    probabilities=[0.30, 0.30, 0.40],
                ),
                description="Current ticket lifecycle status",
            ),
            FieldSpec(
                name="resolved_at",
                type=FieldType.DATETIME,
                nullable=True,
                null_probability=0.60,
                generator=DerivedDateTimeGenerator(
                    created_field="created_at",
                    status_field="status",
                    resolved_status="resolved",
                    min_duration_seconds=300,
                    max_duration_seconds=86400 * 5,
                ),
                description="Resolution timestamp conditioned on status=resolved",
            ),
            FieldSpec(
                name="message",
                type=FieldType.TEXT,
                generator=LLMTextGenerator(
                    depends_on=["category", "priority", "status", "order_value"],
                    template_id="support_ticket_v1",
                    max_tokens=250,
                    temperature=0.7,
                ),
                description="Synthetic natural language ticket message",
            ),
        ],
        constraints=[],
        text_options=TextOptions(
            template_version="v1",
            max_length=500,
            timeout_seconds=30.0,
        ),
    )

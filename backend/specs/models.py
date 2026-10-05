from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Literal, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

class FieldType(str, Enum):
    INTEGER = "integer"
    DECIMAL = "decimal"
    CATEGORY = "category"
    DATETIME = "datetime"
    BOOLEAN = "boolean"
    IDENTIFIER = "identifier"
    TEXT = "text"

class BaseSpecModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True,
    )

# --- Generator Variants (Discriminated by `kind`) ---

class IdentifierGenerator(BaseSpecModel):
    kind: Literal["identifier"] = "identifier"
    prefix: str = Field(default="SYN-TKT-", max_length=32)
    start_index: int = Field(default=1, ge=0)
    pad_width: int = Field(default=4, ge=1, le=12)

class CategoricalGenerator(BaseSpecModel):
    kind: Literal["categorical"] = "categorical"
    categories: list[str] = Field(min_length=1)
    probabilities: list[float] | None = None

    @model_validator(mode="after")
    def validate_probabilities(self) -> "CategoricalGenerator":
        if self.probabilities is not None:
            if len(self.categories) != len(self.probabilities):
                raise ValueError("Length of probabilities must match length of categories")
            for p in self.probabilities:
                if p < 0 or not (0.0 <= p <= 1.0):
                    raise ValueError("Each probability must be finite and between 0.0 and 1.0")
            prob_sum = sum(self.probabilities)
            if abs(prob_sum - 1.0) > 1e-4:
                raise ValueError(f"Probabilities must sum to 1.0 (got {prob_sum})")
        return self

class UniformGenerator(BaseSpecModel):
    kind: Literal["uniform"] = "uniform"
    min_value: float
    max_value: float
    precision: int | None = Field(default=None, ge=0, le=6)

    @model_validator(mode="after")
    def validate_range(self) -> "UniformGenerator":
        if self.min_value >= self.max_value:
            raise ValueError(f"min_value ({self.min_value}) must be strictly less than max_value ({self.max_value})")
        return self

class TruncatedNormalGenerator(BaseSpecModel):
    kind: Literal["truncated_normal"] = "truncated_normal"
    mean: float
    std_dev: float = Field(gt=0)
    lower_bound: float
    upper_bound: float
    precision: int | None = Field(default=2, ge=0, le=6)

    @model_validator(mode="after")
    def validate_bounds(self) -> "TruncatedNormalGenerator":
        if self.lower_bound >= self.upper_bound:
            raise ValueError(f"lower_bound ({self.lower_bound}) must be less than upper_bound ({self.upper_bound})")
        if not (self.lower_bound <= self.mean <= self.upper_bound):
            raise ValueError("mean should be situated within lower and upper bounds")
        return self

class BooleanGenerator(BaseSpecModel):
    kind: Literal["boolean"] = "boolean"
    probability_true: float = Field(default=0.5, ge=0.0, le=1.0)

class DateTimeGenerator(BaseSpecModel):
    kind: Literal["datetime"] = "datetime"
    start_date: datetime
    end_date: datetime
    timezone: Literal["UTC"] = "UTC"

    @model_validator(mode="after")
    def validate_interval(self) -> "DateTimeGenerator":
        if self.start_date >= self.end_date:
            raise ValueError("start_date must be strictly earlier than end_date")
        return self

class ConditionalCategoricalGenerator(BaseSpecModel):
    kind: Literal["conditional_categorical"] = "conditional_categorical"
    depends_on: str = Field(min_length=1)
    mapping: dict[str, dict[str, float]] = Field(min_length=1)

    @field_validator("mapping")
    @classmethod
    def validate_distribution_mapping(cls, v: dict[str, dict[str, float]]) -> dict[str, dict[str, float]]:
        for parent_val, dist in v.items():
            if not dist:
                raise ValueError(f"Category '{parent_val}' has empty probability distribution")
            total = sum(dist.values())
            if abs(total - 1.0) > 1e-4:
                raise ValueError(f"Distribution for parent category '{parent_val}' must sum to 1.0 (got {total})")
            for cat, prob in dist.items():
                if prob < 0:
                    raise ValueError(f"Probability for '{cat}' must be non-negative")
        return v

class DerivedDateTimeGenerator(BaseSpecModel):
    kind: Literal["derived_datetime"] = "derived_datetime"
    created_field: str = Field(min_length=1)
    status_field: str = Field(min_length=1)
    resolved_status: str = Field(default="resolved")
    min_duration_seconds: int = Field(default=60, ge=0)
    max_duration_seconds: int = Field(default=86400 * 7, gt=0)

    @model_validator(mode="after")
    def validate_duration_range(self) -> "DerivedDateTimeGenerator":
        if self.min_duration_seconds > self.max_duration_seconds:
            raise ValueError("min_duration_seconds cannot exceed max_duration_seconds")
        return self

class LLMTextGenerator(BaseSpecModel):
    kind: Literal["llm_text"] = "llm_text"
    depends_on: list[str] = Field(min_length=1)
    template_id: str = Field(default="support_ticket_v1", max_length=64)
    max_tokens: int = Field(default=250, ge=10, le=1000)
    temperature: float = Field(default=0.7, ge=0.0, le=1.5)

# Discriminated Union of all supported Generator Configs
GeneratorConfig = Annotated[
    Union[
        IdentifierGenerator,
        CategoricalGenerator,
        UniformGenerator,
        TruncatedNormalGenerator,
        BooleanGenerator,
        DateTimeGenerator,
        ConditionalCategoricalGenerator,
        DerivedDateTimeGenerator,
        LLMTextGenerator,
    ],
    Field(discriminator="kind"),
]

# --- Field Specification ---

class FieldSpec(BaseSpecModel):
    name: str = Field(pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$", max_length=64)
    type: FieldType
    nullable: bool = False
    null_probability: float = Field(default=0.0, ge=0.0, le=1.0)
    description: str | None = Field(default=None, max_length=256)
    generator: GeneratorConfig

    @model_validator(mode="after")
    def validate_type_generator_compatibility(self) -> "FieldSpec":
        gen_kind = self.generator.kind
        f_type = self.type

        # Verify type-generator coherence
        if gen_kind == "identifier" and f_type != FieldType.IDENTIFIER:
            raise ValueError(f"Field '{self.name}' with identifier generator must have type 'identifier'")
        elif gen_kind == "categorical" and f_type != FieldType.CATEGORY:
            raise ValueError(f"Field '{self.name}' with categorical generator must have type 'category'")
        elif gen_kind == "conditional_categorical" and f_type != FieldType.CATEGORY:
            raise ValueError(f"Field '{self.name}' with conditional_categorical generator must have type 'category'")
        elif gen_kind == "boolean" and f_type != FieldType.BOOLEAN:
            raise ValueError(f"Field '{self.name}' with boolean generator must have type 'boolean'")
        elif gen_kind == "datetime" and f_type != FieldType.DATETIME:
            raise ValueError(f"Field '{self.name}' with datetime generator must have type 'datetime'")
        elif gen_kind == "derived_datetime" and f_type != FieldType.DATETIME:
            raise ValueError(f"Field '{self.name}' with derived_datetime generator must have type 'datetime'")
        elif gen_kind == "llm_text" and f_type != FieldType.TEXT:
            raise ValueError(f"Field '{self.name}' with llm_text generator must have type 'text'")
        elif gen_kind == "uniform" and f_type not in (FieldType.INTEGER, FieldType.DECIMAL):
            raise ValueError(f"Field '{self.name}' with uniform generator must have type 'integer' or 'decimal'")
        elif gen_kind == "truncated_normal" and f_type not in (FieldType.INTEGER, FieldType.DECIMAL):
            raise ValueError(f"Field '{self.name}' with truncated_normal generator must have type 'integer' or 'decimal'")

        if not self.nullable and self.null_probability > 0.0:
            raise ValueError(f"Field '{self.name}' is non-nullable but has null_probability > 0")
        return self

# --- Allow-Listed Declarative Constraints ---

class ConstraintSpec(BaseSpecModel):
    kind: Literal["one_of", "greater_than", "date_after", "unique", "nullable_when"]
    field: str = Field(min_length=1)
    target_field: str | None = None
    values: list[Any] | None = None
    condition_field: str | None = None
    condition_value: Any | None = None

    @model_validator(mode="after")
    def validate_constraint_parameters(self) -> "ConstraintSpec":
        if self.kind == "one_of" and not self.values:
            raise ValueError("Constraint 'one_of' requires a non-empty 'values' list")
        if self.kind in ("greater_than", "date_after") and not self.target_field:
            raise ValueError(f"Constraint '{self.kind}' requires 'target_field'")
        if self.kind == "nullable_when" and (not self.condition_field or self.condition_value is None):
            raise ValueError("Constraint 'nullable_when' requires 'condition_field' and 'condition_value'")
        return self

# --- Text Generation Options ---

class TextOptions(BaseSpecModel):
    template_version: str = Field(default="v1", max_length=32)
    max_length: int = Field(default=500, ge=50, le=2000)
    timeout_seconds: float = Field(default=30.0, ge=5.0, le=120.0)

# --- Top-Level Dataset Specification Envelope ---

class DatasetSpec(BaseSpecModel):
    spec_version: Literal[1] = 1
    name: str = Field(min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9_\- ]+$")
    row_count: int = Field(gt=0, le=10000)
    seed: int = Field(default=42, ge=0, le=4294967295)  # 2^32 - 1
    generation_mode: Literal["random", "fixed_proportions"] = "random"
    fields: list[FieldSpec] = Field(min_length=1)
    constraints: list[ConstraintSpec] = Field(default_factory=list)
    text_options: TextOptions = Field(default_factory=TextOptions)

    @field_validator("fields")
    @classmethod
    def validate_unique_field_names(cls, v: list[FieldSpec]) -> list[FieldSpec]:
        seen = set()
        for f in v:
            if f.name in seen:
                raise ValueError(f"Duplicate field name detected: '{f.name}'")
            seen.add(f.name)
        return v

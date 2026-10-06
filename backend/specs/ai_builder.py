import json
import re
from contextlib import nullcontext
from datetime import datetime, timezone
from typing import Any, Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from backend.specs.models import (
    BooleanGenerator,
    CategoricalGenerator,
    DatasetSpec,
    DateTimeGenerator,
    FieldSpec,
    FieldType,
    IdentifierGenerator,
    LLMTextGenerator,
    TextOptions,
    UniformGenerator,
)
from backend.specs.validator import validate_spec_semantics


class AISchemaBuilderError(Exception):
    """Safe operational error raised by the local AI schema builder."""

    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


class AIFieldDraft(BaseModel):
    """Small non-executable field intent returned by the local model."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=64)
    type: Literal["identifier", "category", "integer", "decimal", "boolean", "datetime", "text"]
    description: str | None = Field(default=None, max_length=256)
    categories: list[str] | None = Field(default=None, min_length=1, max_length=50)
    min_value: float | None = None
    max_value: float | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    probability_true: float | None = Field(default=None, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_type_options(self) -> "AIFieldDraft":
        if self.type == "category" and not self.categories:
            raise ValueError("category fields require at least one category")
        if self.min_value is not None and self.max_value is not None and self.min_value >= self.max_value:
            raise ValueError("min_value must be less than max_value")
        if self.start_date is not None and self.end_date is not None and self.start_date >= self.end_date:
            raise ValueError("start_date must be earlier than end_date")
        return self


class AISchemaDraft(BaseModel):
    """Bounded field-intent envelope compiled into the strict DatasetSpec by Python."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)
    row_count: int = Field(default=100, gt=0, le=1000)
    fields: list[AIFieldDraft] = Field(min_length=1, max_length=50)

    @field_validator("fields")
    @classmethod
    def validate_unique_names(cls, fields: list[AIFieldDraft]) -> list[AIFieldDraft]:
        names = [field.name.casefold() for field in fields]
        if len(names) != len(set(names)):
            raise ValueError("field names must be unique")
        return fields


_TYPE_ALIASES = {
    "id": "identifier",
    "string": "text",
    "categorical": "category",
    "float": "decimal",
    "number": "decimal",
    "date": "datetime",
    "timestamp": "datetime",
}

_GENERATOR_TYPES = {
    "identifier": "identifier",
    "categorical": "category",
    "conditional_categorical": "category",
    "uniform": "decimal",
    "truncated_normal": "decimal",
    "boolean": "boolean",
    "datetime": "datetime",
    "derived_datetime": "datetime",
    "llm_text": "text",
}


def _slug(value: str, fallback: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_]+", "_", value.strip()).strip("_")
    if not normalized:
        normalized = fallback
    if normalized[0].isdigit():
        normalized = f"field_{normalized}"
    return normalized[:64]


def _base_prompt(user_prompt: str) -> str:
    return f"""Describe a synthetic dataset as a small JSON field-intent draft.

Requested use case:
{user_prompt}

Return exactly this shape:
{{
  "name": "snake_case_dataset_name",
  "row_count": 100,
  "fields": [
    {{"name": "record_id", "type": "identifier", "description": "Synthetic record identifier"}},
    {{"name": "category", "type": "category", "categories": ["option_a", "option_b"]}},
    {{"name": "quantity", "type": "integer", "min_value": 0, "max_value": 100}},
    {{"name": "price", "type": "decimal", "min_value": 0, "max_value": 1000}},
    {{"name": "active", "type": "boolean", "probability_true": 0.8}},
    {{"name": "created_at", "type": "datetime", "start_date": "2026-01-01T00:00:00Z", "end_date": "2026-12-31T23:59:59Z"}}
  ]
}}

Allowed field types: identifier, category, integer, decimal, boolean, datetime, text.
Category fields require categories. Numeric bounds and datetime bounds are optional.
Set row_count to the number explicitly requested by the user; otherwise use 100.
Do not add generator objects, constraints, records, values, or wrapper objects.
Return JSON only, without Markdown."""


def _repair_prompt(user_prompt: str, issues: list[str]) -> str:
    issue_text = "\n".join(f"- {issue}" for issue in issues[:8])
    return f"""Your previous field-intent draft was rejected.

Original requested use case:
{user_prompt}

Correct these issues:
{issue_text}

Return a complete replacement object with only name, row_count, and fields.
Each field may use only name, type, description, categories, min_value, max_value, start_date, end_date, and probability_true.
Return JSON only."""


def _validation_issues(exc: ValidationError) -> list[str]:
    issues: list[str] = []
    for error in exc.errors(include_url=False, include_input=False):
        path = ".".join(str(part) for part in error.get("loc", ())) or "draft"
        issues.append(f"{path}: {error.get('msg', 'invalid value')}")
    return issues or ["draft: invalid model output"]


def _normalize_draft_payload(parsed: Any) -> Any:
    if not isinstance(parsed, dict):
        return parsed

    root = parsed.get("dataset", parsed)
    if not isinstance(root, dict):
        return root
    normalized = dict(root)
    if "row_count" not in normalized and "records" in normalized:
        normalized["row_count"] = normalized.get("records")

    normalized_fields: list[Any] = []
    for raw_field in normalized.get("fields", []):
        if not isinstance(raw_field, dict):
            normalized_fields.append(raw_field)
            continue
        field = dict(raw_field)
        generator = field.pop("generator", None)
        if isinstance(generator, dict):
            generator_kind = str(generator.get("kind", "")).casefold()
            for key in (
                "categories",
                "min_value",
                "max_value",
                "lower_bound",
                "upper_bound",
                "start_date",
                "end_date",
                "probability_true",
            ):
                if key not in field and key in generator:
                    field[key] = generator[key]
        else:
            generator_kind = str(generator or "").casefold()

        raw_type = str(field.get("type", "")).casefold()
        field["type"] = _TYPE_ALIASES.get(raw_type, raw_type or _GENERATOR_TYPES.get(generator_kind, ""))
        if "min_value" not in field and "lower_bound" in field:
            field["min_value"] = field.get("lower_bound")
        if "max_value" not in field and "upper_bound" in field:
            field["max_value"] = field.get("upper_bound")
        field.pop("lower_bound", None)
        field.pop("upper_bound", None)
        normalized_fields.append(field)

    normalized["fields"] = normalized_fields
    return normalized


def _parse_draft(raw_response: str) -> tuple[AISchemaDraft | None, list[str]]:
    cleaned = raw_response.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned.removeprefix("```json").split("```", 1)[0].strip()
    elif cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```").split("```", 1)[0].strip()

    try:
        parsed: Any = json.loads(cleaned)
    except json.JSONDecodeError:
        return None, ["draft: response was not valid JSON"]

    try:
        return AISchemaDraft.model_validate(_normalize_draft_payload(parsed)), []
    except ValidationError as exc:
        return None, _validation_issues(exc)


def _equal_probabilities(count: int) -> list[float]:
    if count == 1:
        return [1.0]
    probability = 1.0 / count
    probabilities = [probability] * (count - 1)
    probabilities.append(1.0 - sum(probabilities))
    return probabilities


def compile_draft_to_spec(draft: AISchemaDraft) -> DatasetSpec:
    """Compile model-authored field intent into an allow-listed strict DatasetSpec."""
    draft_fields = list(draft.fields)
    if not any(field.type != "text" for field in draft_fields):
        draft_fields.insert(0, AIFieldDraft(name="record_id", type="identifier"))

    names: list[str] = []
    seen: set[str] = set()
    for index, field in enumerate(draft_fields):
        name = _slug(field.name, f"field_{index + 1}")
        base_name = name
        suffix = 2
        while name.casefold() in seen:
            name = f"{base_name[:58]}_{suffix}"
            suffix += 1
        seen.add(name.casefold())
        names.append(name)

    structured_names = [name for name, field in zip(names, draft_fields) if field.type != "text"]
    fields: list[FieldSpec] = []
    default_start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    default_end = datetime(2026, 12, 31, 23, 59, 59, tzinfo=timezone.utc)

    for name, draft_field in zip(names, draft_fields):
        description = draft_field.description
        if draft_field.type == "identifier":
            prefix_label = name.upper().replace("_", "-")[:20]
            generator = IdentifierGenerator(prefix=f"SYN-{prefix_label}-", start_index=1, pad_width=6)
            field_type = FieldType.IDENTIFIER
        elif draft_field.type == "category":
            assert draft_field.categories is not None
            categories = list(dict.fromkeys(category.strip() for category in draft_field.categories if category.strip()))
            if not categories:
                raise AISchemaBuilderError(422, "SCHEMA_MODEL_INVALID_OUTPUT", "The local model returned an empty category list.")
            generator = CategoricalGenerator(
                categories=categories,
                probabilities=_equal_probabilities(len(categories)),
            )
            field_type = FieldType.CATEGORY
        elif draft_field.type in ("integer", "decimal"):
            minimum = draft_field.min_value if draft_field.min_value is not None else 0.0
            maximum = draft_field.max_value if draft_field.max_value is not None else (100.0 if draft_field.type == "integer" else 1000.0)
            generator = UniformGenerator(
                min_value=minimum,
                max_value=maximum,
                precision=None if draft_field.type == "integer" else 2,
            )
            field_type = FieldType.INTEGER if draft_field.type == "integer" else FieldType.DECIMAL
        elif draft_field.type == "boolean":
            probability_true = draft_field.probability_true if draft_field.probability_true is not None else 0.5
            generator = BooleanGenerator(probability_true=probability_true)
            field_type = FieldType.BOOLEAN
        elif draft_field.type == "datetime":
            generator = DateTimeGenerator(
                start_date=draft_field.start_date or default_start,
                end_date=draft_field.end_date or default_end,
                timezone="UTC",
            )
            field_type = FieldType.DATETIME
        else:
            generator = LLMTextGenerator(
                depends_on=structured_names[:6],
                template_id="generic_text_v1",
                max_tokens=150,
                temperature=0.7,
            )
            field_type = FieldType.TEXT

        fields.append(
            FieldSpec(
                name=name,
                type=field_type,
                description=description,
                generator=generator,
            )
        )

    spec = DatasetSpec(
        spec_version=1,
        name=_slug(draft.name, "synthetic_dataset"),
        row_count=draft.row_count,
        seed=42,
        generation_mode="random",
        fields=fields,
        constraints=[],
        text_options=TextOptions(),
    )
    diagnostics = validate_spec_semantics(spec)
    if diagnostics:
        raise AISchemaBuilderError(
            422,
            "SCHEMA_MODEL_INVALID_OUTPUT",
            "The generated schema contained unsupported field dependencies.",
        )
    return spec


def generate_dataset_spec(
    user_prompt: str,
    *,
    base_url: str,
    model: str,
    timeout_seconds: float,
    max_attempts: int = 2,
    client: httpx.Client | None = None,
) -> DatasetSpec:
    """Generate a small field-intent draft and compile it into a strict DatasetSpec."""
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    schema = AISchemaDraft.model_json_schema(mode="validation")
    request_context = (
        nullcontext(client)
        if client is not None
        else httpx.Client(timeout=httpx.Timeout(timeout_seconds, connect=5.0))
    )
    prompt = _base_prompt(user_prompt)
    last_issues = ["draft: local model returned an invalid response"]

    try:
        with request_context as active_client:
            assert active_client is not None
            for attempt in range(max_attempts):
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "format": schema,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 1200,
                    },
                }
                response = active_client.post(f"{base_url.rstrip('/')}/api/generate", json=payload)
                response.raise_for_status()
                response_data = response.json()
                if not isinstance(response_data, dict):
                    last_issues = ["draft: local model returned an unreadable response envelope"]
                    if attempt + 1 < max_attempts:
                        prompt = _repair_prompt(user_prompt, last_issues)
                    continue
                raw_response = response_data.get("response")
                if not isinstance(raw_response, str) or not raw_response.strip():
                    last_issues = ["draft: local model returned an empty response"]
                else:
                    draft, last_issues = _parse_draft(raw_response)
                    if draft is not None:
                        return compile_draft_to_spec(draft)

                if attempt + 1 < max_attempts:
                    prompt = _repair_prompt(user_prompt, last_issues)
    except httpx.TimeoutException as exc:
        raise AISchemaBuilderError(
            status_code=504,
            code="SCHEMA_MODEL_TIMEOUT",
            message="The local model took too long to create a schema. Try a simpler description or a smaller local model.",
        ) from exc
    except AISchemaBuilderError:
        raise
    except (httpx.HTTPError, ValueError, TypeError, json.JSONDecodeError) as exc:
        raise AISchemaBuilderError(
            status_code=503,
            code="SCHEMA_MODEL_UNAVAILABLE",
            message="The local schema model is unavailable or returned an unreadable response.",
        ) from exc

    raise AISchemaBuilderError(
        status_code=422,
        code="SCHEMA_MODEL_INVALID_OUTPUT",
        message="The local model could not produce a compatible schema after two attempts. Try a simpler description.",
    )

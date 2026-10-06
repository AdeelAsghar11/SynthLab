from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from backend.config import settings
from backend.policies.schema_policy import (
    OUTPUT_REJECTION_MESSAGE,
    PROMPT_REJECTION_MESSAGE,
    SPEC_REJECTION_MESSAGE,
    screen_dataset_spec,
    screen_schema_prompt,
)
from backend.specs.ai_builder import AISchemaBuilderError, generate_dataset_spec
from backend.specs.models import DatasetSpec
from backend.specs.templates import get_default_support_ticket_spec
from backend.specs.validator import validate_spec_semantics, get_topological_generation_order

router = APIRouter(prefix="/api", tags=["specifications"])

class DiagnosticItem(BaseModel):
    code: str
    path: str
    message: str

class SpecValidationResponse(BaseModel):
    valid: bool
    diagnostics: list[DiagnosticItem] = Field(default_factory=list)
    generation_order: list[str] = Field(default_factory=list)

class TemplateSummary(BaseModel):
    id: str
    name: str
    description: str
    field_count: int
    default_row_count: int

class GenerateSpecRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=2000)

@router.get("/templates", response_model=list[TemplateSummary])
def list_templates() -> list[TemplateSummary]:
    """Lists available approved dataset templates."""
    default_ticket = get_default_support_ticket_spec()
    return [
        TemplateSummary(
            id="ecommerce_support_tickets_v1",
            name="E-Commerce Support Tickets (Fictional)",
            description="Operational customer support tickets with category, conditional priority, PKR order values, lifecycle dates, and LLM text.",
            field_count=len(default_ticket.fields),
            default_row_count=default_ticket.row_count,
        )
    ]

@router.get("/templates/{template_id}", response_model=DatasetSpec)
def get_template(template_id: str) -> DatasetSpec:
    """Retrieves full specification for an approved template."""
    if template_id in ("ecommerce_support_tickets_v1", "default"):
        return get_default_support_ticket_spec()
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Template '{template_id}' not found.",
    )

@router.post("/specs/validate", response_model=SpecValidationResponse)
def validate_specification(spec: DatasetSpec) -> SpecValidationResponse:
    """Validates specification syntax, field dependencies, and constraint contracts."""
    policy_result = screen_dataset_spec(spec)
    if not policy_result.is_safe:
        return SpecValidationResponse(
            valid=False,
            diagnostics=[
                DiagnosticItem(
                    code="PROHIBITED_SCHEMA_FIELD",
                    path=violation.path,
                    message=SPEC_REJECTION_MESSAGE,
                )
                for violation in policy_result.violations
            ],
            generation_order=[],
        )

    diagnostics = validate_spec_semantics(spec)
    if diagnostics:
        return SpecValidationResponse(
            valid=False,
            diagnostics=[
                DiagnosticItem(code=d.code, path=d.path, message=d.message)
                for d in diagnostics
            ],
            generation_order=[],
        )

    order = get_topological_generation_order(spec)
    return SpecValidationResponse(
        valid=True,
        diagnostics=[],
        generation_order=order,
    )

@router.post("/specs/generate", response_model=DatasetSpec)
def generate_specification_from_prompt(req: GenerateSpecRequest) -> DatasetSpec:
    """Uses the configured local Ollama model to create a validated DatasetSpec."""
    prompt_policy = screen_schema_prompt(req.prompt)
    if not prompt_policy.is_safe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "SCHEMA_PROMPT_REJECTED", "message": PROMPT_REJECTION_MESSAGE},
        )

    try:
        spec = generate_dataset_spec(
            req.prompt,
            base_url=settings.ollama_base_url,
            model=settings.default_model,
            timeout_seconds=settings.schema_generation_timeout_seconds,
        )
    except AISchemaBuilderError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"code": exc.code, "message": exc.message},
        ) from exc

    output_policy = screen_dataset_spec(spec)
    if not output_policy.is_safe:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"code": "SCHEMA_OUTPUT_REJECTED", "message": OUTPUT_REJECTION_MESSAGE},
        )
    return spec

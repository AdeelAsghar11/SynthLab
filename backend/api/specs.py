from typing import Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
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

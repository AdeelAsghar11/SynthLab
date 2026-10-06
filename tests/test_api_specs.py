import json
import pytest
from fastapi.testclient import TestClient

import backend.api.specs as specs_api
from backend.main import app
from backend.specs import get_default_support_ticket_spec
from backend.specs.ai_builder import AISchemaBuilderError, generate_dataset_spec

client = TestClient(app)

def test_list_templates():
    response = client.get("/api/templates")
    assert response.status_code == 200
    templates = response.json()
    assert len(templates) >= 1
    assert templates[0]["id"] == "ecommerce_support_tickets_v1"
    assert templates[0]["field_count"] == 8

def test_get_template_by_id():
    response = client.get("/api/templates/ecommerce_support_tickets_v1")
    assert response.status_code == 200
    spec = response.json()
    assert spec["spec_version"] == 1
    assert spec["name"] == "ecommerce_support_tickets_v1"
    assert len(spec["fields"]) == 8

    # 404 for unknown template
    resp_404 = client.get("/api/templates/nonexistent_template")
    assert resp_404.status_code == 404

def test_validate_spec_endpoint_valid():
    default_spec = get_default_support_ticket_spec()
    response = client.post("/api/specs/validate", json=default_spec.model_dump(mode="json"))
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["diagnostics"] == []
    assert len(data["generation_order"]) == 8
    assert data["generation_order"].index("category") < data["generation_order"].index("priority")

def test_validate_spec_endpoint_semantic_error():
    # Specification with broken dependency reference
    broken_spec = {
        "spec_version": 1,
        "name": "broken_spec",
        "row_count": 25,
        "seed": 42,
        "fields": [
            {
                "name": "priority",
                "type": "category",
                "generator": {
                    "kind": "conditional_categorical",
                    "depends_on": "ghost_category",
                    "mapping": {"delivery": {"high": 1.0}},
                },
            }
        ],
    }
    response = client.post("/api/specs/validate", json=broken_spec)
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert len(data["diagnostics"]) > 0
    assert data["diagnostics"][0]["code"] == "MISSING_DEPENDENCY"

def test_validate_spec_endpoint_extra_key_422():
    # Specification with unknown extra key
    invalid_spec = {
        "spec_version": 1,
        "name": "invalid_spec",
        "row_count": 25,
        "seed": 42,
        "fields": [],
        "injected_extra_key": "malicious",
    }
    response = client.post("/api/specs/validate", json=invalid_spec)
    assert response.status_code == 422


class StubOllamaResponse:
    def __init__(self, response_payload: dict):
        self.response_payload = response_payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {"response": json.dumps(self.response_payload)}


class SequenceOllamaClient:
    def __init__(self, responses: list[dict]):
        self.responses = responses
        self.calls: list[dict] = []

    def post(self, url: str, json: dict) -> StubOllamaResponse:
        self.calls.append({"url": url, "json": json})
        return StubOllamaResponse(self.responses[len(self.calls) - 1])


def test_ai_schema_builder_repairs_incompatible_model_output_once():
    invalid_draft = {
        "name": "fictional_inventory",
        "row_count": 20,
        "fields": [
            {"name": "item_id", "type": "identifier"},
            {"name": "category", "type": "category"},
        ],
    }
    valid_draft = {
        "name": "fictional_inventory",
        "row_count": 20,
        "fields": [
            {"name": "item_id", "type": "identifier"},
            {"name": "category", "type": "category", "categories": ["stock", "backorder"]},
            {"name": "quantity", "type": "integer", "min_value": 0, "max_value": 100},
        ],
    }
    ollama = SequenceOllamaClient([invalid_draft, valid_draft])

    result = generate_dataset_spec(
        "Create fictional ecommerce support tickets",
        base_url="http://ollama.test",
        model="test-model",
        timeout_seconds=5,
        client=ollama,
    )

    assert result.name == "fictional_inventory"
    assert result.row_count == 20
    assert result.fields[1].type.value == "category"
    assert result.fields[1].generator.kind == "categorical"
    assert len(ollama.calls) == 2
    assert ollama.calls[0]["url"] == "http://ollama.test/api/generate"
    assert isinstance(ollama.calls[0]["json"]["format"], dict)
    assert "previous field-intent draft was rejected" in ollama.calls[1]["json"]["prompt"]


def test_ai_schema_endpoint_returns_sanitized_operational_error(monkeypatch):
    def fail_generation(*args, **kwargs):
        raise AISchemaBuilderError(
            status_code=504,
            code="SCHEMA_MODEL_TIMEOUT",
            message="The local model took too long to create a schema.",
        )

    monkeypatch.setattr(specs_api, "generate_dataset_spec", fail_generation)

    response = client.post("/api/specs/generate", json={"prompt": "Create fictional inventory records"})

    assert response.status_code == 504
    assert response.json() == {
        "detail": {
            "code": "SCHEMA_MODEL_TIMEOUT",
            "message": "The local model took too long to create a schema.",
        }
    }
    assert "pydantic" not in response.text.lower()

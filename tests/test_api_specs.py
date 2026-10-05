import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.specs import get_default_support_ticket_spec

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

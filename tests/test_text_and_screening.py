import pytest
import pandas as pd
from typing import Any

from backend.generation import (
    AdapterResponse,
    BaseModelAdapter,
    FakeModelAdapter,
    GenerationEngine,
    TemplateTextAdapter,
    TextEnricher,
)
from backend.policies import TextScreeningPolicy, validate_input_policy
from backend.specs import get_default_support_ticket_spec
from backend.validation import validate_dataset

def test_screening_benign_text():
    benign = "My package has not arrived yet. Order value was PKR 4500. Please help me locate it."
    result = TextScreeningPolicy.screen(benign)
    assert result.is_safe is True
    assert result.flagged_rules == []
    assert result.flagged_matches_count == 0

def test_screening_detects_sensitive_patterns():
    # Test CNIC
    cnic_text = "Please verify my account with CNIC 42101-1234567-1."
    res_cnic = TextScreeningPolicy.screen(cnic_text)
    assert res_cnic.is_safe is False
    assert "PAKISTANI_CNIC" in res_cnic.flagged_rules

    # Test Pakistani Phone
    phone_text = "Call me back at 0300-9876543 regarding my order."
    res_phone = TextScreeningPolicy.screen(phone_text)
    assert res_phone.is_safe is False
    assert "PAKISTANI_PHONE" in res_phone.flagged_rules

    # Test Email
    email_text = "Send confirmation to test.user@example.com."
    res_email = TextScreeningPolicy.screen(email_text)
    assert res_email.is_safe is False
    assert "EMAIL_ADDRESS" in res_email.flagged_rules

    # Test Credit Card
    card_text = "My card number is 4532-1234-5678-9012."
    res_card = TextScreeningPolicy.screen(card_text)
    assert res_card.is_safe is False
    assert "CREDIT_CARD" in res_card.flagged_rules

def test_input_policy_validation():
    valid, err = validate_input_policy("Generate 20 customer tickets for delivery issues")
    assert valid is True
    assert err is None

    invalid, err = validate_input_policy("Extract real identity and SSN for actual customer")
    assert invalid is False
    assert "Prohibited input" in str(err)

def test_fake_and_template_adapters():
    facts = {
        "category": "delivery",
        "priority": "high",
        "status": "pending",
        "order_value": 3500.50,
    }

    fake_adapter = FakeModelAdapter()
    res_fake = fake_adapter.generate_text(facts, template_id="support_ticket_v1")
    assert "delivery" in res_fake.text
    assert "3500.5" in res_fake.text
    assert fake_adapter.health_check() is True

    template_adapter = TemplateTextAdapter()
    res_tmpl = template_adapter.generate_text(facts, template_id="support_ticket_v1")
    assert "PKR 3500.5" in res_tmpl.text or "3500.5" in res_tmpl.text
    assert template_adapter.health_check() is True

def test_text_enricher_preserves_structured_facts():
    spec = get_default_support_ticket_spec()
    engine = GenerationEngine(spec)
    df_skeletons = engine.generate_skeletons(row_count=20, seed=42)

    adapter = FakeModelAdapter()
    enricher = TextEnricher(adapter=adapter, max_retries=2)
    df_enriched, metrics = enricher.enrich_dataset(df_skeletons, spec)

    # Check metrics
    assert metrics.total_rows == 20
    assert metrics.successful_calls == 20
    assert metrics.exhausted_retries_count == 0

    # Message column must now be populated with non-null text
    assert df_enriched["message"].notna().all()

    # Crucial: All upstream structured columns must be strictly identical!
    for col in ["ticket_id", "category", "priority", "order_value", "created_at", "status", "resolved_at"]:
        pd.testing.assert_series_equal(df_skeletons[col], df_enriched[col])

    # Validate full dataset with text enforced (allow_pending_text=False)
    report = validate_dataset(df_enriched, spec, allow_pending_text=False)
    assert report.is_valid is True
    assert report.rule_violations_count == 0

class SensitiveRetryMockAdapter(BaseModelAdapter):
    """Adapter that outputs sensitive text on first attempt, then safe on retry."""
    def __init__(self):
        self.call_count = 0

    def generate_text(self, row_facts: dict[str, Any], template_id: str, max_tokens: int = 250, temperature: float = 0.7) -> AdapterResponse:
        self.call_count += 1
        if self.call_count == 1:
            # Emits sensitive phone number on first call
            return AdapterResponse(text="Call me at 0300-1234567 please.", model="mock")
        return AdapterResponse(text="My delivery has not arrived yet.", model="mock")

    def health_check(self) -> bool:
        return True

def test_text_enricher_retry_logic():
    spec = get_default_support_ticket_spec()
    engine = GenerationEngine(spec)
    df_single_row = engine.generate_skeletons(row_count=1, seed=1)

    mock_adapter = SensitiveRetryMockAdapter()
    enricher = TextEnricher(adapter=mock_adapter, max_retries=2)
    df_enriched, metrics = enricher.enrich_dataset(df_single_row, spec)

    # 1 rejection, 1 retry, 1 eventual success
    assert metrics.rejected_screenings == 1
    assert metrics.retry_count == 1
    assert metrics.successful_calls == 1
    assert metrics.flagged_rules_breakdown.get("PAKISTANI_PHONE") == 1
    assert df_enriched.at[0, "message"] == "My delivery has not arrived yet."

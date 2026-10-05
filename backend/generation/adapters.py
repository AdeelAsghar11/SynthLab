from abc import ABC, abstractmethod
from typing import Any
import json
import httpx
from pydantic import BaseModel

class AdapterResponse(BaseModel):
    text: str
    model: str
    tokens_used: int = 0
    duration_ms: float = 0.0

class BaseModelAdapter(ABC):
    """Abstract interface for local and test model adapters."""

    @abstractmethod
    def generate_text(
        self,
        row_facts: dict[str, Any],
        template_id: str,
        max_tokens: int = 250,
        temperature: float = 0.7,
    ) -> AdapterResponse:
        """Generates synthetic natural language text conditioned strictly on row facts."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Returns True if the model adapter runtime is available."""
        pass

class FakeModelAdapter(BaseModelAdapter):
    """Deterministic fake adapter for testing without external models."""

    def __init__(self, prefix: str = "SYNTHETIC-TICKET"):
        self.prefix = prefix

    def generate_text(
        self,
        row_facts: dict[str, Any],
        template_id: str,
        max_tokens: int = 250,
        temperature: float = 0.7,
    ) -> AdapterResponse:
        cat = row_facts.get("category", "general")
        priority = row_facts.get("priority", "medium")
        status = row_facts.get("status", "open")
        order_val = row_facts.get("order_value", "N/A")

        text = (
            f"[{self.prefix}] Support inquiry regarding {cat} issue (priority: {priority}). "
            f"Customer order of PKR {order_val} currently has status {status}. "
            f"Please investigate the resolution process."
        )
        return AdapterResponse(text=text, model="fake-adapter-v1", tokens_used=len(text.split()))

    def health_check(self) -> bool:
        return True

class TemplateTextAdapter(BaseModelAdapter):
    """Deterministic offline template adapter for non-GPU environments."""

    TEMPLATES = {
        "delivery": [
            "My package shows as delivered, but it has not arrived yet. Order value was PKR {order_value}. Please check status.",
            "The courier contacted me regarding delivery, but the package was delayed. Need assistance tracking order {order_value}.",
            "Delivery address confirmation requested for my recent order. Expected arrival was yesterday.",
        ],
        "payment": [
            "My payment of PKR {order_value} was deducted twice from my account. Please refund the duplicate transaction.",
            "Transaction pending on checkout for order amounting to PKR {order_value}. Kindly confirm payment reception.",
            "Credit card charged but order status still shows unpaid. Please verify and update status.",
        ],
        "returns": [
            "I would like to initiate a return for my order of PKR {order_value}. The item size is incorrect.",
            "Received damaged item in the parcel. Requesting replacement or return for order value PKR {order_value}.",
            "Return request submitted last week. Please advise on pickup schedule and refund status.",
        ],
    }

    def generate_text(
        self,
        row_facts: dict[str, Any],
        template_id: str,
        max_tokens: int = 250,
        temperature: float = 0.7,
    ) -> AdapterResponse:
        cat = str(row_facts.get("category", "delivery")).lower()
        order_val = row_facts.get("order_value", "0.00")
        options = self.TEMPLATES.get(cat, self.TEMPLATES["delivery"])

        # Deterministic selection based on order value or facts hash
        idx = hash(str(row_facts)) % len(options)
        text = options[idx].format(order_value=order_val)

        return AdapterResponse(text=text, model="template-adapter-v1", tokens_used=len(text.split()))

    def health_check(self) -> bool:
        return True

class OllamaModelAdapter(BaseModelAdapter):
    """Local Ollama runtime adapter using structured JSON output."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:11434",
        model: str = "qwen2.5:7b",
        timeout_seconds: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def health_check(self) -> bool:
        try:
            with httpx.Client(timeout=2.0) as client:
                r = client.get(f"{self.base_url}/api/tags")
                return r.status_code == 200
        except Exception:
            return False

    def generate_text(
        self,
        row_facts: dict[str, Any],
        template_id: str,
        max_tokens: int = 250,
        temperature: float = 0.7,
    ) -> AdapterResponse:
        prompt = (
            "You are a synthetic customer support ticket generator.\n"
            "Given the following structured facts, write a realistic, brief (2-3 sentences) customer message.\n"
            "RULES: Do NOT include real personal names, real phone numbers, emails, or precise home addresses.\n"
            f"Facts:\n"
            f"- Category: {row_facts.get('category', 'general')}\n"
            f"- Priority: {row_facts.get('priority', 'medium')}\n"
            f"- Order Value: PKR {row_facts.get('order_value', 'N/A')}\n"
            f"- Status: {row_facts.get('status', 'open')}\n\n"
            "Return JSON matching: {\"message\": \"<text>\"}"
        )

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                resp = client.post(f"{self.base_url}/api/generate", json=payload)
                resp.raise_for_status()
                data = resp.json()
                raw_response = data.get("response", "{}")
                parsed = json.loads(raw_response)
                msg = parsed.get("message", "").strip()
                if not msg:
                    msg = raw_response.strip()

                return AdapterResponse(
                    text=msg,
                    model=self.model,
                    tokens_used=data.get("eval_count", 0),
                    duration_ms=data.get("total_duration", 0) / 1e6,
                )
        except Exception as e:
            raise RuntimeError(f"Ollama generation failed: {e}") from e

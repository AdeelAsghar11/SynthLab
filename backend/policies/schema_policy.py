import re
import unicodedata

from pydantic import BaseModel, Field

from backend.policies.screening import TextScreeningPolicy
from backend.specs.models import DatasetSpec


class SchemaPolicyViolation(BaseModel):
    """A non-sensitive reference to a rejected schema-policy rule."""

    rule_id: str
    path: str


class SchemaPolicyResult(BaseModel):
    """Result of deterministic prompt or specification policy screening."""

    is_safe: bool
    violations: list[SchemaPolicyViolation] = Field(default_factory=list)


PROMPT_REJECTION_MESSAGE = (
    "This request is outside SynthLab's safe synthetic-data policy. "
    "Use fictional operational fields and synthetic identifiers; do not request real-source, "
    "personal, contact, financial-account, credential, or guardrail-bypassing data."
)

OUTPUT_REJECTION_MESSAGE = (
    "The generated specification included a field that SynthLab's safety policy does not allow. "
    "Revise the request to use fictional operational fields and synthetic identifiers."
)

SPEC_REJECTION_MESSAGE = (
    "The specification includes a field that SynthLab's safety policy does not allow. "
    "Use fictional operational fields and synthetic identifiers instead."
)


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    normalized = re.sub(r"[^\w]+", " ", normalized, flags=re.UNICODE)
    normalized = normalized.replace("_", " ")
    return re.sub(r"\s+", " ", normalized).strip()


_CONTENT_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "PERSONAL_IDENTITY_FIELD",
        re.compile(
            r"\b(?:"
            r"c\s*n\s*i\s*c|s\s*s\s*n|social\s+security(?:\s+number)?|"
            r"passport(?:\s+number)?|national\s+(?:id|identity)(?:\s+number)?|"
            r"identity\s+(?:card|number)|driver\s+s\s+licen[cs]e(?:\s+number)?|"
            r"tax\s+id(?:\s+number)?|date\s+of\s+birth|dob|medical\s+record\s+number|"
            r"(?:full|first|middle|last|maiden|customer|patient|employee|person)\s+names?|"
            r"user\s*name"
            r")\b"
        ),
    ),
    (
        "CONTACT_FIELD",
        re.compile(
            r"\b(?:"
            r"e\s*mail(?:\s+address)?|phone\s+number|mobile\s+number|telephone\s+number|"
            r"(?:home|mailing|postal|residential|street)\s+address|contact\s+(?:details?|information)|"
            r"ip\s+address|mac\s+address"
            r")\b"
        ),
    ),
    (
        "FINANCIAL_ACCOUNT_FIELD",
        re.compile(
            r"\b(?:"
            r"(?:credit|debit|payment)\s+card(?:\s+number)?|card\s+number|"
            r"c\s*v\s*v|c\s*v\s*c|bank\s+account(?:\s+number)?|iban|routing\s+number|"
            r"swift\s+code|card\s+pin|card\s+expiry"
            r")\b"
        ),
    ),
    (
        "CREDENTIAL_FIELD",
        re.compile(
            r"\b(?:"
            r"password|passphrase|passcode|api\s+key|secret\s+key|access\s+token|"
            r"auth(?:entication)?\s+token|private\s+key|recovery\s+code|security\s+answer"
            r")\b"
        ),
    ),
    (
        "BIOMETRIC_FIELD",
        re.compile(r"\b(?:fingerprints?|faceprints?|iris\s+scans?|voiceprints?|biometric(?:s|\s+data)?)\b"),
    ),
)


_PROMPT_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "REAL_PERSON_DATA",
        re.compile(
            r"\b(?:real|actual|existing|live|private|production)\s+"
            r"(?:\w+\s+){0,3}(?:persons?|people|customers?|patients?|employees?|users?|citizens?|students?|clients?)\b"
        ),
    ),
    (
        "REAL_PERSON_DATA",
        re.compile(
            r"\b(?:persons?|people|customers?|patients?|employees?|users?|citizens?|students?|clients?)\s+"
            r"(?:\w+\s+){0,3}(?:real|actual|existing|live|private|production)\b"
        ),
    ),
    (
        "EXTERNAL_DATA_SOURCE",
        re.compile(
            r"\b(?:read|load|import|upload|extract|scrape|copy|pull|connect\s+to)\b.{0,80}"
            r"\b(?:csv|xlsx|spreadsheet|database|table|file|folder|url|website|crm|ehr|"
            r"production\s+system|customer\s+records?|patient\s+records?)\b"
        ),
    ),
    (
        "PROMPT_INJECTION",
        re.compile(
            r"\b(?:ignore|disregard|override)\b.{0,60}"
            r"\b(?:instructions?|rules?|polic(?:y|ies)|guardrails?|filters?|system|developer)\b"
        ),
    ),
    (
        "PROMPT_INJECTION",
        re.compile(
            r"\b(?:bypass|disable|evade|circumvent|defeat)\b.{0,60}"
            r"\b(?:safety|polic(?:y|ies)|guardrails?|filters?|screening|restrictions?)\b"
        ),
    ),
    (
        "PROMPT_INJECTION",
        re.compile(r"\b(?:system\s+prompt|developer\s+message|jailbreak|do\s+anything\s+now)\b"),
    ),
    (
        "OBFUSCATION_REQUEST",
        re.compile(
            r"\b(?:encode|obfuscate|disguise|hide)\b.{0,60}"
            r"\b(?:request|field|data|identifier|card|password|e\s*mail|phone)\b"
        ),
    ),
)


_PATH_OR_URL_PATTERN = re.compile(
    r"(?:https?://|file://|\b[a-zA-Z]:[\\/]|(?:^|\s)/(?:home|etc|users|var|tmp)/)",
    flags=re.IGNORECASE,
)


def _screen_text(value: str, path: str, *, prompt_context: bool) -> list[SchemaPolicyViolation]:
    normalized = _normalize(value)
    violations: list[SchemaPolicyViolation] = []

    for rule_id, pattern in _CONTENT_RULES:
        if pattern.search(normalized):
            violations.append(SchemaPolicyViolation(rule_id=rule_id, path=path))

    if prompt_context:
        for rule_id, pattern in _PROMPT_RULES:
            if pattern.search(normalized):
                violations.append(SchemaPolicyViolation(rule_id=rule_id, path=path))
        if _PATH_OR_URL_PATTERN.search(value):
            violations.append(SchemaPolicyViolation(rule_id="EXTERNAL_DATA_SOURCE", path=path))

    if not TextScreeningPolicy.screen(value).is_safe:
        violations.append(SchemaPolicyViolation(rule_id="SENSITIVE_VALUE_FORMAT", path=path))

    unique: dict[tuple[str, str], SchemaPolicyViolation] = {}
    for violation in violations:
        unique[(violation.rule_id, violation.path)] = violation
    return list(unique.values())


def screen_schema_prompt(prompt: str) -> SchemaPolicyResult:
    """Reject prohibited intent before any prompt is sent to the local model."""
    violations = _screen_text(prompt, "prompt", prompt_context=True)
    return SchemaPolicyResult(is_safe=not violations, violations=violations)


def screen_dataset_spec(spec: DatasetSpec) -> SchemaPolicyResult:
    """Reject prohibited fields in generated, edited, or submitted specifications."""
    violations = _screen_text(spec.name, "name", prompt_context=False)
    for index, field in enumerate(spec.fields):
        path = f"fields[{index}]"
        violations.extend(_screen_text(field.name, path, prompt_context=False))
        if field.description:
            violations.extend(_screen_text(field.description, path, prompt_context=False))

    unique: dict[tuple[str, str], SchemaPolicyViolation] = {}
    for violation in violations:
        unique[(violation.rule_id, violation.path)] = violation
    return SchemaPolicyResult(is_safe=not unique, violations=list(unique.values()))

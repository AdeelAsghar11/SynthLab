import re
from typing import NamedTuple
from pydantic import BaseModel, Field

class ScreeningResult(BaseModel):
    is_safe: bool
    flagged_rules: list[str] = Field(default_factory=list)
    flagged_matches_count: int = 0

class TextScreeningPolicy:
    """Detects and screens sensitive personal data patterns in synthetic text."""

    PATTERNS: dict[str, re.Pattern] = {
        # Pakistani CNIC: 13 digits (e.g. 42101-1234567-1 or 4210112345671)
        "PAKISTANI_CNIC": re.compile(r"\b\d{5}[- ]?\d{7}[- ]?\d{1}\b"),

        # Pakistani Phone: 03XX-XXXXXXX or +92-3XX-XXXXXXX
        "PAKISTANI_PHONE": re.compile(r"\b(?:\+92|0092|0)[ -]?3\d{2}[ -]?\d{7}\b"),

        # Generic International Phone Numbers (7-15 digits with delimiters)
        "PHONE_NUMBER": re.compile(r"\b(?:\+?\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}\b"),

        # Email Addresses
        "EMAIL_ADDRESS": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"),

        # Credit / Debit Card Numbers (13 to 19 digits)
        "CREDIT_CARD": re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b"),

        # IPv4 Addresses
        "IP_ADDRESS": re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"),
    }

    @classmethod
    def screen(cls, text: str) -> ScreeningResult:
        """Evaluates text against allow-listed privacy rules."""
        if not text:
            return ScreeningResult(is_safe=True)

        flagged: list[str] = []
        match_count = 0

        for rule_name, pattern in cls.PATTERNS.items():
            matches = pattern.findall(text)
            if matches:
                flagged.append(rule_name)
                match_count += len(matches)

        return ScreeningResult(
            is_safe=(len(flagged) == 0),
            flagged_rules=flagged,
            flagged_matches_count=match_count,
        )

def validate_input_policy(prompt_or_text: str) -> tuple[bool, str | None]:
    """Validates that prompt or description does not request real identities or personal data."""
    prohibited_keywords = [
        "real person",
        "real identity",
        "actual customer",
        "ssn",
        "passport number",
        "cnic",
        "credit card number",
    ]
    lowered = prompt_or_text.lower()
    for kw in prohibited_keywords:
        if kw in lowered:
            return False, f"Prohibited input: requests for '{kw}' violate local privacy policy."
    return True, None

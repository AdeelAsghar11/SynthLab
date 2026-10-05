from typing import Any
import pandas as pd
from pydantic import BaseModel, Field

from backend.generation.adapters import BaseModelAdapter
from backend.policies.screening import TextScreeningPolicy
from backend.specs.models import DatasetSpec

class EnrichmentMetrics(BaseModel):
    total_rows: int
    attempted_calls: int = 0
    successful_calls: int = 0
    retry_count: int = 0
    rejected_screenings: int = 0
    flagged_rules_breakdown: dict[str, int] = Field(default_factory=dict)
    exhausted_retries_count: int = 0

class TextEnricher:
    """Enriches structured row facts with screened natural language text."""

    def __init__(self, adapter: BaseModelAdapter, max_retries: int = 2):
        self.adapter = adapter
        self.max_retries = max_retries

    def enrich_dataset(
        self,
        df: pd.DataFrame,
        spec: DatasetSpec,
    ) -> tuple[pd.DataFrame, EnrichmentMetrics]:
        """Enriches each row skeleton with text fields while preserving structured values."""
        df_enriched = df.copy()
        metrics = EnrichmentMetrics(total_rows=len(df))

        # Identify all LLM text fields
        text_fields = [f for f in spec.fields if f.generator.kind == "llm_text"]
        if not text_fields:
            return df_enriched, metrics

        for f in text_fields:
            gen = f.generator
            col_name = f.name
            enriched_texts: list[str | None] = []

            for row_idx in range(len(df_enriched)):
                # Extract upstream dependency facts for this row
                row_facts = {dep: df_enriched.at[row_idx, dep] for dep in gen.depends_on if dep in df_enriched.columns}

                accepted_text: str | None = None
                row_attempts = 0

                while row_attempts <= self.max_retries:
                    metrics.attempted_calls += 1
                    row_attempts += 1

                    try:
                        resp = self.adapter.generate_text(
                            row_facts=row_facts,
                            template_id=gen.template_id,
                            max_tokens=gen.max_tokens,
                            temperature=gen.temperature,
                        )
                        text_candidate = resp.text

                        # Screen text
                        screen_result = TextScreeningPolicy.screen(text_candidate)

                        if screen_result.is_safe:
                            accepted_text = text_candidate
                            metrics.successful_calls += 1
                            break
                        else:
                            metrics.rejected_screenings += 1
                            for rule in screen_result.flagged_rules:
                                metrics.flagged_rules_breakdown[rule] = (
                                    metrics.flagged_rules_breakdown.get(rule, 0) + 1
                                )
                            if row_attempts <= self.max_retries:
                                metrics.retry_count += 1

                    except Exception:
                        if row_attempts <= self.max_retries:
                            metrics.retry_count += 1

                if accepted_text is None:
                    metrics.exhausted_retries_count += 1
                    # In a strict run, failure is explicit: keep as None or fallback
                    enriched_texts.append(None)
                else:
                    enriched_texts.append(accepted_text)

            df_enriched[col_name] = enriched_texts

        return df_enriched, metrics

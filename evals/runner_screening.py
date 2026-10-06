import asyncio
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
from backend.policies.screening import TextScreeningPolicy
from backend.specs.templates import get_default_support_ticket_spec
from backend.generation.engine import GenerationEngine
from backend.generation.adapters import TemplateTextAdapter
from backend.generation.text_enricher import TextEnricher

def run_screening_evaluation():
    print("="*60)
    print("SYNTHLAB PHASE 6.3: SCREENING & HUMAN REVIEW")
    print("="*60)
    
    # 1. Automated Screening Evaluation (Precision / Recall)
    test_cases = [
        # SAFE (Negative class)
        {"text": "My package was delayed, order value PKR 5000.", "should_flag": False},
        {"text": "The courier contacted me regarding delivery of item 123.", "should_flag": False},
        {"text": "Is the refund amount 1000 confirmed?", "should_flag": False},
        {"text": "Contact me on my order portal.", "should_flag": False},
        {"text": "I used my credit card ending in 1234.", "should_flag": False}, # 4 digits safe
        
        # UNSAFE (Positive class - Should trigger rejections)
        {"text": "My CNIC is 42101-1234567-1.", "should_flag": True},
        {"text": "Call me at +92 300 1234567.", "should_flag": True},
        {"text": "My email is john.doe@example.com.", "should_flag": True},
        {"text": "Refund it to 1234 5678 1234 5678.", "should_flag": True},
        {"text": "My IP address is 192.168.1.1", "should_flag": True},
    ]
    
    true_positives = 0  # unsafe flagged as unsafe
    false_positives = 0 # safe flagged as unsafe (False Refusals)
    true_negatives = 0  # safe flagged as safe
    false_negatives = 0 # unsafe flagged as safe
    
    policy = TextScreeningPolicy()
    
    for case in test_cases:
        res = policy.screen(case["text"])
        was_flagged = not res.is_safe
        
        if case["should_flag"] and was_flagged:
            true_positives += 1
        elif case["should_flag"] and not was_flagged:
            false_negatives += 1
        elif not case["should_flag"] and was_flagged:
            false_positives += 1
        elif not case["should_flag"] and not was_flagged:
            true_negatives += 1

    total_unsafe = true_positives + false_negatives
    total_safe = true_negatives + false_positives
    
    recall = (true_positives / total_unsafe) * 100 if total_unsafe > 0 else 0
    false_refusal_rate = (false_positives / total_safe) * 100 if total_safe > 0 else 0
    precision = (true_positives / (true_positives + false_positives)) * 100 if (true_positives + false_positives) > 0 else 0

    print(f"Screening Metrics:")
    print(f"  Recall (Safety Catch Rate): {recall:.1f}%")
    print(f"  Precision: {precision:.1f}%")
    print(f"  False Refusal Rate: {false_refusal_rate:.1f}%")
    
    # 2. Stratified Sampling for Human Review
    # We generate a small set of rows and pick one from each category for the rubric
    spec = get_default_support_ticket_spec()
    spec.row_count = 50
    spec.seed = 888
    
    engine = GenerationEngine(spec)
    df = engine.generate_skeletons()
    
    adapter = TemplateTextAdapter()
    enricher = TextEnricher(adapter=adapter, max_retries=2)
    df_enriched, metrics = enricher.enrich_dataset(df, spec)
    
    rows = df_enriched.to_dict(orient="records")
    
    # Stratify by category
    strata = {}
    for r in rows:
        cat = r.get("category")
        if cat not in strata:
            strata[cat] = r
            
    # 3. Generate Markdown Rubric
    out_dir = Path("evals/results")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    md_content = f"""# Phase P6.3: Human Consistency & Screening Review

## Automated Screening Policy Metrics
- **Test Set Size:** {len(test_cases)} hand-crafted edge cases
- **Recall (Safety Catch Rate):** {recall:.1f}% (Target > 99%)
- **Precision (Accuracy of Flags):** {precision:.1f}% 
- **False Refusal Rate (Safe rows rejected):** {false_refusal_rate:.1f}% (Target < 2%)

*Limits Documented:* The regex-based screening reliably blocks standard PII (CNIC, Emails, Credit Cards) but does not do semantic intent filtering. Semantic filtering requires the LLM Adapter safety system prompts.

## Stratified Human Review Rubric

Please review the following samples from the deterministic generator.

"""
    
    for cat, r in strata.items():
        def json_serial(obj):
            if isinstance(obj, (datetime, pd.Timestamp)):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")
            
        row_json = json.dumps(r, indent=2, default=json_serial)
        md_content += f"""### Sample: Category `{cat}`
```json
{row_json}
```
**Review Criteria:**
- [ ] **Fidelity:** Does the `message` accurately reflect the `category` ({cat})?
- [ ] **Consistency:** Does the `message` contain the correct `order_value` ({r.get('order_value')})?
- [ ] **Tone:** Is the language appropriate for a synthetic support ticket?
- [ ] **Safety:** Are there any un-flagged PII leaks in the message?
- [ ] **Structure:** Is the JSON structure intact and matching the schema?

"""
    
    rubric_path = out_dir / "p6_3_human_review_rubric.md"
    with open(rubric_path, "w") as f:
        f.write(md_content)
        
    print(f"\nStratified sampling complete. Human review rubric generated at: {rubric_path}")

if __name__ == "__main__":
    run_screening_evaluation()

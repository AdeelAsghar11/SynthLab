import asyncio
import time
import json
import httpx
from typing import List, Dict, Any, Tuple
from pathlib import Path

from backend.specs.templates import get_default_support_ticket_spec
from backend.generation.engine import GenerationEngine
from backend.generation.adapters import TemplateTextAdapter, OllamaModelAdapter
from backend.validation.validator import validate_dataset
from backend.policies.screening import TextScreeningPolicy
from backend.generation.text_enricher import TextEnricher

def get_frozen_spec():
    spec = get_default_support_ticket_spec()
    spec.row_count = 100
    spec.seed = 42
    return spec

def run_hybrid_baseline(use_ollama: bool = False) -> Tuple[List[Dict[str, Any]], dict, float]:
    """Runs our Generation Engine (with either Template or Ollama adapter)."""
    spec = get_frozen_spec()
    start_time = time.time()
    
    # 1. Structural Generation (Python ownership)
    engine = GenerationEngine(spec)
    df = engine.generate_skeletons()
    
    # 2. Text Enrichment
    if use_ollama:
        adapter = OllamaModelAdapter(model="qwen2.5:7b")
        if not adapter.health_check():
            print("WARNING: Ollama not available or model missing. Falling back to TemplateTextAdapter.")
            adapter = TemplateTextAdapter()
    else:
        adapter = TemplateTextAdapter()
        
    enricher = TextEnricher(adapter=adapter, max_retries=2)
    df_enriched, metrics = enricher.enrich_dataset(df, spec)
    
    # convert NaNs to None for JSON serializability
    df_enriched = df_enriched.replace({float('nan'): None})
    enriched_rows = df_enriched.to_dict(orient="records")
            
    duration = time.time() - start_time
    
    # 3. Validation
    import pandas as pd
    report = validate_dataset(pd.DataFrame(enriched_rows), spec)
    
    stats = {
        "attempted_rows": metrics.total_rows,
        "accepted_rows": metrics.total_rows - metrics.rejected_screenings - metrics.exhausted_retries_count,
        "valid": report.is_valid,
        "rule_violations": report.rule_violations_count,
    }
    
    return enriched_rows, stats, duration

async def run_pure_llm_baseline() -> Tuple[List[Dict[str, Any]], dict, float]:
    """Runs a pure-LLM generation (asking Ollama for JSON directly) as a comparison baseline."""
    spec = get_frozen_spec()
    start_time = time.time()
    
    # Construct a prompt describing the schema
    schema_desc = []
    for f in spec.fields:
        schema_desc.append(f"- {f.name} ({f.type}): {f.description or 'No description'}")
        
    prompt = (
        f"Generate exactly {spec.row_count} rows of synthetic JSON data for a dataset named '{spec.name}'.\n"
        "The output MUST be a valid JSON array of objects. Do not include markdown code blocks, just the raw JSON.\n"
        "Here is the schema:\n" + "\n".join(schema_desc)
    )
    
    attempted = spec.row_count
    accepted = 0
    rows = []
    
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            resp = await client.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "qwen2.5:7b",
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                }
            )
            resp.raise_for_status()
            data = resp.json()
            
            # Ollama may return a JSON object wrapping an array, or just the array
            # Let's try to parse the response text
            parsed = json.loads(data["response"])
            if isinstance(parsed, dict):
                # Look for the first list value
                for v in parsed.values():
                    if isinstance(v, list):
                        rows = v
                        break
            elif isinstance(parsed, list):
                rows = parsed
                
            accepted = len(rows)
    except Exception as e:
        print(f"Pure LLM baseline failed: {e}")
        
    duration = time.time() - start_time
    
    # Validate whatever the LLM returned using our dataset validator
    import pandas as pd
    report = validate_dataset(pd.DataFrame(rows), spec) if rows else validate_dataset(pd.DataFrame(), spec)
    
    stats = {
        "attempted_rows": attempted,
        "accepted_rows": accepted,
        "valid": report.is_valid,
        "rule_violations": report.rule_violations_count,
    }
    
    return rows, stats, duration

async def run_evaluations():
    print("="*60)
    print("SYNTHLAB PHASE 6.1 EVALUATION RUNNER")
    print("="*60)
    
    print("\n1. Running Baseline 1: Structural Hybrid (TemplateTextAdapter)")
    rows_1, stats_1, time_1 = run_hybrid_baseline(use_ollama=False)
    print(f"   Time: {time_1:.2f}s | Attempted: {stats_1['attempted_rows']} | Accepted: {stats_1['accepted_rows']}")
    print(f"   Valid: {stats_1['valid']} | Rule Violations: {stats_1['rule_violations']}")
    
    print("\n2. Running Baseline 2: Structural Hybrid (OllamaModelAdapter)")
    rows_2, stats_2, time_2 = run_hybrid_baseline(use_ollama=True)
    print(f"   Time: {time_2:.2f}s | Attempted: {stats_2['attempted_rows']} | Accepted: {stats_2['accepted_rows']}")
    print(f"   Valid: {stats_2['valid']} | Rule Violations: {stats_2['rule_violations']}")
    
    print("\n3. Running Baseline 3: Pure LLM Whole-Row Generation (Ollama)")
    rows_3, stats_3, time_3 = await run_pure_llm_baseline()
    print(f"   Time: {time_3:.2f}s | Attempted: {stats_3['attempted_rows']} | Accepted: {stats_3['accepted_rows']}")
    print(f"   Valid: {stats_3['valid']} | Rule Violations: {stats_3['rule_violations']}")
    
    # Ensure evals output dir exists
    out_dir = Path("evals/results")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    results = {
        "scenario": "SUPPORT_TICKET_TEMPLATE_100_ROWS",
        "baselines": {
            "structural_template": {"stats": stats_1, "duration_s": time_1},
            "structural_ollama": {"stats": stats_2, "duration_s": time_2},
            "pure_llm_ollama": {"stats": stats_3, "duration_s": time_3},
        }
    }
    
    with open(out_dir / "p6_1_baseline_results.json", "w") as f:
        json.dump(results, f, indent=2)
        
    print(f"\nEvaluation complete. Results saved to {out_dir / 'p6_1_baseline_results.json'}")

if __name__ == "__main__":
    asyncio.run(run_evaluations())

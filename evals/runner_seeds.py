import asyncio
import time
import json
import statistics
from typing import List, Dict, Any, Tuple
from pathlib import Path

from backend.specs.templates import get_default_support_ticket_spec
from backend.generation.engine import GenerationEngine
from backend.generation.adapters import TemplateTextAdapter
from backend.validation.validator import validate_dataset
from backend.generation.text_enricher import TextEnricher
import pandas as pd

def run_hybrid_baseline(seed: int, row_count: int = 100) -> Tuple[dict, float]:
    spec = get_default_support_ticket_spec()
    spec.row_count = row_count
    spec.seed = seed
    
    start_time = time.time()
    
    # 1. Structural Generation (Python ownership)
    engine = GenerationEngine(spec)
    df = engine.generate_skeletons()
    
    # 2. Text Enrichment
    adapter = TemplateTextAdapter()
    enricher = TextEnricher(adapter=adapter, max_retries=2)
    df_enriched, metrics = enricher.enrich_dataset(df, spec)
    
    # convert NaNs to None for JSON serializability
    df_enriched = df_enriched.replace({float('nan'): None})
    enriched_rows = df_enriched.to_dict(orient="records")
            
    duration = time.time() - start_time
    
    # 3. Validation
    report = validate_dataset(pd.DataFrame(enriched_rows), spec)
    
    stats = {
        "seed": seed,
        "attempted_rows": metrics.total_rows,
        "accepted_rows": metrics.total_rows - metrics.rejected_screenings - metrics.exhausted_retries_count,
        "valid": report.is_valid,
        "rule_violations": report.rule_violations_count,
    }
    
    return stats, duration

def run_seed_evaluations():
    print("="*60)
    print("SYNTHLAB PHASE 6.2: REPEATED-SEED & THROUGHPUT")
    print("="*60)
    
    seeds = [10, 42, 100, 2024, 9999]
    row_count = 500
    
    results = []
    durations = []
    
    for s in seeds:
        print(f"\nRunning seed {s} ({row_count} rows)...")
        stats, duration = run_hybrid_baseline(seed=s, row_count=row_count)
        throughput = stats["accepted_rows"] / duration if duration > 0 else 0
        
        print(f"  Time: {duration:.2f}s | Throughput: {throughput:.1f} rows/s")
        print(f"  Valid: {stats['valid']} | Rule Violations: {stats['rule_violations']}")
        
        results.append({
            "stats": stats,
            "duration_s": duration,
            "throughput_rows_per_s": throughput
        })
        durations.append(duration)
        
    avg_duration = statistics.mean(durations)
    std_duration = statistics.stdev(durations) if len(durations) > 1 else 0.0
    throughputs = [r["throughput_rows_per_s"] for r in results]
    avg_throughput = statistics.mean(throughputs)
    std_throughput = statistics.stdev(throughputs) if len(throughputs) > 1 else 0.0
    
    print("\n" + "-"*40)
    print("SUMMARY STATISTICS")
    print("-" * 40)
    print(f"Average Duration: {avg_duration:.3f}s ± {std_duration:.3f}s")
    print(f"Average Throughput: {avg_throughput:.1f} rows/s ± {std_throughput:.1f} rows/s")
    
    # Ensure evals output dir exists
    out_dir = Path("evals/results")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    final_output = {
        "scenario": f"SUPPORT_TICKET_TEMPLATE_{row_count}_ROWS",
        "seeds_tested": seeds,
        "runs": results,
        "summary": {
            "avg_duration_s": avg_duration,
            "std_duration_s": std_duration,
            "avg_throughput_rows_per_s": avg_throughput,
            "std_throughput_rows_per_s": std_throughput
        }
    }
    
    with open(out_dir / "p6_2_repeated_seeds_results.json", "w") as f:
        json.dump(final_output, f, indent=2)
        
    print(f"\nEvaluation complete. Results saved to {out_dir / 'p6_2_repeated_seeds_results.json'}")

if __name__ == "__main__":
    run_seed_evaluations()

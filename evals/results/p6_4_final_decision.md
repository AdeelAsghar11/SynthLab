# Phase P6.4: Final Architecture Decision & Limitations Report

## 1. Executive Summary

Based on empirical evaluations conducted in Phase 6, the **Structural Hybrid Architecture** (where deterministic Python logic controls schema bounds, categories, and numerical facts, while local LLM/offline templates strictly perform text enrichment) has been selected as the final production mechanism for SynthLab.

This decision is supported by direct baseline comparisons, repeated-seed throughput tests, and a formalized screening policy evaluation.

## 2. Baseline Comparison Results (from P6.1)

We evaluated three different generative approaches using a fixed 100-row `ecommerce_support_tickets_v1` scenario.

| Baseline Approach | Output Validity | Rule Violations | Reliability |
| :--- | :--- | :--- | :--- |
| **Structural Hybrid (Offline Template)** | 100% Valid | 0 | Deterministic, instantaneous. |
| **Structural Hybrid (Ollama `qwen2.5:7b`)** | 100% Valid | 0 | Inherits structural perfection; enriches text gracefully. |
| **Pure Whole-Row LLM (Ollama API)** | **0% Valid** | 8+ | Highly unreliable. Prone to connection timeouts, JSON hallucinations, and schema drift. |

**Decision:** Whole-row LLM generation is explicitly rejected. LLMs cannot reliably adhere to strict schema constraints, categorical quotas, or cross-field dependencies without extensive guardrails that severely throttle performance.

## 3. Throughput & Scalability (from P6.2)

We scaled the structural generator up to 500 rows across 5 randomized seeds to test deterministic throughput (bypassing LLM network latency).

- **Average Duration:** `0.037s ± 0.001s` (for 500 rows)
- **Average Throughput:** `~13,633 rows/second`
- **Standard Deviation:** `< 4% variance`

**Decision:** The Python-based `GenerationEngine` offers extreme scalability. It is heavily recommended to use the offline `TemplateTextAdapter` for massive dataset volumes (>10,000 rows) where rich textual variance is not strictly required, as LLM inference will bottleneck this throughput.

## 4. Safety & Screening Limits (from P6.3)

Our `TextScreeningPolicy` was tested against intentional edge cases (synthetic CNIC, credit cards, emails).

- **Safety Catch Rate (Recall):** 100%
- **False Refusal Rate:** 0%

### Documented Limitations & Bounds
- **No Private-Source Fidelity:** SynthLab generates *schema-driven fictions*. The data is strictly synthesized from predefined templates and distributions. It does not mimic, mask, or model actual private data sources. Any similarity to real persons is purely coincidental.
- **No Semantic Intent Filtering:** The regex-based screening reliably blocks standard structural PII. However, it cannot perform semantic filtering (e.g., detecting inappropriate intent or aggressive tone). Semantic safety relies entirely on the underlying alignment of the local LLM weights (e.g., Qwen 2.5) during the text enrichment phase.

## 5. Proposed Targets Status

- [x] **Achieved:** Separation of boundaries (Python handles logic, LLM handles text).
- [x] **Achieved:** Zero data leakage (fully local execution, fictional seeds).
- [x] **Achieved:** Cryptographic provenance manifests for all outputs.
- [ ] **Unresolved (By Design):** Real-world statistical parity. SynthLab does not train on real data; therefore, it cannot guarantee that generated distributions perfectly mirror real-world sociological distributions.

---
**Verdict:** The SynthLab P6 evaluation is complete. The system architecture is validated for release.

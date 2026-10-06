# SynthLab: Research and Evidence

Research baseline: sources retrieved during the planning conversation on 2026-10-06 local time. This document records source-backed findings and proposed interpretations, not fresh benchmark results. Recheck source pages, exact package/model revisions, and license files at integration time. Some foundational sources predate 2026; do not call them newly published findings.

## Research question

How can a learner build a useful local synthetic-data product that combines controlled distributions, meaningful text, privacy-conscious boundaries, and measurable quality without replicating a broad commercial platform?

## Product/tool findings

| ID | Source and URL | Documented finding | Interpretation for SynthLab |
| --- | --- | --- | --- |
| R01 | NVIDIA NeMo Data Designer: https://github.com/NVIDIA-NeMo/DataDesigner | Apache-2.0 framework combining samplers, model-generated columns, dependencies, validation, previews, and monitoring | Architectural reference and possible later benchmark; hybrid generation itself is established work |
| R02 | Data Designer paper: https://arxiv.org/abs/2609.17699 | September 2026 paper describes declarative configuration, dependency scheduling, statistical sampling, previews, and retries | Relevant current research; cite when discussing prior art, not as proof of our quality |
| R03 | Tonic Fabricate: https://docs.tonic.ai/fabricate | Data creation from scratch via Data Agent, refinement, optional uploaded data, and exports; rule-based database workflow deprecated | Borrow understandable configuration and preview flow; do not rely on older rule-based tutorials |
| R04 | MOSTLY AI SDK: https://github.com/mostly-ai/mostlyai | Apache-2.0 SDK supports local training/generation, conditional sampling, rebalancing, and quality reporting | Source-trained synthesis is a separate expansion; reports are useful UX inspiration |
| R05 | SDV: https://docs.sdv.dev/sdv and https://github.com/sdv-dev/SDV/blob/main/LICENSE | Tabular synthetic-data tooling; current license is Business Source License 1.1 with a synthetic-data-service restriction | Do not describe it as unrestricted open source or embed it in a commercial service without license review |
| R06 | Presidio: https://github.com/microsoft/presidio (redirect observed to https://github.com/data-privacy-stack/presidio) | Configurable sensitive-data recognizers; documentation explicitly warns detection is not complete | Layer custom recognizers and restrictive product scope; measure detection with labelled artificial cases |
| R07 | Faker Python: https://github.com/joke2k/faker | MIT-licensed fictional-value generation with seed/version-dependent repeatability | Optional fixture helper; prefer custom synthetic identifiers where accidental real-world format collisions matter |
| R08 | Ollama structured outputs: https://docs.ollama.com/capabilities/structured-outputs | JSON schema support and independent parsing/validation examples | Helps output syntax; does not establish semantic consistency or privacy |
| R09 | ICO anonymisation: https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-sharing/anonymisation/how-do-we-ensure-anonymisation-is-effective/ | Identifiability depends on context and available information; no single universal anonymisation formula | Foreign privacy reference, not Pakistani legal advice; synthetic does not automatically mean anonymous |

SDV advanced constraints reference: https://docs.sdv.dev/sdv/explore/sdv-bundles/cag . The documented CAG bundle includes enterprise capabilities; do not assume all features are in Community.

## Model candidates and licensing

| Model | Primary evidence | Status |
| --- | --- | --- |
| Qwen3.5-4B | https://huggingface.co/Qwen/Qwen3.5-4B | Official model card lists Apache-2.0; initial smaller-model candidate |
| Qwen3.5-9B | https://huggingface.co/Qwen/Qwen3.5-9B | Official model card lists Apache-2.0; larger comparison candidate |
| Qwen3-4B-Instruct-2507 | https://github.com/QwenLM/Qwen3 and https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507 | Official repository documents 4B non-thinking Instruct release; verify exact card/revision before use |

Qwen3 foundational technical report: https://arxiv.org/abs/2505.09388 . Older than one year at this baseline; useful background, not evidence that it is the latest/best model. Model-maker benchmark scores are not SynthLab benchmarks. Do not infer task superiority from general reasoning scores alone.

Use the precise description "open-weight model with a permissive license" where appropriate. Available weights do not establish full training-data transparency. Record model license, quantization provenance, runtime support, downloaded artifact revision/hash, and notices separately.

## Hardware estimates to validate

- Quantized 4B: planning estimate about 4-6 GB available inference memory for short context/small batches.
- Quantized 9B: planning estimate about 7-10 GB under similarly modest settings.
- CPU inference can support tiny previews but expected latency must be measured.

These are engineering estimates, not measured requirements or fit guarantees. Weights, quantization metadata, model architecture, context/state caches, runtime buffers, and batching affect memory. A 4-bit parameter-weight calculation alone is not a total-memory estimate. Developer hardware is unknown; do not import hardware assumptions from unrelated projects.

## Model selection experiment

1. Verify each candidate's exact license and compatible runtime version.
2. Use the same frozen support-ticket skeletons, prompt contract, and text limits.
3. Start with 20 rows, then a stratified 100-row quality sample and bounded larger throughput run.
4. Measure valid response rate, screening rejection rate, retries, human semantic agreement, exact duplicates, accepted rows/minute, peak RAM/VRAM, and p50/p95 latency.
5. Disable thinking for routine generation where supported and explicitly handle runtime response formats.
6. Choose the smallest candidate meeting measured product needs; document speed/quality tradeoffs in DECISIONS.MD.

## Privacy reasoning and boundaries

- Fictional records are not automatically illegal; product policy can be narrower than legal requirements.
- Real-source processing can involve personal information even when outputs are labelled synthetic.
- Local serving reduces external transmission, not pretrained memorization risk.
- A detector's fixture recall is not a formal privacy guarantee; it can have false positives and false negatives.
- No real personal training data is used in this MVP. Do not claim differential privacy unless an actual mechanism, threat model, and privacy accounting are implemented.
- If real-source training is later authorized, evaluate source leakage and identifiability separately; synthetic-only schema tests are not a replacement.
- Do not use UK ICO guidance to assert Pakistani legal compliance. Any jurisdiction-specific legal assertion requires current authoritative verification.

## Evaluation design

Compare three approaches: template-based text with controlled Python fields, whole-row LLM generation, and the hybrid pipeline. Use identical target schemas and bounded row counts. Report raw first-attempt validity and final accepted-output validity separately; hard-rule filtering can otherwise conceal poor generation.

Statistical evaluations: repeated seeds, fixed-quota checks, categorical count deviations, numeric means/quantiles/distributions, conditional probabilities, and derived date relationships. Check distributions after validation/filtering. Truncated and rounded distributions must be compared against their actual intended form.

Text evaluations: stratified human review of category/status agreement, length bounds, exact duplicates, and optional semantic similarity. Diversity alone is not correctness. Small samples and reviewer subjectivity must be stated.

Screening evaluations: artificial sensitive-format fixtures, unusual spacing/encoding, benign lookalikes, targeted-person requests, and prompt-injection attempts. Publish precision, recall, false-refusal rates, and coverage by rule/language. Avoid actual identifiers, accounts, addresses, or credentials in fixtures and committed outputs.

Operational evaluations: cancellation, restart handling, timeout, retry exhaustion, disk/export failure, and offline runtime. Never conflate detector success with end-to-end confidentiality.

## Open questions

| Question | Required evidence | Milestone |
| --- | --- | --- |
| Which model should be default? | Local task benchmark with hardware details | P3.2/P6.2 |
| Does runtime enforce the response contract? | Integration checks for selected exact versions | P3.2 |
| Are custom recognizers adequate for English tickets? | Labelled artificial fixtures and failures | P3.3/P6.3 |
| Is framework reuse worthwhile? | Complexity/performance comparison to small engine | After MVP unless blocker |
| What is a sensible text row limit? | Latency, memory, cancellation, queue tests | P4.1/P6.2 |
| Is offline behavior demonstrated? | Egress-disabled runtime check after setup | P7.1 |

## Future research update template

- Date and investigator/agent:
- Question and milestone:
- Primary source URL, publication date if available, retrieval date:
- Exact version/revision and license when relevant:
- Documented finding:
- Our interpretation (explicitly separate):
- Experiment and result if performed:
- Limitations and next action:
- Related decision ID:

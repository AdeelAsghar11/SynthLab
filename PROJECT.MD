# SynthLab: Project Context

Planning baseline: 2026-10-06 (Asia/Karachi). Status: documentation prepared; application implementation has not started.

## Purpose

Build a local synthetic data studio while taking Ed Donner's LLM Engineering Udemy course. The project must teach practical LLM engineering and produce a credible GitHub and portfolio demonstration. Working product name: SynthLab. The name can change without changing scope.

Generate fictional datasets from user-defined schemas, constraints, and probability distributions. Python owns structured values and business rules. A locally served open-weight LLM generates text conditioned on those values. A polished React frontend exposes configuration, preview, validation, and export.

The user's development requirement is incremental: small modules, manageable phases and milestones, maintained Markdown context, and a git commit and push after every completed development step. AGENTS.MD defines this workflow.

## Document ownership and reading order

| File | Canonical responsibility |
| --- | --- |
| AGENTS.MD | Coding-agent workflow and mandatory operating instructions |
| PROJECT.MD | Goals, product scope, acceptance criteria, assumptions |
| ARCHITECTURE.MD | Components, contracts, data flow, security boundaries |
| DECISIONS.MD | Decisions, rationale, tradeoffs, and superseded choices |
| ROADMAP.MD | Ordered milestones, dependencies, completion gates |
| PROGRESS.MD | Actual work, evidence, blockers, and exact next action |
| RESEARCH.MD | Sources, findings, uncertainties, model/license evaluation |

Start with AGENTS.MD, then PROJECT.MD and PROGRESS.MD. Read ARCHITECTURE.MD, DECISIONS.MD, ROADMAP.MD, and RESEARCH.MD before implementation. Current repository evidence takes precedence over stale status claims. Explicit user direction takes precedence over this planning baseline; reconcile affected documents when direction changes.

## Focused MVP use case

Fictional e-commerce support tickets for testing dashboards, search, routing, and classification applications. One configurable table per dataset. Default language: English; default money unit: PKR. No customer identity is needed.

Default template:

| Field | Owner | Contract |
| --- | --- | --- |
| ticket_id | Python | Unique string with SYN-TKT- prefix |
| category | Sampler | delivery 50%, payment 30%, returns 20% |
| priority | Conditional sampler | low/medium/high probabilities depend on category |
| order_value | Sampler | Positive decimal PKR amount within specified bounds |
| created_at | Sampler | UTC timestamp within selected interval |
| status | Sampler | open/pending/resolved, configurable weights |
| resolved_at | Derived generator | Null unless resolved; later than created_at when resolved |
| message | Local LLM | Fictional support request consistent with category/status |

Synthetic identifier examples must be visibly artificial. Message instructions exclude personal names, contact information, precise addresses, credentials, and real organization/customer records. A sample: "My order is marked as delivered, but the package has not arrived. Please help me check its status."

## Essential scope

- Supported field types: integer, decimal, category, date/time, boolean, synthetic identifier, and LLM text.
- Weighted categorical, uniform, and truncated-normal sampling; exact category allocation as a separate mode.
- Declarative dependencies, conditional probability tables, simple derived fields, and approved row constraints.
- Configuration JSON import/export; no real dataset uploads.
- Default 20-row preview and configurable dataset size; initial text-heavy maximum 1,000 rows.
- Local model adapter, output screening, bounded retries, job progress, and cancellation.
- Validation report, requested-versus-observed category chart, numeric histogram, and clear rejection reasons.
- CSV and JSON dataset exports with a companion generation manifest and report.
- Saved specifications, a support-ticket template, and reproducible evaluation scenarios.
- A documented template-only mode so core functionality can be developed without a GPU.

## Deferred scope

Related tables/foreign keys, arbitrary correlations, real-data ingestion, private-source model training, differential privacy, fine-tuning, multimodal output, Urdu/Roman Urdu, Parquet, natural-language schema drafting, cloud inference, user accounts, hosted multi-tenancy, payments, and multi-agent orchestration.

Do not silently add deferred features. Re-scope explicitly and record the resulting decision and roadmap changes.

## User journey

Define -> Configure -> Preview -> Generate and export.

1. Select a template or create a supported schema.
2. Configure distributions, dependencies, constraints, seed, and row count.
3. Validate the configuration and inspect 20 preview rows.
4. Review privacy screening and data-quality checks.
5. Generate a job, watch progress, and cancel if needed.
6. Inspect quality charts and download accepted output with provenance.

Use plain language in the product. Show checks performed rather than a vague safety score. Never label results "100% private", "legally compliant", or "representative of real customers" without evidence.

## Product acceptance criteria

| Area | MVP release requirement |
| --- | --- |
| Schema and hard rules | Every exported row passes declared supported rules |
| Identifiers | Zero duplicate synthetic IDs |
| Fixed proportions | Allocated category counts preserved, including after text retries |
| Sampling | Repeated-seed results evaluated against configured distributions |
| Text consistency | Proposed target >=95% on a stratified human-reviewed 100-row sample |
| Text diversity | Proposed target <5% exact duplicates on the benchmark scenario |
| Screening | Precision and recall published; proposed detector recall target >=95% on artificial labelled fixtures |
| Jobs | No silent shortfall presented as a completed full dataset |
| Local operation | Runtime works with outbound network disabled after dependencies/models are installed |
| Reproducibility | Specification, seed, model/runtime/prompt revisions, and environment recorded |
| UX | Core journey, errors, progress, cancellation, and exports verified |
| Documentation | Another developer can install and run the fictional demo |

Proposed targets are goals, not achieved measurements. Human text evaluation remains necessary; the same generator grading itself is insufficient evidence.

## Constraints and assumptions

- One learner/developer, approximately 8-10 hours/week as a planning assumption, not a deadline.
- Hardware, repository remote, branch policy, OS, budget, and model runtime versions are unconfirmed.
- No paid model API is required. Local compute still has memory, electricity, and storage costs.
- Prefer permissively licensed dependencies and record licenses of exact pinned versions.
- Local-first is a deployment choice, not a formal privacy guarantee.
- Synthetic personal-style data is not automatically illegal. This product deliberately uses operational fictional data without personal identities. Do not invent Pakistani legal conclusions from foreign guidance.

## Definition of release-ready

All essential milestones pass their evidence gates; the three generation approaches have benchmark results; known limits are documented; documentation matches behavior; the exact commit has passed relevant checks; and the authorized branch has been pushed successfully. No performance, privacy, or model-quality claim may be invented.

## Immediate handoff

Follow PROGRESS.MD's next action. Do not start by building the whole application. First inspect the destination repository and complete P0.1 in ROADMAP.MD.

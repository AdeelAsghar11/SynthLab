# SynthLab: Incremental Roadmap

Baseline: 2026-10-06. All implementation milestones are initially not started; actual status lives in PROGRESS.MD. Approximately six weeks at 8-10 hours/week is an illustrative schedule, not a delivery promise.

## Mandatory execution rules

One bounded development step at a time. A milestone is a scope boundary, not permission to implement every component at once. If a listed milestone is too large for a focused change, subdivide it into named steps before coding. Each completed step gets relevant documentation updates, appropriate verification, one focused commit, and a push. Do not implement the next step while the previous checkpoint remains unpushed without explicit user direction.

A phase is complete only when its gates are evidenced. Do not mark a milestone complete just because files exist. Maintain exact next action in PROGRESS.MD. User-requested reprioritization must update dependencies and scope.

## P0: Repository and minimal scaffold

| ID | Bounded milestone | Completion gate |
| --- | --- | --- |
| P0.1 | Inspect designated repo, agent guidance, status, branch, remote, and hardware facts | Existing user work preserved; repo/branch destination and unknowns recorded |
| P0.2 | Minimal backend health route, frontend starter, locked compatible environment | Both start locally; frontend can reach health route; no feature modules yet |
| P0.3 | Ignore rules, safe configuration example, minimal relevant CI/check scripts | Secrets, weights, databases, and job outputs excluded; available checks pass |

Do not create or publish a remote repository implicitly. If no remote is available, obtain the destination before a push; do not invent one.

## P1: Specification contracts

Depends on P0.

| ID | Bounded milestone | Completion gate |
| --- | --- | --- |
| P1.1 | Versioned specification envelope and initial field variants | Accepted/rejected fixtures prove types, unknown-key rejection, and limits |
| P1.2 | Probability/range/field-reference checks and structured diagnostics | Invalid sums, non-finite values, duplicate names, and inverted ranges rejected |
| P1.3 | Dependency graph and allow-listed rule contracts | Cycles/missing dependencies rejected; ordering deterministic; no executable rules |
| P1.4 | Default fictional support-ticket specification | Template validates; field generation ownership and null/date semantics clear |

Gate: The configuration contract is documented and can be validated without an LLM or UI.

## P2: Statistical generation

Depends on P1.

| ID | Bounded milestone | Completion gate |
| --- | --- | --- |
| P2.1 | Seeded categorical and boolean generators | Repeatability and category boundary tests pass |
| P2.2 | Fixed-proportion allocation and stable shuffling | Largest-remainder counts/tie-breaks verified for small and uneven sizes |
| P2.3 | Integer/decimal uniform and truncated-normal generators | Bounds, rounding, reproducibility, and repeated-seed statistics verified |
| P2.4 | Synthetic IDs and UTC creation dates | IDs unique; time-boundary behavior documented/tested |
| P2.5 | Conditional categories and derived resolution dates | Parent-child rules, null behavior, and ordering pass |
| P2.6 | Row/dataset validator and basic quality report | Every accepted structured row valid; impossible/unsupported rules fail clearly |

Gate: Statistical-only ticket datasets are reproducible under pinned conditions, validated, and reported. No model work until ownership of structured facts is sound.

## P3: Local text generation and safeguards

Depends on P2; each step remains separately reviewable.

| ID | Bounded milestone | Completion gate |
| --- | --- | --- |
| P3.1 | Text adapter contract, deterministic fake, and template adapter | Tests run without a downloaded model; text cannot overwrite structured fields |
| P3.2 | One real local runtime/model integration and compatibility spike | Exact revision/license/config recorded; 20-row preview measured; JSON parsing works |
| P3.3 | Input policy and sensitive-text recognizers | Artificial prohibited/benign cases measured; sensitive content omitted from logs |
| P3.4 | Output screening and two-retry limit | Same skeleton retained; timeout/exhaustion explicit; counters verified |
| P3.5 | Frozen text-consistency rubric and initial manual sample | Reviewer worksheet and observed limitations recorded, no invented scores |

Gate: Local model text can be generated and screened with bounded resource use. Model default remains provisional until enough benchmark evidence exists.

## P4: Jobs, persistence, and export

Depends on P3 for full text jobs; statistical job components can use the fake adapter during development.

| ID | Bounded milestone | Completion gate |
| --- | --- | --- |
| P4.1 | Single worker, bounded queue, status state machine | Requests non-blocking; duplicate worker avoided; row/token/time limits enforced |
| P4.2 | SQLite snapshots and artifact isolation/retention | Paths safe; restart interruption explicit; cleanup policy documented |
| P4.3 | Cancellation behavior and safe errors | Cancellation idempotent; checks between batches; no completed claim for shortfall |
| P4.4 | Completed-only CSV/JSON export and atomic finalization | Revalidated outputs; spreadsheet-safe mode; failures never yield normal full export |
| P4.5 | Generation manifest and API report/preview endpoints | Exact snapshots and known revisions recorded; unknown values labelled honestly |

Gate: End-to-end generation works via API, with reliable failures, cancellation, report, and provenance.

## P5: Frontend workspace

Depends on P1 contracts and P4 endpoints. UI work uses fixtures where endpoints are pending; never silently invent incompatible contracts.

| ID | Bounded milestone | Completion gate |
| --- | --- | --- |
| P5.1 | Workspace shell and template picker | Readable responsive layout; clear local model status |
| P5.2 | Field editor and supported generator controls | Typed configuration round-trips; field-specific errors displayed |
| P5.3 | Probability/constraint controls | Random/fixed modes clear; totals and unsupported rules explained |
| P5.4 | Preview submission and 20-row table | Sensitive output escaped; loading and validation failures understandable |
| P5.5 | Job progress and cancellation | Status transitions visible; cancellation/failure not shown as success |
| P5.6 | Report charts, saved specs, and download controls | Requested/observed proportions and numeric histogram accurate; completed-only exports |

Gate: Define -> Configure -> Preview -> Generate/export journey passes core Playwright checks. No implementation jargon or universal privacy claims in product copy.

## P6: Measured evaluation

Depends on stable generation and reporting. Evaluation scenarios can be frozen earlier.

| ID | Bounded milestone | Completion gate |
| --- | --- | --- |
| P6.1 | Frozen scenarios and three baseline runners | Same schema/row budgets; attempted vs accepted results separated |
| P6.2 | Repeated-seed statistics and model throughput comparison | Counts/distributions/latency/memory reported with environment and revisions |
| P6.3 | Stratified human consistency review and screening evaluation | Sample/rubric, precision/recall/false refusals, limits documented |
| P6.4 | Final model/default limit decision and report | Decisions supported by results; proposed targets marked achieved or unresolved |

Gate: Publish actual evidence comparing templates, whole-row LLM, and hybrid. Avoid claiming private-source fidelity or formal privacy from schema-driven fictional tests.

## P7: Release and portfolio

Depends on essential prior phase gates.

| ID | Bounded milestone | Completion gate |
| --- | --- | --- |
| P7.1 | Runtime-offline and failure/cleanup checks | Egress-disabled operation after setup; safe logging and retention verified |
| P7.2 | README, architecture, threat model, dataset card, licenses, examples | Documentation matches implementation; fictional artifacts only |
| P7.3 | Screenshots and two-minute demo | Show configuration, preview, report, and export without secrets |
| P7.4 | Reproduction and final release checkpoint | Fresh setup works; relevant checks pass; branch pushed and remote HEAD verified |

No public hosting required. Authentication and multi-tenancy must be designed before any later public deployment.

## Illustrative weekly grouping

- Week 1: P0 and P1.
- Week 2: P2.
- Week 3: P3.
- Week 4: P4 and early P5.
- Week 5: finish P5 and begin P6.
- Week 6: finish P6 and P7.

If milestones take longer, preserve quality and small checkpoints; revise the schedule instead of collapsing phases into a large unverified change.

## Deferred backlog

Multi-table generation; Parquet; Urdu/Roman Urdu; safe natural-language schema drafting with user review; authorized private-source ingestion; privacy accounting/differential privacy; model fine-tuning; downstream classifier utility studies; framework adapters; hosted multi-user deployment. Each needs a scope decision, architecture update, and its own incremental milestones before implementation.

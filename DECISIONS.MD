# SynthLab: Decision Log

Baseline: 2026-10-06. Status labels: Accepted baseline, Provisional, Superseded. Accepted baseline means selected for this plan, not implemented or benchmarked.

## Update rules

Append a numbered decision when a material choice changes behavior, scope, dependencies, security, contracts, or workflow. Include date, status, context, decision, why, alternatives, consequences, and evidence. Preserve earlier rationale; supersede rather than silently rewrite history. Update ARCHITECTURE.MD/PROJECT.MD/ROADMAP.MD as applicable and summarize implementation in PROGRESS.MD.

## D001: Focus on fictional support tickets

- Date/status: 2026-10-06, Accepted baseline.
- Decision: Build a single-table e-commerce support-ticket generator first.
- Why: Combines controlled categories, numeric/date rules, dependencies, and meaningful LLM text without customer identities.
- Alternative: Generic enterprise synthetic-data platform or private-data replication.
- Consequence: Support configurable supported schemas, but demonstrate one domain deeply; multi-table and private-source training are deferred.

## D002: Hybrid generation with Python ownership

- Status: Accepted baseline.
- Decision: Generate structured row skeletons in Python; LLM enriches approved text fields only.
- Why: Category frequencies, uniqueness, date ordering, and arithmetic are enforceable and measurable outside probabilistic text generation.
- Alternative: Ask an LLM to generate every complete row.
- Consequence: Separate sampling and text streams; compare whole-row LLM as an evaluation baseline. Temperature is not a probability-control mechanism.
- Evidence: RESEARCH.MD R01 describes a comparable hybrid architecture.

## D003: No personal identities or source-row uploads in MVP

- Status: Accepted baseline.
- Decision: Accept schema JSON; generate visibly synthetic operational data; reject personal identity/contact/credential fields and targeted real-person requests.
- Why: Narrows the product threat model and keeps course scope manageable.
- Alternative: Upload and replicate sensitive datasets.
- Consequence: Product restriction, not a claim that all fictional personal-style data is illegal. Source-data ingestion requires a later privacy design.

## D004: Declarative allow-listed rules

- Status: Accepted baseline.
- Decision: Typed generator variants and explicit operators; no execution of user/model code.
- Why: Supports validation, clear errors, reproducibility, and bounded security exposure.
- Alternative: eval, custom Python validators supplied by users, arbitrary SQL/code.
- Consequence: Unsupported constraints are rejected; arbitrary constraint solving is deferred.

## D005: Distinguish random sampling and fixed proportions

- Status: Accepted baseline.
- Decision: Offer seeded probabilistic draws and largest-remainder allocation as distinct modes.
- Why: Random probabilities describe a sampling process; exact quotas describe counts. Users must know the difference.
- Consequence: Preserve row category allocations during text retries. Conditional quotas apply within parent groups; contradictory global targets are rejected.

## D006: Local inference behind an adapter

- Status: Provisional runtime/model choice; Accepted local-only boundary.
- Decision: Start with Ollama integration, plus fake/template adapters. Benchmark Qwen3.5-4B and 9B; retain Qwen3-4B-Instruct-2507 as a text-only baseline.
- Why: Local workflow avoids paid inference dependencies; adapter keeps runtime replaceable.
- Alternatives: Direct Transformers, vLLM, cloud inference.
- Consequence: Verify exact version compatibility, structured output, licensing, memory, and task quality before selecting the default. No cloud fallback.

## D007: React and FastAPI

- Status: Accepted baseline; exact dependency versions unselected.
- Decision: React/TypeScript/Vite UI and Python FastAPI backend; Tailwind/shadcn for UI; NumPy/SciPy/pandas for generation/reporting.
- Why: Python fits sampling and local inference; React supports a portfolio-quality configuration workspace.
- Alternative: Streamlit-only implementation.
- Consequence: Two development environments, requiring locked versions and explicit API contracts.

## D008: Single local worker and SQLite

- Status: Accepted baseline; worker launch mechanism provisional.
- Decision: One active job, bounded queue, SQLite metadata, isolated local artifacts, polling status.
- Why: Sufficient for a local single-user MVP with visible progress and cancellation.
- Alternative: Redis/Celery, distributed workers, streaming event infrastructure.
- Consequence: No public multi-user deployment. Restarted jobs fail explicitly; automatic resume is deferred. Avoid duplicate workers in reload mode.

## D009: Layered screening with honest limits

- Status: Accepted baseline.
- Decision: Presidio plus custom recognizers, prompt restrictions, local execution, safe logs, and output screening.
- Why: Different controls address different risks; detector recall alone cannot establish privacy.
- Consequence: Document coverage gaps, false positives, and false negatives. Avoid blanket privacy/legal claims or unsupported differential-privacy labels.
- Evidence: RESEARCH.MD R06 and R09.

## D010: Bounded retries and explicit failed jobs

- Status: Accepted baseline.
- Decision: Initial text attempt plus at most two retries per row. Keep structured facts fixed. Exhaustion fails the job; normal exports require full completion.
- Why: Predictable resource use and no hidden count/proportion changes.
- Alternative: Unlimited retries, silently dropping rows, changing categories.
- Consequence: Failure reasons must be actionable. Report rejected attempts separately from final rejected rows. Future partial-export support requires explicit design.

## D011: Evaluation against three baselines

- Status: Accepted baseline; thresholds are proposed.
- Decision: Compare template text, whole-row LLM, and hybrid generation on frozen scenarios, across seeds where relevant.
- Why: Demonstrates the effect of engineering controls with measurable tradeoffs.
- Consequence: Report hard-rule pass rates, distributions, consistency, diversity, latency, and memory. Human review supplements automation; publish actual results only.

## D012: Own a small engine first

- Status: Accepted baseline.
- Decision: Use straightforward Python components rather than build the initial product around SDV or a broad orchestration framework.
- Why: Learn the mechanics, keep contracts understandable, and avoid unnecessary licensing/scope complications.
- Alternative: Wrap Data Designer, MOSTLY AI, or SDV immediately.
- Consequence: Cite prior tools and avoid novelty claims. Later compare Data Designer or add an adapter if evidence supports it. SDV's Business Source License requires specific review before service use.

## D013: Incremental context and git workflow

- Status: Accepted user requirement.
- Decision: One bounded development step at a time; update relevant context documents; verify; commit; push the authorized branch after every completed step.
- Why: Maintains reviewability and long-term agent continuity.
- Consequence: Do not accumulate multiple milestones into one large change. A push failure leaves the step committed but unsynchronized; record the blocker and resolve it before further development. Never force-push, invent a remote, or stage unrelated work.
- Evidence: Explicit user request on 2026-10-06.

## D014: Reproducibility through manifests

- Status: Accepted baseline.
- Decision: Save specification, seed, code/model/prompt/runtime revisions, settings, and environment metadata with outputs.
- Why: Seed alone cannot reproduce changing model or package behavior.
- Consequence: Promise reproducible statistical generation under pinned conditions; qualify exact LLM-text reproducibility across runtimes/devices.

## Decision template

### D0XX: Short descriptive title

- Date/status:
- Context:
- Decision:
- Why:
- Alternatives considered:
- Consequences and risks:
- Evidence/related milestone:
- Supersedes or superseded by:

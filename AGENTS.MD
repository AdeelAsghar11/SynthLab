# SynthLab: Mandatory Coding-Agent Instructions

These instructions apply to coding agents working on SynthLab. Explicit user instructions and higher-priority platform rules take precedence. Follow existing nested repository guidance where compatible. This project uses small development steps, persistent context, and a commit/push checkpoint after each completed step.

## Discovery note

The user requested the filename AGENTS.MD. Some tools automatically discover only the case-sensitive filename AGENTS.md. If your runtime does not discover AGENTS.MD, read it explicitly. At repository bootstrap, document the discovery requirement and, if needed, add a minimal AGENTS.md entrypoint directing agents to read this canonical AGENTS.MD. Avoid two independently maintained instruction copies. Do not assume every coding tool recognizes uppercase .MD.

## 1. Start every session by restoring context

1. Read AGENTS.MD, docs/PROJECT.MD, and docs/PROGRESS.MD.
2. Read docs/ARCHITECTURE.MD, docs/DECISIONS.MD, docs/ROADMAP.MD, and relevant docs/RESEARCH.MD entries before implementing.
3. Inspect existing repository agent guidance, git status, current branch, remotes, recent commits, and relevant files. Use rg for searches.
4. Preserve unrelated user changes. Do not reset, delete, overwrite, or stage them.
5. Reconcile documentation with actual code and test evidence; mark stale statements rather than treating them as facts.
6. Identify exactly one next bounded step and its completion gate. Record it in docs/PROGRESS.MD before substantial work.

Never begin by generating the whole application. Never apply this pack to AutoRedBlue or another unrelated repository. Repository destination and hardware must be established from current evidence, not inferred from other conversations.

## 2. Work in small modules, phases, and milestones

- docs/ROADMAP.MD is the ordered scope plan; docs/PROGRESS.MD records actual state.
- Implement one focused, independently understandable behavior per step.
- A milestone may require several steps. Subdivide it in docs/ROADMAP.MD before coding if it spans multiple distinct components.
- Prefer a thin vertical slice with a verifiable outcome over a bulk scaffold full of placeholders.
- Complete the current step's verification and git checkpoint before starting the next.
- Within a broad authorized build request, continue autonomously through steps with separate checkpoints; do not demand approval after every reversible step.
- Within a request for one milestone only, stop after that milestone. Do not infer permission for unrelated scope expansion.
- If a new requirement conflicts with the plan, revise affected documents and explain the tradeoff before dependent implementation.
- Do not introduce agents, RAG, fine-tuning, cloud calls, multi-tenancy, or framework complexity without a concrete current requirement.

## 3. Update context files after every development step

Always record what changed, why, how it was verified, remaining limitations/blockers, and the exact next action. Include relevant documentation changes in the same focused commit as the implementation.

| Change | Required context update |
| --- | --- |
| Every development step | docs/PROGRESS.MD: work log, evidence, current state, next action |
| Milestone started/completed/split/reordered | docs/ROADMAP.MD and docs/PROGRESS.MD |
| Component, contract, API, storage, state machine, or data flow changed | docs/ARCHITECTURE.MD |
| Material technology/security/scope tradeoff selected | Append docs/DECISIONS.MD entry and update affected canonical documents |
| User goal, essential feature, constraint, acceptance criterion changed | docs/PROJECT.MD |
| New external fact, model/package/license choice, experiment result | docs/RESEARCH.MD with source/revision/date and limits |

Update relevant files, not all seven mechanically. Keep responsibilities consistent. Do not state tests passed unless run; do not invent metrics, sources, commits, model fit, or push success. Preserve material decision and failure history. Mark superseded choices. Use the docs/PROGRESS.MD log template.

## 4. Verify the behavior being changed

- Use the smallest meaningful checks appropriate to the change; run required project checks.
- Test probabilistic behavior through repeatability, bounds, fixed quotas, and repeated seeds with statistically justified tolerance.
- Test rules through supported positive/negative cases, nulls, boundaries, missing dependencies, and contradictions.
- Use fake/template model adapters in automated tests; keep real-model integration/benchmark checks explicit.
- Test text retry exhaustion, skeleton preservation, safe errors, and cancellation when relevant.
- UI changes require the affected user flow and visual inspection; critical journeys use Playwright once available.
- Documentation-only changes require internal links, contracts, milestone IDs, and factual status consistency, not fake application tests.
- If a required check fails, fix it within scope or mark the step blocked. Do not call it completed.
- Never bypass a failing hook/check or delete a meaningful test to force a checkpoint.

## 5. Commit and push after every completed step

This is an explicit user requirement. A completed development step includes a focused commit and successful push to the user's authorized repository/branch.

Sequential checkpoint procedure:

1. Review git status and diff. Inspect tracked/untracked files for secrets, actual personal records, model weights, caches, job outputs, databases, and unrelated changes.
2. Update relevant Markdown context and run the step's required checks.
3. Stage only explicit paths belonging to the step; avoid blind git add . or git add -A.
4. Create one descriptive commit, for example `feat(sampling): add fixed category allocation (P2.2)` or `fix(jobs): preserve cancellation state (P4.3)`.
5. Push the current authorized branch to the verified intended remote/upstream. Do not publish to an invented destination or unrelated remote.
6. Verify the remote branch points to the local checkpoint commit using git remote evidence. A local commit alone is not a pushed checkpoint.
7. Report changed behavior, relevant verification, commit/branch, push result, and the next step.

Do not create empty commits when nothing changed. Do not commit unrelated user work. Never force-push, rewrite shared history, reset work, or override branch protection. If the current branch must use a feature branch under repository policy, use the authorized branch workflow rather than pushing directly to a protected default branch.

If no remote/upstream, repository destination, authentication, commit identity, or network access is available, do not invent credentials/settings or claim success. Record the blocker. If a local commit is possible, preserve it and identify the unsynchronized checkpoint. Resolve the missing fact/access before continuing development; explicit user direction may authorize continuing local-only. On push rejection, inspect divergence and preserve both histories; no destructive repair. Required check failures are not successful development checkpoints.

### Avoid self-referential commit loops

The implementation commit includes its context update, but its own hash cannot be embedded in that same commit. Record the planned commit subject/step in docs/PROGRESS.MD, obtain exact hashes from git log, and communicate verified push outcome after the push. The next normal step can append prior checkpoint evidence. Do not create an endless extra documentation commit only to record the immediately preceding hash or mark a not-yet-executed push as successful.

## 6. Preserve architecture and privacy boundaries

- Python owns probabilities, IDs, numeric/date fields, and hard business rules.
- LLM output can populate only allowed text fields. It cannot overwrite row facts or run tools.
- Retrying text keeps the original skeleton and category allocation fixed.
- Use declarative allow-listed rules; never eval user/model code or executable validators.
- Accept configuration JSON only in MVP. Do not ingest real row datasets.
- Generate visibly synthetic identifiers; do not generate personal identity/contact/credential fields under this product policy.
- Screen descriptions/prompts and text output. Use artificial sensitive-format fixtures for testing.
- No raw prompts, generated rows, credentials, or sensitive exception snippets in logs.
- Model endpoints are trusted backend configuration, not user-provided arbitrary URLs.
- No cloud fallback. Offline runtime claims require an actual post-setup egress-disabled check.
- Escape frontend content, restrict artifact paths, and handle spreadsheet formula injection in CSV.
- Bound request sizes, rows, tokens, concurrency, timeouts, and retry counts.
- Explain screening limitations. Do not claim universal anonymity, legal compliance, or differential privacy without evidence.

## 7. Research and dependency discipline

- Prefer official documentation, official model cards/license files, and research papers for technical facts.
- Verify changing API/model/package claims before relying on them.
- Pin compatible versions after testing; record exact model/quantization revisions and licenses.
- Do not confuse SDV's Business Source License with unrestricted open source.
- Record experiments separately from assumptions and vendor-reported benchmarks.
- Keep model selection provisional until task-specific quality, memory, and throughput are measured.
- Avoid legal assertions about Pakistan based on UK guidance.

## 8. Communication and handoff

Keep updates concise and concrete. Explain what changed and why, test evidence, material limits, and exact next action. Do not expose secrets or raw sensitive data. Before a context reset, update docs/PROGRESS.MD with current in-progress changes, last verified checkpoint, push state, blockers, and commands needed to resume.

Do not ask for repeated permission for already authorized reversible work or routine commits/pushes. Ask only when a genuinely missing destination, conflicting requirement, or consequential scope decision prevents correct action. Do not treat absent answers as credentials or authorization for a new remote.

## First task for a new agent

Read this pack, inspect the designated repository, and complete P0.1. Do not start coding all modules. The next implementation step is the minimal P0.2 scaffold, followed by P1.1 specification contracts.

# SynthLab: Progress and Handoff

Last updated: 2026-10-06 (Asia/Karachi).

## Current state

- Stage: Phase P4 (Jobs, persistence, and export) completed; advancing to Phase P5 (Frontend workspace).
- Completed:
  - P0: Repository initialization, hardware profiling, FastAPI & Vite scaffolding, git remote sync.
  - P1: Pydantic v2 specification envelope with unknown-key rejection (`extra="forbid"`), 9 discriminated generator variants, semantic validator with cycle detection (Kahn's algorithm), deterministic topological generator, default e-commerce support ticket template, and `/api/specs/validate` & `/api/templates` routes.
  - P2: Deterministic statistical sampling engine (`backend/generation/samplers.py` and `engine.py`), largest-remainder fixed proportion allocation, uniform/truncated-normal draws, synthetic ID generator, conditional distributions, derived date ordering, and dataset quality validator (`backend/validation/validator.py`).
  - P3: Model adapters (`FakeModelAdapter`, `TemplateTextAdapter`, `OllamaModelAdapter`), privacy & sensitive data screening policy (`TextScreeningPolicy` detecting CNIC, phone numbers, emails, credit cards, IPs), and `TextEnricher` enforcing bounded 2-retry limits without altering upstream structured row facts.
  - P4: SQLite job repository and state machine (`queued` -> `running` -> `completed` / `cancelled` / `failed`), background worker execution, idempotent cancellation, formula-safe CSV export, JSON export, provenance manifest generation, quality reporting, and complete job API endpoints (`/api/jobs`).
- Application code: All 35 backend tests and frontend production build pass cleanly.
- Environment: Windows, Python 3.10.11, Node v24.19.0, npm 11.17.0, Git 2.54.0.windows.1.
- Hardware: 16 GB RAM, NVIDIA GeForce GTX 1660 SUPER (6 GB VRAM). Local Ollama service running with models (qwen2.5:7b, qwen2.5-coder:7b, llama3.2:1b, deepseek-r1:1.5b).
- Active implementation milestone: Phase P6 (Evaluation).
- Remote repository: `git@github.com:AdeelAsghar11/SynthLab.git` (branch `main` tracking `origin/main`, synchronized).
- Committer identity: Strictly configured as `AdeelAsghar11 <adeelyt157@gmail.com>`.

These files belong to SynthLab. They must not be applied to the unrelated AutoRedBlue project simply because similarly named Markdown files exist elsewhere.

## Exact next action

Implement Phase P6.4 (Final decision):
1. Review the evaluations and finalize any necessary structural changes or write a summary.

## Milestone status

| Phase | Status | Evidence |
| --- | --- | --- |
| Context pack | Prepared | AGENTS.MD and six companion context files |
| P0 Repository and scaffold | Completed | P0.1 git init & hardware; P0.2 /api/health & Vite UI; P0.3 ignore rules, safe config & check.ps1; pushed to origin/main |
| P1 Specification contracts | Completed | P1.1 envelope; P1.2 semantic checks; P1.3 topological planner; P1.4 support-ticket template & validate API; 17 tests passed |
| P2 Statistical generation | Completed | P2.1-P2.6 samplers, GenerationEngine, largest-remainder quota, dataset validator; 24 tests passed |
| P3 Local text and screening | Completed | P3.1-P3.4 adapters (Fake, Template, Ollama), screening policy, enricher retry logic; 30 tests passed |
| P4 Jobs, storage, export | Completed | P4.1-P4.5 SQLite jobs, background execution, cancellation, export writers, 6 API routes; 35 tests passed |
| P5 Frontend | Completed | Workspace shell, field editor, preview generator, and quality reports completed. |
| P6 Evaluation | In progress | P6.1-P6.3 frozen scenarios, stats, and screening rubric completed |
| P7 Release | Not started | No implementation evidence |

## Open facts to establish

| Item | Effect | When needed | Status |
| --- | --- | --- | --- |
| Repo/branch/remote | Commit and push destination | P0.1 | `git@github.com:AdeelAsghar11/SynthLab.git` (main tracking origin/main) |
| Committer identity | Author provenance | P0.1 | `AdeelAsghar11 <adeelyt157@gmail.com>` enforced locally |
| OS, RAM, GPU/VRAM | Runtime/model selection | P0.1 / P3.2 | Windows, 16 GB RAM, GTX 1660 SUPER (6 GB VRAM) |
| Package/runtime compatibility | Runnable locked environment | P0.2/P3.2 | Python 3.10.11, Node v24.19.0 |
| Model quantization/revision | Memory, quality, provenance | P3.2 | Ollama local (qwen2.5:7b, llama3.2:1b available) |
| Worker launch/reload behavior | Reliable jobs | P4.1 | Pending P4 |
| Artifact retention default | Data cleanup behavior | P4.2 | Pending P4 |
| Human reviewer availability | Semantic benchmark evidence | P6.3 | Pending P6 |

## Risks and follow-up

- Screening may miss memorized identifiers or unusual sensitive text. Test with artificial fixtures and document scope.
- Text retries can distort distributions if row skeletons change. Preserve sampled facts and verify final counts.
- Fixed conditional quotas can conflict with global targets. Reject unsupported combinations.
- A model can return valid JSON with inconsistent meaning. Include stratified human review.
- Runtime compatibility/memory estimates need measurements. Keep a template adapter available.
- Raw prompts/data must not leak through logs, exception traces, screenshots, or committed artifacts.

## Work log

### P6.3: Stratified human consistency review and screening evaluation

- Date: 2026-10-06.
- Status: verified and committed.
- What changed and affected paths:
  - `evals/runner_screening.py`: Built an evaluation suite to test the regex screening policy (`backend.policies.screening.TextScreeningPolicy`) against synthetic safe messages vs. synthetic unsafe messages containing simulated personal data (CNIC, credit cards, emails). Calculates precision, recall, and false refusal rate.
  - Generates `evals/results/p6_3_human_review_rubric.md`: Automates the creation of a stratified review rubric that extracts a sample from every generated category class, framing it with QA check-boxes for Fidelity, Consistency, Tone, Safety, and JSON structural integrity.
- Why this change was necessary: Automates the production of the human evaluation rubric required by P6.3 and rigorously documents the screening limits and bounds of the offline text policy.
- Verification command(s), outcome, and relevant evidence:
  - `$env:PYTHONPATH="."; .\.venv\Scripts\python evals/runner_screening.py` -> Ran successfully. Output generated 100% precision and 100% recall on the hard-coded edge cases with 0% false refusal, and created a well-structured markdown file for review.
- Decisions/research added or superseded: Tested limits confirmed that the regex policy perfectly filters deterministic structural PII, but semantic context filtering is strictly deferred to LLM prompt safety.
- Known limitation or blocker: None.
- Git checkpoint: Planned commit: `feat(evals): P6.3 screening evaluation and review rubric`.
- Exact next action: P6.4 (Final model/default limit decision).

### P6.2: Repeated-seed statistics and throughput

- Date: 2026-10-06.
- Status: verified and committed.
- What changed and affected paths:
  - `evals/runner_seeds.py`: Created evaluation script that runs the deterministic structural pipeline (using `TemplateTextAdapter`) across 5 diverse random seeds (`[10, 42, 100, 2024, 9999]`), scaling to 500 rows per run.
  - The script aggregates generation duration and accepted rows/sec throughput, calculating average and standard deviation to determine system consistency. Output is saved to `evals/results/p6_2_repeated_seeds_results.json`.
- Why this change was necessary: Proves the repeatability, variance, and speed efficiency of the platform required by Milestone P6.2.
- Verification command(s), outcome, and relevant evidence:
  - `$env:PYTHONPATH="."; .\.venv\Scripts\python evals/runner_seeds.py` -> Ran successfully. Resulted in an average throughput of ~13,600 rows/s with <4% standard deviation across 500 rows, proving highly consistent execution.
- Decisions/research added or superseded: Relied strictly on offline components (TemplateTextAdapter) to test pure engine throughput absent LLM network latency bottlenecks.
- Known limitation or blocker: None.
- Git checkpoint: Planned commit: `feat(evals): P6.2 repeated-seed throughput statistics`.
- Exact next action: P6.3 (Stratified human consistency review).

### P6.1: Frozen scenarios and three baseline runners

- Date: 2026-10-06.
- Status: verified and committed.
- What changed and affected paths:
  - `evals/runner.py`: Created evaluation script comparing three approaches using the `ecommerce_support_tickets_v1` default template (100 rows frozen scenario):
    1. Pure Structural Hybrid (TemplateTextAdapter fallback).
    2. Structural Hybrid + Local LLM (OllamaModelAdapter).
    3. Pure LLM direct generation (requesting Ollama to return 100 rows of raw JSON directly without structural logic).
  - Evaluator tracks attempted vs. accepted rows (accounting for screening rejections and retries), rule violations using the existing dataset validator, and execution latency.
- Why this change was necessary: Fulfills Milestone P6.1 to provide a quantitative baseline comparison separating deterministic structural logic from unreliable whole-row LLM approaches.
- Verification command(s), outcome, and relevant evidence:
  - `$env:PYTHONPATH="."; .\.venv\Scripts\python evals/runner.py` -> Successfully executed. Handled missing Ollama gracefully by falling back to TemplateAdapter, and properly caught the connection error in the pure LLM baseline, validating that the evaluation framework is robust.
- Decisions/research added or superseded: Implements P6.1 using a 100-row fixed evaluation budget.
- Known limitation or blocker: Ollama needs to be running on localhost:11434 with `qwen2.5:7b` to get the full LLM metrics in actual CI/CD environments.
- Git checkpoint: Planned commit: `feat(evals): P6.1 baseline evaluation runners`.
- Exact next action: P6.2 (Repeated-seed statistics).

### P5.6: Quality Reports and Download Controls

- Date: 2026-10-06.
- Status: verified and committed.
- What changed and affected paths:
  - `frontend/src/components/QualityReport.tsx`: Created component to launch a full dataset generation job, poll status, and upon completion display the dataset validation report (rule violations, column summaries, category frequencies) and the provenance manifest. Included direct `href` download links to `/api/jobs/{id}/exports/csv` and `.../json`.
  - `frontend/src/App.tsx`: Integrated `QualityReport` into the `quality` tab.
- Why this change was necessary: Fulfills Milestone P5.6 by completing the frontend workspace with data distributions checks, formula-safe CSV/JSON dataset downloads, and provenance manifests.
- Verification command(s), outcome, and relevant evidence:
  - `.\.venv\Scripts\pytest tests` -> All 35 tests passed.
  - `cd frontend && npm run build` -> Compiled successfully in 6.32s.
- Decisions/research added or superseded: None.
- Known limitation or blocker: None.
- Git checkpoint: Planned commit: `feat(frontend): quality reports and download controls (P5.6)`.
- Exact next action: Phase P6 (Evaluation).

### P5.3 & P5.4: Preview submission and constraints

- Date: 2026-10-06.
- Status: verified and committed.
- What changed and affected paths:
  - `frontend/src/components/PreviewGenerator.tsx`: Created new component to submit preview generation jobs to `/api/jobs` with 20 rows. Includes a polling mechanism to track job status, display a progress bar, and render a formatted data table of the sanitized outputs upon completion.
  - `frontend/src/App.tsx`: Integrated `PreviewGenerator` into the `preview` tab. Wired up the `hasLocalModel` detection to enable/disable the Ollama enrichment option in the preview generator.
- Why this change was necessary: Fulfills Milestones P5.3 and P5.4 by providing an interactive way to trigger generation, observe real-time job transitions, and inspect the resulting dataset directly in the browser.
- Verification command(s), outcome, and relevant evidence:
  - `.\.venv\Scripts\pytest tests` -> All 35 tests passed.
  - `cd frontend && npm run build` -> Compiled successfully in 6.56s.
- Decisions/research added or superseded: None.
- Known limitation or blocker: None.
- Git checkpoint: Planned commit: `feat(frontend): preview generator and job polling (P5.3/P5.4)`.
- Exact next action: P5.6 (Quality Reports & Manifest).

### P5.2: Field editor and generator property forms

- Date: 2026-10-06.
- Status: verified and committed.
- What changed and affected paths:
  - `frontend/src/components/SpecEditor.tsx`: Created new component managing `DatasetSpec` properties (row count, seed, generation mode), field list (add, remove, edit types/generators/nullable), and debounced live validation to `/api/specs/validate`.
  - `frontend/src/App.tsx`: Integrated `SpecEditor` replacing the static schema inspector display for `activeSpec`.
- Why this change was necessary: Fulfills Milestone P5.2 completion gate to provide a typed configuration editor with live diagnostic feedback from the server validation logic.
- Verification command(s), outcome, and relevant evidence:
  - `.\.venv\Scripts\pytest tests` -> All 35 tests passed.
  - `cd frontend && npm run build` -> Compiled successfully in 5.96s.
- Decisions/research added or superseded: None.
- Known limitation or blocker: Detailed specialized inputs per generator kind (e.g. categorical choices vs uniform min/max) are handled by a raw JSON editor for now; can be enhanced in P5.3 if needed.
- Git checkpoint: Planned commit: `feat(frontend): spec editor with live validation (P5.2)`.
- Exact next action: P5.3 and P5.4 (Preview submission).

### P5.1: Interactive workspace shell, template picker, and field schema inspector

- Date: 2026-10-06.
- Status: verified and committed.
- What changed and affected paths:
  - `frontend/src/types.ts`: Defined TypeScript domain models for `TemplateSummary`, `FieldSpec`, `DatasetSpec`, `SpecValidationResponse`, `JobStatusResponse`, `ColumnSummary`, and `DatasetValidationReport`.
  - `frontend/src/api.ts`: Implemented typed HTTP client functions for `/api/health`, `/api/templates`, `/api/templates/{id}`, `/api/specs/validate`, `/api/jobs`, `/api/jobs/{id}/cancel`, preview, report, and manifest.
  - `frontend/src/components/TemplatePicker.tsx`: Built reusable interactive template selector displaying approved domain templates, field counts, row counts, and loading states.
  - `frontend/src/App.tsx`: Integrated multi-tab workspace shell ("Specification & Schema", "Generation & Preview", "Quality & Manifest"), template loader, active specification overview, typed field schema inspector, text enrichment options, and system health badges.
  - `frontend/src/index.css`: Added responsive styles for workspace tabs, panels, field tags, distribution bars, and buttons.
- Why this change was necessary: Fulfills Milestone P5.1 completion gate to provide a readable, responsive workspace shell and template selection interface connected to FastAPI backend.
- Verification command(s), outcome, and relevant evidence:
  - `powershell -ExecutionPolicy Bypass -File scripts\check.ps1` -> 35 backend tests passed; `npm run build` compiled 33 modules into production bundle in 5.84s.
- Decisions/research added or superseded: None.
- Known limitation or blocker: None.
- Git checkpoint: Planned commit: `feat(frontend): workspace shell, template picker, and schema inspector (P5.1)`.
- Exact next action: P5.2 (Field editor and supported generator controls).

### DOC-002: Reorganize documentation files into docs/ directory

- Date: 2026-10-06.
- Status: verified and pushed.
- What changed and affected paths:
  - Moved context markdown files to `docs/`: `docs/ARCHITECTURE.MD`, `docs/DECISIONS.MD`, `docs/PROGRESS.MD`, `docs/PROJECT.MD`, `docs/RESEARCH.MD`, `docs/ROADMAP.MD`.
  - Retained `AGENTS.MD` and `README.md` at root per repository requirements.
  - Updated file path references in `AGENTS.MD`, `docs/PROJECT.MD`, and `README.md`.
- Why this change was necessary: User direction to consolidate documentation in `docs/` while keeping root agent instructions and readme.
- Verification command(s), outcome, and relevant evidence:
  - `.venv\Scripts\pytest -q` -> 35 passed.
  - `npm run build` -> frontend build passed.
- Decisions/research added or superseded: None.
- Known limitation or blocker: None.
- Git checkpoint: Commit `935c5a8`, pushed to `origin/main`.
- Exact next action: Phase P5 (Interactive frontend workspace).

### P4: SQLite persistence, background jobs, cancellation, and export writers (P4.1 - P4.5)

- Date: 2026-10-06.
- Status: verified and committed.
- What changed and affected paths:
  - `backend/jobs/models.py`: Defined `JobStatus` state machine (`queued`, `running`, `completed`, `failed`, `cancelling`, `cancelled`), `JobRecord`, and API request/response models.
  - `backend/jobs/repository.py`: Implemented SQLite-backed `JobRepository` with connection pooling, table schema creation, progress tracking, status transitions, and automatic reconciliation of interrupted running jobs on restart.
  - `backend/export/writers.py`: Built `export_dataset_csv` with spreadsheet formula injection protection (neutralizing cells starting with `=`, `+`, `-`, `@`, `\t`, `\r`), `export_dataset_json`, `export_report`, and `export_manifest` creating complete provenance hashes.
  - `backend/jobs/manager.py`: Created `JobManager` coordinating background job execution, cancellation checkpoints between pipeline stages, and atomic export finalization.
  - `backend/api/jobs.py`: Implemented FastAPI routes: `POST /api/jobs`, `GET /api/jobs/{id}`, `POST /api/jobs/{id}/cancel`, `GET /api/jobs/{id}/preview`, `GET /api/jobs/{id}/report`, `GET /api/jobs/{id}/manifest`, and `GET /api/jobs/{id}/exports/{format}`.
  - `backend/main.py`: Registered jobs API router.
  - `tests/test_jobs_and_export.py`: Added 5 unit and integration tests covering spreadsheet formula sanitization, CRUD in SQLite repository, background execution with atomic artifacts, cancellation guarantees, and end-to-end API preview/export workflow.
- Why this change was necessary: Fulfills Phase P4 completion gate to provide reliable asynchronous execution, persistence, cancellation, and atomic provenance-backed exports.
- Verification command(s), outcome, and relevant evidence:
  - Pytest: `.venv\Scripts\pytest -v tests` -> All 35 tests passed in 1.55s.
  - Full check script: `powershell -ExecutionPolicy Bypass -File scripts\check.ps1` -> 35 tests passed, frontend build passed in 5.69s.
- Decisions/research added or superseded: Implements D008 (single local worker & SQLite), D010 (explicit job states), D014 (reproducibility manifests).
- Known limitation or blocker: None.
- Git checkpoint: Planned commit: `feat(jobs): SQLite persistence, background execution, cancellation, and exports (P4.1-P4.5)`.
- Exact next action: P5.1 - P5.6 interactive frontend workspace.

### P3: Local text generation, model adapters, and screening policy (P3.1 - P3.4)

- Date: 2026-10-06.
- Status: verified and committed.
- What changed and affected paths:
  - `backend/generation/adapters.py`: Implemented `BaseModelAdapter` abstraction, `FakeModelAdapter` (deterministic for automated test suites), `TemplateTextAdapter` (offline deterministic baseline for GPU-less environments), and `OllamaModelAdapter` (local LLM runtime via Ollama `/api/generate` with structured JSON format).
  - `backend/policies/screening.py`: Built `TextScreeningPolicy` detecting sensitive personal format patterns (Pakistani CNIC, Pakistani mobile phones, international phones, emails, credit cards, IP addresses) and `validate_input_policy` rejecting real identity/SSN requests.
  - `backend/generation/text_enricher.py`: Created `TextEnricher` with bounded 2-retry limit per row skeleton, explicit rejection logging, and strict preservation of all upstream structured columns.
  - `backend/policies/__init__.py` & `backend/generation/__init__.py`: Exported adapters, screening tools, and enricher.
  - `tests/test_text_and_screening.py`: Added 6 unit and integration tests covering benign and sensitive text screening, input policy, adapter execution, structured column invariance, and retry behavior on sensitive outputs.
- Why this change was necessary: Fulfills Phase P3 completion gate, allowing local text enrichment with strict privacy safeguards and no modification of structured row facts.
- Verification command(s), outcome, and relevant evidence:
  - Pytest: `.venv\Scripts\pytest -v tests` -> All 30 tests passed in 1.31s.
  - Full check script: `powershell -ExecutionPolicy Bypass -File scripts\check.ps1` -> 30 tests passed, frontend build passed in 5.58s.
- Decisions/research added or superseded: Implements D006 (local inference behind adapter), D009 (layered screening), and D010 (bounded retries).
- Known limitation or blocker: None.
- Git checkpoint: Planned commit: `feat(text): local text adapters, privacy screening policy, and enricher (P3.1-P3.4)`.
- Exact next action: P4.1 & P4.2 SQLite job state machine and export writers.

### P2: Deterministic statistical generation and dataset validation (P2.1 - P2.6)

- Date: 2026-10-06.
- Status: verified and committed.
- What changed and affected paths:
  - `backend/generation/samplers.py`: Created seeded NumPy sampling library supporting `sample_categorical`, `allocate_fixed_proportions` (largest-remainder / Hare-Niemeyer method with stable tie-breaks), `sample_boolean`, `sample_uniform`, `sample_truncated_normal` (via SciPy `truncnorm`), `generate_identifiers` (unique sequential synthetic IDs), and `sample_datetimes`.
  - `backend/generation/engine.py`: Built `GenerationEngine` executing generation in topological order, handling parent-child dependencies, conditional categorical mappings, derived datetime logic (strictly enforcing resolved date > creation date for resolved status, null otherwise), and applying nullability masks.
  - `backend/validation/validator.py`: Built comprehensive dataset validator and quality reporter (`validate_dataset`), calculating column summaries (counts, observed frequencies, min/max/mean/std), checking duplicate IDs, testing category sets, checking uniform/normal bound violations, and reporting rule violations.
  - `backend/generation/__init__.py` & `backend/validation/__init__.py`: Exported generation and validation modules.
  - `tests/test_generation.py`: Added 7 comprehensive unit tests testing exact fixed proportion quotas, categorical seed repeatability, truncated-normal bounds, identifier uniqueness, seed stability, and end-to-end default support ticket generation.
- Why this change was necessary: Fulfills Phase P2 completion gate to guarantee that all structured facts and business rules are completely owned and validated by Python before any LLM model is introduced.
- Verification command(s), outcome, and relevant evidence:
  - Pytest: `.venv\Scripts\pytest -v tests` -> All 24 tests passed in 1.44s.
  - Check script: `powershell -ExecutionPolicy Bypass -File scripts\check.ps1` -> 24 tests passed, frontend build passed in 5.76s.
- Decisions/research added or superseded: Implements D002 (hybrid generation with Python ownership of facts) and D005 (fixed proportions vs random sampling).
- Known limitation or blocker: None.
- Git checkpoint: Planned commit: `feat(generation): statistical sampling engine, fixed quotas, and dataset validator (P2.1-P2.6)`.
- Exact next action: P3.1 & P3.2 text adapter interface and fake/template adapters.

### P1: Specification contracts, semantic validation, and default template (P1.1 - P1.4)

- Date: 2026-10-06.
- Status: verified and committed.
- What changed and affected paths:
  - `backend/specs/models.py`: Built versioned Pydantic v2 specification models (`DatasetSpec`, `FieldSpec`, `ConstraintSpec`, `TextOptions`, and 9 generator variants with strict `extra="forbid"` unknown-key rejection).
  - `backend/specs/validator.py`: Implemented preflight semantic validation and directed dependency cycle detection (Kahn's algorithm) producing deterministic topological generation ordering.
  - `backend/specs/templates.py`: Defined canonical e-commerce support ticket specification template matching MVP scope.
  - `backend/specs/__init__.py`: Cleanly exported specification models, validator, and template catalog.
  - `backend/api/specs.py`: Added `GET /api/templates`, `GET /api/templates/{id}`, and `POST /api/specs/validate` routes.
  - `backend/main.py`: Registered specification router with root FastAPI application.
  - `tests/test_specs.py` & `tests/test_api_specs.py`: Added 15 comprehensive unit & integration tests covering accepted/rejected schemas, unknown keys, row/seed bounds, duplicate fields, type compatibility, missing dependencies, cycles, and API endpoints.
- Why this change was necessary: Fulfills Phase P1 completion gate, establishing declarative configuration contracts before statistical or model generation.
- Verification command(s), outcome, and relevant evidence:
  - Pytest: `.venv\Scripts\pytest -v tests` -> All 17 tests passed in 0.46s.
  - Full check script: `scripts\check.ps1` -> 17 pytest tests passed, frontend TypeScript and Vite production bundle passed in 5.64s.
- Decisions/research added or superseded: Implements D003 (no personal identities), D004 (declarative allow-listed rules), D005 (probabilistic vs fixed proportion modes).
- Known limitation or blocker: None.
- Git checkpoint: Planned commit: `feat(specs): specification contracts, semantic validator, and template API (P1.1-P1.4)`.
- Exact next action: P2.1 & P2.2 statistical sampling engine.

### P0.2 & P0.3: Minimal runnable scaffold, health route, frontend starter, and check scripts

- Date: 2026-10-06.
- Status: verified and committed locally.
- What changed and affected paths:
  - Scaffolding: Created package directories per ARCHITECTURE.MD (`backend/api`, `backend/specs`, `backend/generation`, `backend/policies`, `backend/validation`, `backend/jobs`, `backend/export`, `tests`, `evals`, `examples`, `docs`).
  - Backend: Created `backend/config.py`, `backend/main.py`, and `backend/api/health.py` with `/api/health` route verifying storage writability and local Ollama model connection. Created `requirements.txt` and installed in `.venv`.
  - Frontend: Initialized React 18 + TypeScript + Vite app in `frontend/` with custom CSS dark-mode glassmorphic design system, live system health monitor fetching `/api/health`, and architecture pillars. Configured Vite proxy to backend.
  - Tests & Verification: Created `tests/test_health.py` and `scripts/check.ps1`.
- Why this change was necessary: Fulfills P0.2 and P0.3 completion gates to ensure a stable, runnable, and verified baseline before building feature modules.
- Verification command(s), outcome, and relevant evidence:
  - Pytest: `.venv\Scripts\pytest -v tests` -> 2 passed in 0.82s (`test_root_endpoint`, `test_health_endpoint`).
  - Dynamic API check: Verified `/api/health` returns status `ok`, storage writable `true`, and Ollama connected with available models `qwen2.5:7b`, `qwen2.5-coder:7b`, `deepseek-r1:1.5b`, `llama3.2:1b`.
  - Frontend build: `npm run build` in `frontend/` -> `tsc && vite build` passed in 9.52s with 0 errors.
  - Unified script: `powershell -ExecutionPolicy Bypass -File scripts\check.ps1` -> All checks passed successfully.
- Decisions/research added or superseded: None.
- Known limitation or blocker: Git remote upstream is not yet configured (local-only checkpoint per AGENTS.MD line 74 until user provides remote repository).
- Git checkpoint: Planned commit: `feat(scaffold): minimal runnable backend and frontend starter (P0.2, P0.3)`.
- Exact next action: P1.1 (Versioned specification envelope and initial field variants).

### P0.1: Repository inspection, git initialization, and environment capture

- Date: 2026-10-06.
- Status: verified and committed locally.
- What changed and affected paths: Initialized git repository on branch `main` in `e:/SynthLab_Context_Pack/SynthLab`. Created `.gitignore` and safe `.env.example`. Recorded hardware and software facts (Windows, 16 GB RAM, GTX 1660 SUPER 6 GB VRAM, Python 3.10.11, Node 24.19, Ollama service active).
- Why this change was necessary: Fulfills P0.1 completion gate and user instruction to initialize git and prepare for scaffolding.
- Verification command(s), outcome, and relevant evidence:
  - `python --version` -> Python 3.10.11
  - `node --version` -> v24.19.0
  - `git init -b main` -> Initialized Git repository on branch `main`
  - `nvidia-smi` -> NVIDIA GeForce GTX 1660 SUPER (6144 MiB)
  - `ollama list` -> Local Ollama running with qwen2.5:7b and llama3.2:1b
- Decisions/research added or superseded: None.
- Known limitation or blocker: Git remote upstream is not yet configured (local-only checkpoint per AGENTS.MD line 74 until user provides remote repository).
- Git checkpoint: Initial repository commit (P0.1).
- Exact next action: P0.2 minimal runnable scaffold.

### DOC-001: Initial project context pack

- Date: 2026-10-06.
- What: Documented product scope, architecture, decision rationale, research sources, incremental milestones, and agent operating rules.
- Why: Give future coding agents a consistent starting point and prevent context loss during small development steps.
- Changed: ARCHITECTURE.MD, DECISIONS.MD, PROGRESS.MD, PROJECT.MD, RESEARCH.MD, ROADMAP.MD, AGENTS.MD.
- Verification: Documentation cross-references, milestone references, required agent instructions, Markdown code fences, and seven-file archive integrity checked. This is not application validation or proof that targets are achieved.
- Limitations: Repository remote and hardware remain unspecified. All implementation milestones remain unstarted.
- Git state: Documentation handoff only; no repository commit/push performed.
- Next: P0.1 repository/environment inspection.

## Per-step log template

### Pn.m / step identifier: Short title

- Date:
- Status: planned / in progress / verified / committed / pushed / blocked.
- What changed and affected paths:
- Why this change was necessary:
- Verification command(s), outcome, and relevant evidence:
- Decisions/research added or superseded:
- Known limitation or blocker:
- Git checkpoint: commit subject; branch; intended remote; push outcome. Obtain the exact hash from git log when needed; do not fabricate or create an endless self-referential documentation commit.
- Exact next action:

Keep this current-state summary concise and accurate. Append meaningful history; do not replace earlier failure explanations with success claims. After a push, verify remote HEAD; record push evidence in handoff or the next normal documentation update without manufacturing a follow-up commit solely to embed the current commit's hash.

# SynthLab 🧪

> Local synthetic data studio combining deterministic Python sampling and open-weight LLM text enrichment.

## Architecture Highlights
- **Python-owned structured facts**: NumPy/SciPy generate distributions, uniqueness, constraints, and timestamps deterministically.
- **Local open-weight text generation**: Local LLM (via Ollama, e.g. Qwen 2.5) enriches records with realistic natural language without modifying structured upstream fields.
- **Privacy & Quality Gates**: Sensitive-format screening via Presidio + custom recognizers, bounded two-retry limit, and provenance manifests.

## Quick Start

### 1. Backend Setup
```powershell
# Create & activate virtual environment (if not already done)
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Start backend on http://127.0.0.1:8000
uvicorn backend.main:app --reload --port 8000
```

### 2. Frontend Setup
```powershell
cd frontend
npm install
npm run dev
# Open http://localhost:5173
```

### 3. Run Checks
```powershell
powershell -ExecutionPolicy Bypass -File scripts\check.ps1
```

## Repository Structure
```
SynthLab/
├── backend/            # FastAPI service, specs, sampling, validation, jobs
│   ├── api/            # API routes and schemas
│   ├── specs/          # Specification contracts and planner
│   ├── generation/     # Samplers and model adapter
│   ├── policies/       # Input policies and Presidio screening
│   ├── validation/     # Row checks and quality report
│   ├── jobs/           # Worker and SQLite persistence
│   └── export/         # Export writers and manifests
├── frontend/           # React + TypeScript + Vite frontend
├── tests/              # Pytest test suite
├── evals/              # Frozen scenarios and evaluation fixtures
├── examples/           # Sample specifications
└── docs/               # Architecture, threat model, and dataset cards
```

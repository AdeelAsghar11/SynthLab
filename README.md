# SynthLab 🧪

> Local synthetic data studio combining deterministic Python sampling and open-weight LLM text enrichment.

![SynthLab Cover Placeholder](https://via.placeholder.com/1200x400.png?text=SynthLab+Synthetic+Data+Studio)

## Architecture Highlights
- **Python-owned structured facts**: NumPy/SciPy generate distributions, uniqueness, constraints, and timestamps deterministically.
- **Local open-weight text generation**: Local LLM (via Ollama, e.g. Qwen 2.5) enriches records with realistic natural language without modifying structured upstream fields.
- **Privacy & Quality Gates**: Sensitive-format screening via regex, bounded two-retry limit, and provenance manifests.
- **Hybrid Performance**: Offline structural generation achieves ~13,600 rows/second throughput, scaling deterministically prior to LLM enrichment.

## Quick Start

### 1. Backend Setup
```powershell
# Create & activate virtual environment (if not already done)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

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

### 3. Run Checks (P7.4)
```powershell
powershell -ExecutionPolicy Bypass -File scripts\check.ps1
```

## Threat Model & Security Posture
SynthLab operates strictly as a **local-first** environment designed to prevent real PII linkage:
- **No Private-Source Fidelity**: Datasets are schema-driven fictions. Real-world dataset records are never used as training inputs or seeds.
- **Offline Capable**: The backend and frontend execute fully disconnected from public cloud AI platforms, eliminating third-party API data leakage.
- **Screening**: The internal `TextScreeningPolicy` actively blocks generated structural PII (CNIC, SSN, Credit Cards, Emails) via regex interception.

## Dataset Card & Limitations
Generated datasets carry a cryptographically verifiable manifest documenting their exact origins. 
- **Limitation**: SynthLab generates fictional distributions based on theoretical formulas; it does not map to true sociological representations of populations.
- **Semantic Limits**: The deterministic quality gates do not filter semantic toxicity; semantic tone safety relies on the safety alignment of the local LLM weights (e.g. Qwen 2.5).

## Repository Structure
```
SynthLab/
├── backend/            # FastAPI service, specs, sampling, validation, jobs
├── frontend/           # React + TypeScript + Vite frontend
├── tests/              # Pytest test suite (100% passing)
├── evals/              # Frozen scenarios, runners, and screening rubrics
├── examples/           # Sample specifications
└── docs/               # Project specs, architecture, roadmap, decisions, and research
```

## License
MIT License. See `LICENSE` for details.

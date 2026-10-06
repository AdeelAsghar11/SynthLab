# SynthLab 🧪

> **The deterministically safe, local-first synthetic data studio.**

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](#)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](#)
[![License](https://img.shields.io/badge/license-MIT-green)](#)
[![Local LLM](https://img.shields.io/badge/LLM-Ollama-purple)](#)

![SynthLab Cover Placeholder](https://via.placeholder.com/1200x400/0f172a/38bdf8.png?text=SynthLab+Synthetic+Data+Studio)

SynthLab is a highly rigorous, local-first synthetic data generation platform. By enforcing a strict architectural boundary between **deterministic mathematical sampling** and **generative AI text enrichment**, SynthLab creates perfectly valid datasets that never suffer from LLM schema hallucinations or constraint drift.

If you need millions of rows of safe, mathematically precise, schema-valid data paired with realistic support tickets or organic text—all without sending a single byte to the cloud—SynthLab is built for you.

---

## 🎯 Key Capabilities

- **Mathematical Perfection**: Leveraging NumPy and SciPy, the Python generation engine guarantees precise categorical distributions, largest-remainder quota allocations, unique identifiers, and strict numerical bounds.
- **Organic Text Enrichment**: Seamlessly integrates with [Ollama](https://ollama.com/) (e.g., Qwen 2.5, Llama 3) to inject realistic natural language into structured rows *without* allowing the LLM to mutate the underlying factual data.
- **Extreme Throughput**: The deterministic offline engine is capable of scaling to **~13,600 rows per second** on a single thread.
- **Privacy & Quality Gates**: Bounded retries and regex-based interception mechanisms immediately block simulated structural PII (CNIC, SSN, Credit Cards, Emails) from bleeding into the output.
- **Cryptographic Provenance**: Every generated dataset provides an immutable JSON manifest documenting the exact seeds, templates, and limits used to guarantee perfect reproducibility.

---

## 🚀 Quick Start

SynthLab is split into a robust FastAPI backend and a beautiful React/Vite frontend workspace.

### Prerequisites
- **Python 3.10+**
- **Node.js 24+**
- **Ollama** (optional, but required for LLM text enrichment. Pull a model like `qwen2.5:7b` locally)

### 1. Launch the Backend
```powershell
# Create & activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install required dependencies
pip install -r requirements.txt

# Start the FastAPI service
uvicorn backend.main:app --reload --port 8000
```
*The backend will now be accessible at `http://127.0.0.1:8000`.*

### 2. Launch the Frontend Workspace
Open a new terminal window:
```powershell
cd frontend
npm install
npm run dev
```
*Open your browser and navigate to `http://localhost:5173` to access the Data Studio.*

### 3. Verify Health & Tests
To verify your environment is correctly configured, run the integrated test suite:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\check.ps1
```

---

## 🏗️ Architecture & Threat Model

SynthLab operates strictly as a **local-first** environment designed to prevent real PII linkage:
- **No Private-Source Fidelity**: Datasets are schema-driven fictions. Real-world dataset records are never used as training inputs or seeds. Any resemblance to real persons is purely coincidental.
- **Air-Gapped Operation**: The backend and frontend execute fully disconnected from public cloud AI platforms, eliminating third-party API data leakage vectors.
- **Screening Policies**: The internal `TextScreeningPolicy` actively blocks generated structural PII via regex interception. Note that while structural PII is filtered, *semantic tone safety* relies on the safety alignment of the local LLM weights provided by the user.

---

## 📂 Repository Structure

```text
SynthLab/
├── backend/            # FastAPI service, specs, sampling, validation, jobs
├── frontend/           # React + TypeScript + Vite frontend studio
├── tests/              # 100% passing Pytest suite covering logic & APIs
├── evals/              # Frozen scenarios, runners, and throughput benchmarks
├── examples/           # Sample JSON specifications
└── scripts/            # CLI utilities and environment checks
```

---

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.

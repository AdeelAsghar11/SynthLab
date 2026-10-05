import React, { useEffect, useState } from 'react';
import { fetchHealth } from './api';
import { HealthResponse } from './types';

export const App: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastChecked, setLastChecked] = useState<string>('');

  const loadHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchHealth();
      setHealth(data);
      setLastChecked(new Date().toLocaleTimeString());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reach API server');
      setLastChecked(new Date().toLocaleTimeString());
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHealth();
  }, []);

  return (
    <div className="app-container" id="synthlab-root">
      {/* Header */}
      <header className="header" id="synthlab-header">
        <div className="brand-wrapper">
          <div className="brand-icon-box" aria-hidden="true">
            🧪
          </div>
          <div>
            <h1 className="brand-title" id="app-title">SynthLab</h1>
            <p className="brand-subtitle" id="app-subtitle">
              Local Synthetic Data Studio • Hybrid Python & LLM Synthesis
            </p>
          </div>
        </div>

        <div className="header-badges">
          <span className="badge badge-primary" id="branch-badge">
            branch: main
          </span>
          <span className="badge badge-mono" id="version-badge">
            v{health?.version || '0.1.0'}
          </span>
          <span className="badge" id="local-mode-badge">
            🔒 Local-First (No Cloud Egress)
          </span>
        </div>
      </header>

      {/* Main Health Panel */}
      <section className="health-panel" id="health-monitor-section" aria-label="System Health Monitor">
        <div className="panel-title-bar">
          <h2 className="panel-heading" id="health-monitor-heading">
            <span
              className={`status-indicator ${
                loading ? 'loading' : error ? 'offline' : 'online'
              }`}
              id="system-status-indicator"
            />
            System Runtime & Subsystems
          </h2>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            {lastChecked && (
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Checked: {lastChecked}
              </span>
            )}
            <button
              id="refresh-health-button"
              className="refresh-button"
              onClick={loadHealth}
              disabled={loading}
            >
              {loading ? 'Checking...' : '↻ Refresh Status'}
            </button>
          </div>
        </div>

        {error ? (
          <div
            id="health-error-banner"
            style={{
              padding: '1rem',
              borderRadius: 'var(--radius-sm)',
              background: 'rgba(244, 63, 94, 0.1)',
              border: '1px solid rgba(244, 63, 94, 0.3)',
              color: 'var(--accent-rose)',
              fontSize: '0.9rem',
            }}
          >
            <strong>Backend Connection Notice:</strong> {error}. Ensure FastAPI is running on port 8000.
          </div>
        ) : (
          <div className="health-grid" id="health-status-grid">
            {/* FastAPI Backend */}
            <div className="health-card" id="card-api-status">
              <div className="health-card-label">API Gateway</div>
              <div className="health-card-value">
                <span style={{ color: 'var(--accent-emerald)' }}>●</span>
                <span>FastAPI Service</span>
              </div>
              <div className="health-card-meta">
                Status: {health?.status.toUpperCase() || 'CONNECTING...'}
              </div>
            </div>

            {/* Storage System */}
            <div className="health-card" id="card-storage-status">
              <div className="health-card-label">Storage Subsystem</div>
              <div className="health-card-value">
                <span
                  style={{
                    color: health?.storage.writable
                      ? 'var(--accent-emerald)'
                      : 'var(--accent-amber)',
                  }}
                >
                  ●
                </span>
                <span>SQLite & Artifacts</span>
              </div>
              <div className="health-card-meta">
                Writable: {health?.storage.writable ? 'Yes (Verified)' : 'Pending'}
              </div>
            </div>

            {/* Local Inference */}
            <div className="health-card" id="card-inference-status">
              <div className="health-card-label">Local LLM Provider</div>
              <div className="health-card-value">
                <span
                  style={{
                    color:
                      health?.inference.status === 'connected'
                        ? 'var(--accent-emerald)'
                        : 'var(--accent-amber)',
                  }}
                >
                  ●
                </span>
                <span>Ollama Interface</span>
              </div>
              <div className="health-card-meta">
                {health?.inference.status === 'connected'
                  ? `Connected (${health.inference.base_url})`
                  : 'Offline / Template Fallback Active'}
              </div>

              {health?.inference.available_models && health.inference.available_models.length > 0 && (
                <div className="model-pill-list" id="detected-models-list">
                  {health.inference.available_models.map((m) => (
                    <span key={m} className="model-pill">
                      {m}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </section>

      {/* Core Architectural Pillars */}
      <h3 className="section-title">Core Engine Architecture</h3>
      <div className="features-grid">
        <div className="feature-card" id="feature-card-sampler">
          <div
            className="feature-icon-wrapper"
            style={{ background: 'rgba(56, 189, 248, 0.1)', color: 'var(--accent-cyan)' }}
          >
            📊
          </div>
          <h4 className="feature-title">Python Structured Sampler</h4>
          <p className="feature-desc">
            Controls probability distributions (categorical, uniform, truncated-normal) and exact largest-remainder quota allocations. Business rules and uniqueness are strictly guaranteed by Python.
          </p>
          <div className="feature-footer">
            <span>Ownership: Python / NumPy / SciPy</span>
            <span>Deterministic</span>
          </div>
        </div>

        <div className="feature-card" id="feature-card-llm">
          <div
            className="feature-icon-wrapper"
            style={{ background: 'rgba(99, 102, 241, 0.1)', color: 'var(--accent-indigo)' }}
          >
            ⚡
          </div>
          <h4 className="feature-title">Local LLM Enrichment</h4>
          <p className="feature-desc">
            Enriches row facts with realistic natural language (support ticket messages) using local open-weight models like Qwen 2.5 via Ollama. Text cannot overwrite structured facts.
          </p>
          <div className="feature-footer">
            <span>Boundary: Local Open-Weights</span>
            <span>Zero Data Leakage</span>
          </div>
        </div>

        <div className="feature-card" id="feature-card-screening">
          <div
            className="feature-icon-wrapper"
            style={{ background: 'rgba(16, 185, 129, 0.1)', color: 'var(--accent-emerald)' }}
          >
            🛡️
          </div>
          <h4 className="feature-title">Quality Gate & Screening</h4>
          <p className="feature-desc">
            Layered Presidio and pattern recognizers screen for sensitive formats with a maximum of two bounded retries per row skeleton. Full dataset manifests document provenance and reproducibility.
          </p>
          <div className="feature-footer">
            <span>Validation: Presidio + Rules</span>
            <span>Provenance Manifest</span>
          </div>
        </div>
      </div>

      {/* Roadmap Progress Banner */}
      <div className="roadmap-banner" id="roadmap-banner">
        <div className="roadmap-info">
          <h4>Development Roadmap & Milestones</h4>
          <p>Strict incremental delivery with per-step verification and git checkpoints.</p>
        </div>

        <div className="roadmap-steps">
          <span className="step-badge done" title="P0.1: Repo & Environment Facts">
            ✓ P0.1
          </span>
          <span className="step-badge active" title="P0.2: Minimal Runnable Scaffold">
            ● P0.2 Active
          </span>
          <span className="step-badge next" title="P1.1: Specification Envelope">
            ○ P1.1 Next
          </span>
          <span className="step-badge next" title="P2: Statistical Generation">
            ○ P2
          </span>
          <span className="step-badge next" title="P3: Text & Screening">
            ○ P3
          </span>
        </div>
      </div>
    </div>
  );
};

export default App;

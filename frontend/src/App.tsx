import React, { useEffect, useState } from 'react';
import { fetchHealth, fetchTemplates, fetchTemplate } from './api';
import { HealthResponse, TemplateSummary, DatasetSpec } from './types';
import { TemplatePicker } from './components/TemplatePicker';
import { SpecEditor } from './components/SpecEditor';
import { PreviewGenerator } from './components/PreviewGenerator';

export const App: React.FC = () => {
  // Runtime Health State
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthLoading, setHealthLoading] = useState<boolean>(true);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [lastChecked, setLastChecked] = useState<string>('');

  // Workspace Navigation & Templates State
  const [activeTab, setActiveTab] = useState<'spec' | 'preview' | 'quality'>('spec');
  const [templates, setTemplates] = useState<TemplateSummary[]>([]);
  const [templatesLoading, setTemplatesLoading] = useState<boolean>(true);
  const [templatesError, setTemplatesError] = useState<string | null>(null);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null);
  const [activeSpec, setActiveSpec] = useState<DatasetSpec | null>(null);
  const [specLoading, setSpecLoading] = useState<boolean>(false);
  const [specError, setSpecError] = useState<string | null>(null);

  const loadHealth = async () => {
    setHealthLoading(true);
    setHealthError(null);
    try {
      const data = await fetchHealth();
      setHealth(data);
      setLastChecked(new Date().toLocaleTimeString());
    } catch (err) {
      setHealthError(err instanceof Error ? err.message : 'Failed to reach API server');
      setLastChecked(new Date().toLocaleTimeString());
    } finally {
      setHealthLoading(false);
    }
  };

  const loadTemplates = async () => {
    setTemplatesLoading(true);
    setTemplatesError(null);
    try {
      const list = await fetchTemplates();
      setTemplates(list);
      if (list.length > 0 && !selectedTemplateId) {
        handleSelectTemplate(list[0].id);
      }
    } catch (err) {
      setTemplatesError(err instanceof Error ? err.message : 'Failed to load templates');
    } finally {
      setTemplatesLoading(false);
    }
  };

  const handleSelectTemplate = async (templateId: string) => {
    setSelectedTemplateId(templateId);
    setSpecLoading(true);
    setSpecError(null);
    try {
      const spec = await fetchTemplate(templateId);
      setActiveSpec(spec);
    } catch (err) {
      setSpecError(err instanceof Error ? err.message : `Failed to load template ${templateId}`);
    } finally {
      setSpecLoading(false);
    }
  };

  useEffect(() => {
    loadHealth();
    loadTemplates();
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
                healthLoading ? 'loading' : healthError ? 'offline' : 'online'
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
              disabled={healthLoading}
            >
              {healthLoading ? 'Checking...' : '↻ Refresh Status'}
            </button>
          </div>
        </div>

        {healthError ? (
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
            <strong>Backend Connection Notice:</strong> {healthError}. Ensure FastAPI is running on port 8000.
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

      {/* Workspace Tabs Navigation */}
      <div className="workspace-tabs" id="workspace-tabs">
        <button
          id="tab-spec-btn"
          className={`workspace-tab ${activeTab === 'spec' ? 'active' : ''}`}
          onClick={() => setActiveTab('spec')}
        >
          📋 1. Specification & Schema
        </button>
        <button
          id="tab-preview-btn"
          className={`workspace-tab ${activeTab === 'preview' ? 'active' : ''}`}
          onClick={() => setActiveTab('preview')}
        >
          ⚡ 2. Generation & Preview
        </button>
        <button
          id="tab-quality-btn"
          className={`workspace-tab ${activeTab === 'quality' ? 'active' : ''}`}
          onClick={() => setActiveTab('quality')}
        >
          🛡️ 3. Quality & Manifest
        </button>
      </div>

      {/* Tab 1: Specification & Schema (P5.1 Milestone) */}
      {activeTab === 'spec' && (
        <div className="workspace-grid" id="spec-workspace-grid">
          {/* Left Column: Template Picker & Boundaries Note */}
          <div>
            <TemplatePicker
              templates={templates}
              selectedTemplateId={selectedTemplateId}
              onSelectTemplate={handleSelectTemplate}
              loading={templatesLoading}
            />

            {templatesError && (
              <div
                style={{
                  padding: '0.85rem',
                  borderRadius: 'var(--radius-sm)',
                  background: 'rgba(244, 63, 94, 0.1)',
                  border: '1px solid rgba(244, 63, 94, 0.3)',
                  color: 'var(--accent-rose)',
                  fontSize: '0.85rem',
                  marginTop: '0.75rem',
                }}
              >
                {templatesError}
              </div>
            )}

            <div className="card-panel" style={{ marginTop: '1.25rem' }}>
              <h4 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '0.5rem' }}>
                🔒 Separation of Boundaries
              </h4>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                <strong>Python</strong> deterministically generates distributions, category quotas, IDs, and numeric rules.
                <br /><br />
                <strong>Local LLM (via Ollama)</strong> strictly enriches approved text fields without ever altering upstream structured facts.
              </p>
            </div>
          </div>

          {/* Right Column: Active Specification & Fields Inspector */}
          <div>
            {specLoading ? (
              <div className="card-panel" style={{ textAlign: 'center', padding: '3rem' }}>
                <p style={{ color: 'var(--text-secondary)' }}>Loading specification schema...</p>
              </div>
            ) : specError ? (
              <div className="card-panel">
                <p style={{ color: 'var(--accent-rose)' }}>Error loading specification: {specError}</p>
              </div>
            ) : activeSpec ? (
              <SpecEditor initialSpec={activeSpec} onSpecChange={setActiveSpec} />
            ) : (
              <div className="card-panel">
                <p style={{ color: 'var(--text-muted)' }}>Select a template on the left to inspect the schema.</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 2: Preview & Generation (P5.4) */}
      {activeTab === 'preview' && activeSpec ? (
        <PreviewGenerator spec={activeSpec} hasLocalModel={health?.inference.status === 'connected'} />
      ) : activeTab === 'preview' && (
        <div className="card-panel" style={{ textAlign: 'center', padding: '3.5rem 1.5rem' }}>
          <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>⚠️</div>
          <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>No Specification Selected</h3>
          <p style={{ color: 'var(--text-secondary)', maxWidth: '520px', margin: '0 auto 1.5rem auto', fontSize: '0.9rem' }}>
            Please select a template and configure the dataset specification first.
          </p>
          <button className="btn-secondary" onClick={() => setActiveTab('spec')}>
            ← Go to Specification
          </button>
        </div>
      )}

      {/* Tab 3: Quality Reports & Manifest Placeholder (Next P5.6 milestone) */}
      {activeTab === 'quality' && (
        <div className="card-panel" style={{ textAlign: 'center', padding: '3.5rem 1.5rem' }}>
          <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>🛡️</div>
          <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>Data Quality Reports & Export Manifests</h3>
          <p style={{ color: 'var(--text-secondary)', maxWidth: '520px', margin: '0 auto 1.5rem auto', fontSize: '0.9rem' }}>
            Ready for Milestone P5.6: Category distribution checks, numerical range statistics, formula-safe CSV & JSON dataset downloads, and provenance manifests.
          </p>
          <button className="btn-secondary" onClick={() => setActiveTab('spec')}>
            ← Back to Specification
          </button>
        </div>
      )}

      {/* Core Architectural Pillars */}
      <h3 className="section-title" style={{ marginTop: '2.5rem' }}>Core Engine Architecture</h3>
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
          <span className="step-badge done" title="P0: Scaffolding">✓ P0</span>
          <span className="step-badge done" title="P1: Specification Contracts">✓ P1</span>
          <span className="step-badge done" title="P2: Statistical Generation">✓ P2</span>
          <span className="step-badge done" title="P3: Text & Screening">✓ P3</span>
          <span className="step-badge done" title="P4: Jobs & Storage">✓ P4</span>
          <span className="step-badge active" title="P5.1: Workspace Shell & Templates">● P5.1 Active</span>
          <span className="step-badge next" title="P5.2-P5.6: Interactive Controls">○ P5.2+</span>
        </div>
      </div>
    </div>
  );
};

export default App;

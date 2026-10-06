import React, { useEffect, useState } from 'react';
import { fetchHealth, fetchTemplates, fetchTemplate } from './api';
import { HealthResponse, TemplateSummary, DatasetSpec } from './types';
import { TemplatePicker } from './components/TemplatePicker';
import { SpecEditor } from './components/SpecEditor';
import { PreviewGenerator } from './components/PreviewGenerator';
import { QualityReport } from './components/QualityReport';

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

      {/* Mini Health Bar instead of massive dashboard */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem', padding: '0.75rem 1rem', background: 'var(--surface-light)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)' }}>
          <span
            className={`status-indicator ${
              healthLoading ? 'loading' : healthError ? 'offline' : 'online'
            }`}
            style={{ width: '10px', height: '10px' }}
          />
          <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>
            {healthLoading ? 'Connecting to SynthLab Core...' : healthError ? `System Offline: ${healthError}` : 'System Ready • Local-First Mode'}
          </span>
          {health?.inference.status === 'connected' && (
             <span style={{ fontSize: '0.8rem', color: 'var(--accent-emerald)', marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span className="badge badge-mono">LLM: {health.inference.available_models?.[0] || 'Ollama'}</span>
             </span>
          )}
          {health?.inference.status !== 'connected' && !healthLoading && !healthError && (
             <span style={{ fontSize: '0.8rem', color: 'var(--accent-amber)', marginLeft: 'auto' }}>
                <span className="badge badge-mono">LLM Offline (Using Fast Templates)</span>
             </span>
          )}
      </div>



      {/* Workspace Tabs Navigation */}
      <div className="workspace-tabs" id="workspace-tabs">
        <button
          id="tab-spec-btn"
          className={`workspace-tab ${activeTab === 'spec' ? 'active' : ''}`}
          onClick={() => setActiveTab('spec')}
        >
          📋 1. Configure Dataset
        </button>
        <button
          id="tab-preview-btn"
          className={`workspace-tab ${activeTab === 'preview' ? 'active' : ''}`}
          onClick={() => setActiveTab('preview')}
        >
          ⚡ 2. Generate Data
        </button>
        <button
          id="tab-quality-btn"
          className={`workspace-tab ${activeTab === 'quality' ? 'active' : ''}`}
          onClick={() => setActiveTab('quality')}
        >
          🛡️ 3. Review & Export
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

      {/* Tab 3: Quality Reports & Manifest (P5.6) */}
      {activeTab === 'quality' && activeSpec ? (
        <QualityReport spec={activeSpec} hasLocalModel={health?.inference.status === 'connected'} />
      ) : activeTab === 'quality' && (
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


    </div>
  );
};

export default App;

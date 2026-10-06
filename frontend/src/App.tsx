import React, { useEffect, useState } from 'react';
import { fetchHealth, fetchTemplates, fetchTemplate, generateSpecification } from './api';
import { HealthResponse, TemplateSummary, DatasetSpec } from './types';
import { TemplatePicker } from './components/TemplatePicker';
import { SpecEditor } from './components/SpecEditor';
import { PreviewGenerator } from './components/PreviewGenerator';
import { QualityReport } from './components/QualityReport';
import { TestTube, Lock, ClipboardList, Zap, ShieldCheck, AlertTriangle, Cpu, ArrowLeft } from 'lucide-react';

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

  // AI Builder State
  const [aiPrompt, setAiPrompt] = useState<string>('');
  const [aiGenerating, setAiGenerating] = useState<boolean>(false);

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

  const handleAIGenerate = async () => {
    if (!aiPrompt.trim()) return;
    setAiGenerating(true);
    setSpecError(null);
    setSpecLoading(true);
    try {
      const newSpec = await generateSpecification(aiPrompt);
      setActiveSpec(newSpec);
      setSelectedTemplateId('custom_ai');
    } catch (err) {
      setSpecError(err instanceof Error ? err.message : 'AI Generation Failed');
    } finally {
      setAiGenerating(false);
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
            <TestTube size={44} />
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
            <Lock size={14} /> Local-First (No Cloud Egress)
          </span>
        </div>
      </header>

      {/* Mini Health Bar instead of massive dashboard */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem', padding: '0.75rem 1rem', background: 'var(--bg-card)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
          <span
            className={`status-indicator ${
              healthLoading ? 'loading' : healthError ? 'offline' : 'online'
            }`}
            style={{ width: '10px', height: '10px' }}
          />
          <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>
            {healthLoading
              ? 'Connecting to SynthLab Core...'
              : healthError
                ? `System Offline: ${healthError}`
                : `System Ready • Local-First Mode${lastChecked ? ` • checked ${lastChecked}` : ''}`}
          </span>
          {health?.inference.status === 'connected' && (
             <span style={{ fontSize: '0.8rem', color: 'var(--accent-emerald)', marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span className="badge badge-mono"><Cpu size={14} /> LLM: {health.inference.available_models?.[0] || 'Ollama'}</span>
             </span>
          )}
          {health?.inference.status !== 'connected' && !healthLoading && !healthError && (
             <span style={{ fontSize: '0.8rem', color: 'var(--accent-amber)', marginLeft: 'auto' }}>
                <span className="badge badge-mono">LLM Offline (Using Fast Templates)</span>
             </span>
          )}
      </div>



      {/* Workspace Tabs Navigation */}
      <div className="workspace-tabs" id="workspace-tabs" role="tablist">
        <button
          id="tab-spec-btn"
          role="tab"
          aria-selected={activeTab === 'spec'}
          aria-controls="spec-workspace-grid"
          className={`workspace-tab ${activeTab === 'spec' ? 'active' : ''}`}
          onClick={() => setActiveTab('spec')}
          onKeyDown={(e) => { if (e.key === 'ArrowRight') document.getElementById('tab-preview-btn')?.focus(); }}
        >
          <ClipboardList size={18} aria-hidden="true" /> <span style={{marginLeft: '8px'}}>1. Configure Dataset</span>
        </button>
        <button
          id="tab-preview-btn"
          role="tab"
          aria-selected={activeTab === 'preview'}
          aria-controls="preview-workspace-grid"
          className={`workspace-tab ${activeTab === 'preview' ? 'active' : ''}`}
          onClick={() => setActiveTab('preview')}
          onKeyDown={(e) => { 
            if (e.key === 'ArrowRight') document.getElementById('tab-quality-btn')?.focus(); 
            if (e.key === 'ArrowLeft') document.getElementById('tab-spec-btn')?.focus();
          }}
        >
          <Zap size={18} aria-hidden="true" /> <span style={{marginLeft: '8px'}}>2. Generate Data</span>
        </button>
        <button
          id="tab-quality-btn"
          role="tab"
          aria-selected={activeTab === 'quality'}
          aria-controls="quality-workspace-grid"
          className={`workspace-tab ${activeTab === 'quality' ? 'active' : ''}`}
          onClick={() => setActiveTab('quality')}
          onKeyDown={(e) => { if (e.key === 'ArrowLeft') document.getElementById('tab-preview-btn')?.focus(); }}
        >
          <ShieldCheck size={18} aria-hidden="true" /> <span style={{marginLeft: '8px'}}>3. Review & Export</span>
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
                  background: 'var(--accent-rose)',
                  border: '1px solid var(--accent-rose)',
                  color: '#FFFFFF',
                  fontSize: '0.85rem',
                  marginTop: '0.75rem',
                }}
              >
                {templatesError}
              </div>
            )}

            {/* AI Schema Builder Component */}
            <div className="card-panel" style={{ marginTop: '1.5rem', border: '1px solid var(--border-glow)' }}>
              <div className="card-title-bar" style={{ marginBottom: '0.5rem' }}>
                <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Zap size={18} color="var(--accent-cyan)" /> AI Schema Builder
                </h3>
              </div>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                Describe your use-case (e.g. 10k patient records with blood types) and let the local LLM generate the perfect schema.
              </p>
              <textarea
                className="form-input"
                placeholder="Type your use case here..."
                rows={3}
                value={aiPrompt}
                onChange={e => setAiPrompt(e.target.value)}
                style={{ resize: 'vertical' }}
              />
              <button
                className="btn-primary"
                style={{ width: '100%', marginTop: '1rem' }}
                onClick={handleAIGenerate}
                disabled={aiGenerating || !aiPrompt.trim()}
              >
                {aiGenerating ? (
                  <><span className="status-indicator loading" style={{ width: 10, height: 10 }}></span> Generating...</>
                ) : (
                  'Generate Custom Schema'
                )}
              </button>
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
        <div className="card-panel" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1.5rem', color: 'var(--accent-amber)' }}>
            <AlertTriangle size={56} aria-hidden="true" />
          </div>
          <h3 style={{ fontSize: '1.35rem', marginBottom: '0.75rem' }}>No Specification Selected</h3>
          <p style={{ color: 'var(--text-secondary)', maxWidth: '480px', margin: '0 auto 2rem auto', fontSize: '0.95rem' }}>
            Please select a template and configure the dataset specification first.
          </p>
          <button className="btn-secondary" onClick={() => setActiveTab('spec')}>
            <ArrowLeft size={16} aria-hidden="true" /> <span style={{marginLeft: '6px'}}>Go to Specification</span>
          </button>
        </div>
      )}

      {/* Tab 3: Quality Reports & Manifest (P5.6) */}
      {activeTab === 'quality' && activeSpec ? (
        <QualityReport spec={activeSpec} hasLocalModel={health?.inference.status === 'connected'} />
      ) : activeTab === 'quality' && (
        <div className="card-panel" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1.5rem', color: 'var(--accent-amber)' }}>
            <AlertTriangle size={56} aria-hidden="true" />
          </div>
          <h3 style={{ fontSize: '1.35rem', marginBottom: '0.75rem' }}>No Specification Selected</h3>
          <p style={{ color: 'var(--text-secondary)', maxWidth: '480px', margin: '0 auto 2rem auto', fontSize: '0.95rem' }}>
            Please select a template and configure the dataset specification first.
          </p>
          <button className="btn-secondary" onClick={() => setActiveTab('spec')}>
            <ArrowLeft size={16} aria-hidden="true" /> <span style={{marginLeft: '6px'}}>Go to Specification</span>
          </button>
        </div>
      )}


    </div>
  );
};

export default App;

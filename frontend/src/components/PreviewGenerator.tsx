import React, { useState, useEffect, useCallback, useRef } from 'react';
import { DatasetSpec, JobStatusResponse } from '../types';
import { submitJob, fetchJobStatus, cancelJob, fetchJobPreview } from '../api';

interface PreviewGeneratorProps {
  spec: DatasetSpec;
  hasLocalModel: boolean;
}

export const PreviewGenerator: React.FC<PreviewGeneratorProps> = ({ spec, hasLocalModel }) => {
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<JobStatusResponse | null>(null);
  const [previewData, setPreviewData] = useState<Array<Record<string, any>> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [useOllama, setUseOllama] = useState<boolean>(false);
  
  const pollInterval = useRef<number | null>(null);

  const startPolling = useCallback((currentJobId: string) => {
    if (pollInterval.current) clearInterval(pollInterval.current);
    
    pollInterval.current = window.setInterval(async () => {
      try {
        const jobStatus = await fetchJobStatus(currentJobId);
        setStatus(jobStatus);
        
        if (['completed', 'failed', 'cancelled'].includes(jobStatus.status)) {
          if (pollInterval.current) clearInterval(pollInterval.current);
          
          if (jobStatus.status === 'completed') {
            try {
              const data = await fetchJobPreview(currentJobId);
              setPreviewData(data);
            } catch (err) {
              setError(err instanceof Error ? err.message : 'Failed to fetch preview data');
            }
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to poll job status');
        if (pollInterval.current) clearInterval(pollInterval.current);
      }
    }, 1000);
  }, []);

  const handleGenerate = async () => {
    try {
      setError(null);
      setPreviewData(null);
      setStatus(null);
      const res = await submitJob(spec, true, 20, useOllama);
      setJobId(res.id);
      setStatus(res);
      startPolling(res.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start generation job');
    }
  };

  const handleCancel = async () => {
    if (!jobId) return;
    try {
      await cancelJob(jobId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to cancel job');
    }
  };

  useEffect(() => {
    return () => {
      if (pollInterval.current) clearInterval(pollInterval.current);
    };
  }, []);

  const renderTable = () => {
    if (!previewData || previewData.length === 0) return <p>No data generated.</p>;
    
    const columns = Object.keys(previewData[0]);
    
    return (
      <div style={{ overflowX: 'auto', marginTop: '1rem', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem', textAlign: 'left' }}>
          <thead>
            <tr style={{ background: 'var(--bg-card-hover)', borderBottom: '1px solid var(--border-subtle)' }}>
              {columns.map(col => (
                <th key={col} style={{ padding: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {previewData.map((row, i) => (
              <tr key={i} style={{ borderBottom: '1px solid var(--border-subtle)', background: i % 2 === 0 ? 'var(--bg-card)' : 'var(--bg-card-hover)' }}>
                {columns.map(col => {
                  const val = row[col];
                  const displayVal = val === null ? 'null' : typeof val === 'object' ? JSON.stringify(val) : String(val);
                  return (
                    <td key={col} style={{ padding: '0.65rem 0.75rem', color: val === null ? 'var(--text-muted)' : 'var(--text-primary)' }}>
                      {displayVal}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const isRunning = status ? ['queued', 'running', 'cancelling'].includes(status.status) : false;

  return (
    <div className="preview-generator">
      <div className="card-panel" style={{ marginBottom: '1.25rem' }}>
        <div className="card-title-bar">
          <h3 className="card-title">Preview Generation</h3>
        </div>
        
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
          Run a 20-row preview of the current specification <strong>{spec.name}</strong>. This tests the deterministic generator and local text enrichment adapters without writing heavy outputs.
        </p>

        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', marginBottom: '1rem' }}>
          <button 
            className="btn-primary" 
            onClick={handleGenerate}
            disabled={isRunning || false}
          >
            {isRunning ? 'Generating...' : '⚡ Generate 20-Row Preview'}
          </button>
          
          {isRunning && (
            <button className="btn-danger" onClick={handleCancel}>
              ✕ Cancel
            </button>
          )}

          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', opacity: hasLocalModel ? 1 : 0.5 }}>
            <input 
              type="checkbox" 
              checked={useOllama}
              onChange={(e) => setUseOllama(e.target.checked)}
              disabled={!hasLocalModel || isRunning}
            />
            Use Ollama for Text Enrichment
          </label>
        </div>

        {error && (
          <div style={{ padding: '0.85rem', background: 'var(--accent-rose)', color: '#FFFFFF', borderRadius: 'var(--radius-sm)', fontSize: '0.85rem', marginBottom: '1rem' }}>
            {error}
          </div>
        )}

        {status && (
          <div style={{ padding: '1rem', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)', background: 'var(--bg-card-hover)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
              <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>Job Status: <span style={{ textTransform: 'uppercase' }}>{status.status}</span></div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>ID: {status.id}</div>
            </div>
            
            <div style={{ width: '100%', background: 'var(--border-subtle)', height: '6px', borderRadius: '3px', overflow: 'hidden' }}>
              <div style={{ 
                height: '100%', 
                background: status.status === 'failed' ? 'var(--accent-rose)' : status.status === 'completed' ? 'var(--accent-emerald)' : 'var(--accent-cyan)', 
                width: `${Math.max(5, (status.progress / 20) * 100)}%`,
                transition: 'width 0.3s ease'
              }} />
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem', textAlign: 'right' }}>
              Progress: {status.progress} / 20 rows
            </div>

            {status.error_message && (
              <div style={{ marginTop: '0.5rem', color: 'var(--accent-rose)', fontSize: '0.8rem' }}>
                Error: {status.error_message}
              </div>
            )}
          </div>
        )}
      </div>

      {previewData && (
        <div className="card-panel">
          <div className="card-title-bar">
            <h3 className="card-title">Preview Results ({previewData.length} rows)</h3>
          </div>
          {renderTable()}
        </div>
      )}
    </div>
  );
};

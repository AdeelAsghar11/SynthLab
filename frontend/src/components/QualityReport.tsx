import React, { useState, useEffect, useCallback, useRef } from 'react';
import { DatasetSpec, JobStatusResponse, DatasetValidationReport } from '../types';
import { submitJob, fetchJobStatus, cancelJob, fetchJobReport, fetchJobManifest } from '../api';

interface QualityReportProps {
  spec: DatasetSpec;
  hasLocalModel: boolean;
}

export const QualityReport: React.FC<QualityReportProps> = ({ spec, hasLocalModel }) => {
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<JobStatusResponse | null>(null);
  const [report, setReport] = useState<DatasetValidationReport | null>(null);
  const [manifest, setManifest] = useState<Record<string, any> | null>(null);
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
              const [reportData, manifestData] = await Promise.all([
                fetchJobReport(currentJobId),
                fetchJobManifest(currentJobId)
              ]);
              setReport(reportData);
              setManifest(manifestData);
            } catch (err) {
              setError(err instanceof Error ? err.message : 'Failed to fetch report or manifest');
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
      setReport(null);
      setManifest(null);
      setStatus(null);
      const res = await submitJob(spec, false, spec.row_count, useOllama);
      setJobId(res.id);
      setStatus(res);
      startPolling(res.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start full generation job');
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

  const isRunning = status ? ['queued', 'running', 'cancelling'].includes(status.status) : false;

  return (
    <div className="quality-report">
      <div className="card-panel" style={{ marginBottom: '1.25rem' }}>
        <div className="card-title-bar">
          <h3 className="card-title">Full Generation & Quality Analysis</h3>
        </div>
        
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
          Run the full <strong>{spec.row_count}</strong> rows for <strong>{spec.name}</strong>. Upon completion, you can review data distributions, rule violations, download the provenance manifest, and export the dataset to CSV/JSON.
        </p>

        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', marginBottom: '1rem' }}>
          <button 
            className="btn-primary" 
            onClick={handleGenerate}
            disabled={isRunning || false}
          >
            {isRunning ? 'Generating...' : `🚀 Generate Full Dataset (${spec.row_count} rows)`}
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
          <div style={{ padding: '0.85rem', background: 'rgba(244, 63, 94, 0.1)', color: 'var(--accent-rose)', borderRadius: 'var(--radius-sm)', fontSize: '0.85rem', marginBottom: '1rem' }}>
            {error}
          </div>
        )}

        {status && (
          <div style={{ padding: '1rem', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)', background: 'rgba(15, 23, 42, 0.4)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
              <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>Job Status: <span style={{ textTransform: 'uppercase' }}>{status.status}</span></div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>ID: {status.id}</div>
            </div>
            
            <div style={{ width: '100%', background: 'var(--border-subtle)', height: '6px', borderRadius: '3px', overflow: 'hidden' }}>
              <div style={{ 
                height: '100%', 
                background: status.status === 'failed' ? 'var(--accent-rose)' : status.status === 'completed' ? 'var(--accent-emerald)' : 'var(--accent-cyan)', 
                width: `${Math.max(5, (status.progress / spec.row_count) * 100)}%`,
                transition: 'width 0.3s ease'
              }} />
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem', textAlign: 'right' }}>
              Progress: {status.progress} / {spec.row_count} rows
            </div>

            {status.error_message && (
              <div style={{ marginTop: '0.5rem', color: 'var(--accent-rose)', fontSize: '0.8rem' }}>
                Error: {status.error_message}
              </div>
            )}
          </div>
        )}
      </div>

      {status?.status === 'completed' && jobId && (
        <div className="card-panel" style={{ marginBottom: '1.25rem' }}>
          <div className="card-title-bar">
            <h3 className="card-title">Downloads</h3>
          </div>
          <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
            <a href={`/api/jobs/${encodeURIComponent(jobId)}/exports/csv`} download className="btn-secondary" style={{ textDecoration: 'none' }}>
              📄 Download CSV
            </a>
            <a href={`/api/jobs/${encodeURIComponent(jobId)}/exports/json`} download className="btn-secondary" style={{ textDecoration: 'none' }}>
              {`{ }`} Download JSON
            </a>
          </div>
        </div>
      )}

      {report && (
        <div className="card-panel" style={{ marginBottom: '1.25rem' }}>
          <div className="card-title-bar">
            <h3 className="card-title">Quality Report</h3>
            {report.is_valid ? (
              <span className="tag tag-emerald">PASS</span>
            ) : (
              <span className="tag" style={{ background: 'var(--accent-rose)', color: '#fff' }}>FAIL</span>
            )}
          </div>
          <div style={{ display: 'flex', gap: '2rem', fontSize: '0.85rem', marginBottom: '1rem', color: 'var(--text-secondary)' }}>
            <div>Total Rows: <strong>{report.total_rows}</strong></div>
            <div>Accepted Rows: <strong>{report.accepted_rows}</strong></div>
            <div>Rule Violations: <strong>{report.rule_violations_count}</strong></div>
          </div>
          
          {report.violations && report.violations.length > 0 && (
            <div style={{ background: 'rgba(244, 63, 94, 0.05)', border: '1px solid rgba(244, 63, 94, 0.2)', padding: '0.85rem', borderRadius: 'var(--radius-sm)', marginBottom: '1.5rem' }}>
              <h4 style={{ color: 'var(--accent-rose)', marginTop: 0, fontSize: '0.9rem' }}>Violations</h4>
              <ul style={{ fontSize: '0.8rem', paddingLeft: '1.5rem', marginBottom: 0 }}>
                {report.violations.map((v, i) => (
                  <li key={i}>Row {v.row_index} [{v.field}]: {v.message} ({v.rule})</li>
                ))}
              </ul>
            </div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
            {Object.entries(report.column_summaries).map(([colName, summary]) => (
              <div key={colName} style={{ border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)', padding: '0.85rem' }}>
                <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: '0.5rem', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.25rem' }}>
                  {colName} <span style={{ fontSize: '0.75rem', fontWeight: 400, color: 'var(--text-muted)' }}>({summary.type})</span>
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                  <div>Unique Values: {summary.unique_count}</div>
                  <div>Null Count: {summary.null_count}</div>
                  {summary.numeric_min !== undefined && (
                    <div style={{ marginTop: '0.5rem' }}>
                      Range: [{summary.numeric_min.toFixed(2)}, {summary.numeric_max?.toFixed(2)}]<br/>
                      Mean: {summary.numeric_mean?.toFixed(2)} ± {summary.numeric_std?.toFixed(2)}
                    </div>
                  )}
                  {summary.category_frequencies && (
                    <div style={{ marginTop: '0.5rem' }}>
                      <strong>Frequencies:</strong>
                      <ul style={{ paddingLeft: '1rem', marginTop: '0.2rem', marginBottom: 0 }}>
                        {Object.entries(summary.category_frequencies).map(([cat, freq]) => (
                          <li key={cat}>{cat}: {(freq * 100).toFixed(1)}%</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {manifest && (
        <div className="card-panel">
          <div className="card-title-bar">
            <h3 className="card-title">Provenance Manifest</h3>
          </div>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
            Cryptographically verifiable snapshot of the exact generation envelope.
          </p>
          <pre style={{ background: 'var(--bg-app)', padding: '1rem', borderRadius: 'var(--radius-sm)', fontSize: '0.75rem', overflowX: 'auto', border: '1px solid var(--border-subtle)', fontFamily: 'var(--font-mono)' }}>
            {JSON.stringify(manifest, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};

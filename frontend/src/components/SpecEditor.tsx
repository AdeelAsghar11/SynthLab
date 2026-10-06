import React, { useState, useEffect, useCallback } from 'react';
import { DatasetSpec, FieldSpec, SpecValidationResponse } from '../types';
import { validateSpecification } from '../api';

interface SpecEditorProps {
  initialSpec: DatasetSpec;
  onSpecChange: (spec: DatasetSpec) => void;
}

export const SpecEditor: React.FC<SpecEditorProps> = ({ initialSpec, onSpecChange }) => {
  const [spec, setSpec] = useState<DatasetSpec>(initialSpec);
  const [validation, setValidation] = useState<SpecValidationResponse | null>(null);
  const [validating, setValidating] = useState<boolean>(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  // Sync state if initialSpec completely changes (e.g., loaded a new template)
  useEffect(() => {
    setSpec(initialSpec);
  }, [initialSpec.name]); // Naive check based on name, could be better

  const runValidation = useCallback(async (currentSpec: DatasetSpec) => {
    setValidating(true);
    setValidationError(null);
    try {
      const result = await validateSpecification(currentSpec);
      setValidation(result);
    } catch (err) {
      setValidationError(err instanceof Error ? err.message : 'Validation failed');
      setValidation(null);
    } finally {
      setValidating(false);
    }
  }, []);

  // Debounced validation
  useEffect(() => {
    const timer = setTimeout(() => {
      runValidation(spec);
      onSpecChange(spec);
    }, 500);
    return () => clearTimeout(timer);
  }, [spec, runValidation, onSpecChange]);

  const handleGlobalChange = (field: keyof DatasetSpec, value: any) => {
    setSpec(prev => ({ ...prev, [field]: value }));
  };

  const handleFieldChange = (index: number, updatedField: FieldSpec) => {
    setSpec(prev => {
      const newFields = [...prev.fields];
      newFields[index] = updatedField;
      return { ...prev, fields: newFields };
    });
  };

  const removeField = (index: number) => {
    setSpec(prev => {
      const newFields = [...prev.fields];
      newFields.splice(index, 1);
      return { ...prev, fields: newFields };
    });
  };

  const addField = () => {
    const newField: FieldSpec = {
      name: `new_field_${spec.fields.length + 1}`,
      type: 'text',
      nullable: false,
      null_probability: 0,
      generator: { kind: 'categorical', choices: ['A', 'B'], probabilities: [0.5, 0.5] }
    };
    setSpec(prev => ({ ...prev, fields: [...prev.fields, newField] }));
  };

  return (
    <div className="spec-editor">
      {/* Validation Banner */}
      <div
        className="card-panel"
        style={{
          marginBottom: '1.25rem',
          border: validation?.valid ? '1px solid var(--accent-emerald)' : validationError || (validation && !validation.valid) ? '1px solid var(--accent-rose)' : '1px solid var(--border-subtle)',
          background: validation?.valid ? 'rgba(16, 185, 129, 0.05)' : validationError || (validation && !validation.valid) ? 'rgba(244, 63, 94, 0.05)' : 'var(--bg-card)'
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h4 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            {validating ? (
              <span className="status-indicator loading" />
            ) : validation?.valid ? (
              <span className="status-indicator online" />
            ) : (
              <span className="status-indicator offline" />
            )}
            Live Validation Status
          </h4>
        </div>
        {validationError && (
          <div style={{ color: 'var(--accent-rose)', marginTop: '0.5rem', fontSize: '0.85rem' }}>
            {validationError}
          </div>
        )}
        {validation && !validation.valid && validation.diagnostics && (
          <ul style={{ color: 'var(--accent-rose)', marginTop: '0.5rem', fontSize: '0.85rem', paddingLeft: '1.2rem' }}>
            {validation.diagnostics.map((diag, i) => (
              <li key={i}><strong>{diag.path}</strong>: {diag.message} ({diag.code})</li>
            ))}
          </ul>
        )}
        {validation && validation.valid && (
          <div style={{ color: 'var(--accent-emerald)', marginTop: '0.5rem', fontSize: '0.85rem' }}>
            ✓ Specification is valid. Topological order: {validation.generation_order?.join(' → ')}
          </div>
        )}
      </div>

      {/* Global Settings */}
      <div className="card-panel" style={{ marginBottom: '1.25rem' }}>
        <div className="card-title-bar">
          <h3 className="card-title">Dataset Configuration</h3>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
          <div className="form-group">
            <label className="form-label">Dataset Name</label>
            <input
              type="text"
              className="form-input"
              value={spec.name}
              onChange={e => handleGlobalChange('name', e.target.value)}
            />
          </div>
          <div className="form-group">
            <label className="form-label">Row Count</label>
            <input
              type="number"
              className="form-input"
              value={spec.row_count}
              onChange={e => handleGlobalChange('row_count', parseInt(e.target.value) || 0)}
              min={1}
            />
          </div>
          <div className="form-group">
            <label className="form-label">RNG Seed</label>
            <input
              type="number"
              className="form-input"
              value={spec.seed}
              onChange={e => handleGlobalChange('seed', parseInt(e.target.value) || 0)}
            />
          </div>
          <div className="form-group">
            <label className="form-label">Generation Mode</label>
            <select
              className="form-select"
              value={spec.generation_mode}
              onChange={e => handleGlobalChange('generation_mode', e.target.value)}
            >
              <option value="random">Random Sampling</option>
              <option value="fixed_proportions">Fixed Proportions</option>
            </select>
          </div>
        </div>
      </div>

      {/* Field Editor */}
      <div className="card-panel">
        <div className="card-title-bar">
          <h3 className="card-title">Fields ({spec.fields.length})</h3>
          <button className="btn-secondary" onClick={addField} style={{ padding: '0.35rem 0.75rem', fontSize: '0.8rem' }}>
            + Add Field
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {spec.fields.map((field, index) => (
            <div key={index} style={{ padding: '1rem', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)', background: 'rgba(15, 23, 42, 0.4)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
                <h4 style={{ margin: 0, fontSize: '0.95rem' }}>Field #{index + 1}</h4>
                <button
                  className="btn-danger"
                  onClick={() => removeField(index)}
                  title="Remove Field"
                >
                  ✕
                </button>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Name</label>
                  <input
                    type="text"
                    className="form-input"
                    value={field.name}
                    onChange={e => handleFieldChange(index, { ...field, name: e.target.value })}
                  />
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Type</label>
                  <select
                    className="form-select"
                    value={field.type}
                    onChange={e => handleFieldChange(index, { ...field, type: e.target.value as FieldSpec['type'] })}
                  >
                    <option value="text">Text</option>
                    <option value="integer">Integer</option>
                    <option value="decimal">Decimal</option>
                    <option value="category">Category</option>
                    <option value="datetime">Datetime</option>
                    <option value="boolean">Boolean</option>
                    <option value="identifier">Identifier</option>
                  </select>
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Generator Kind</label>
                  <select
                    className="form-select"
                    value={field.generator.kind}
                    onChange={e => handleFieldChange(index, { ...field, generator: { kind: e.target.value } })}
                  >
                    <option value="categorical">Categorical</option>
                    <option value="uniform">Uniform</option>
                    <option value="truncated_normal">Truncated Normal</option>
                    <option value="date_range">Date Range</option>
                    <option value="synthetic_id">Synthetic ID</option>
                    <option value="llm_text_enrichment">LLM Text Enrichment</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'center' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem' }}>
                  <input
                    type="checkbox"
                    checked={field.nullable}
                    onChange={e => handleFieldChange(index, { ...field, nullable: e.target.checked })}
                  />
                  Nullable
                </label>
                {field.nullable && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <label className="form-label" style={{ marginBottom: 0 }}>Null Prob (0-1):</label>
                    <input
                      type="number"
                      className="form-input"
                      style={{ width: '80px', padding: '0.2rem 0.5rem' }}
                      value={field.null_probability}
                      onChange={e => handleFieldChange(index, { ...field, null_probability: parseFloat(e.target.value) || 0 })}
                      step="0.05"
                      min="0"
                      max="1"
                    />
                  </div>
                )}
              </div>
              
              {/* Note: Generator specific configuration form can be expanded here based on kind */}
              <div style={{ marginTop: '1rem', padding: '0.75rem', background: 'rgba(255,255,255,0.02)', borderRadius: 'var(--radius-sm)' }}>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Raw Generator Config:</div>
                <textarea 
                  className="form-input"
                  style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', minHeight: '60px', width: '100%', resize: 'vertical' }}
                  value={JSON.stringify(field.generator, null, 2)}
                  onChange={e => {
                    try {
                      const parsed = JSON.parse(e.target.value);
                      handleFieldChange(index, { ...field, generator: parsed });
                    } catch (err) {
                      // ignore parse errors while typing
                    }
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

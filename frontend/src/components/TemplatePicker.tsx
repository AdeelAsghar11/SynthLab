import React from 'react';
import { TemplateSummary } from '../types';

interface TemplatePickerProps {
  templates: TemplateSummary[];
  selectedTemplateId: string | null;
  onSelectTemplate: (id: string) => void;
  loading: boolean;
}

export const TemplatePicker: React.FC<TemplatePickerProps> = ({
  templates,
  selectedTemplateId,
  onSelectTemplate,
  loading,
}) => {
  return (
    <div className="card-panel" id="template-picker-card">
      <div className="card-title-bar">
        <h3 className="card-title" id="template-picker-title">Dataset Templates</h3>
        <span className="badge badge-primary">{templates.length} Approved</span>
      </div>

      <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
        Select a pre-validated domain schema to generate structured rows and natural language.
      </p>

      {loading ? (
        <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Loading templates...</div>
      ) : (
        <div>
          {templates.map((tmpl) => {
            const isSelected = tmpl.id === selectedTemplateId;
            return (
              <div
                key={tmpl.id}
                id={`template-item-${tmpl.id}`}
                style={{
                  padding: '1rem',
                  borderRadius: 'var(--radius-sm)',
                  border: isSelected
                    ? '1px solid var(--accent-cyan)'
                    : '1px solid var(--border-subtle)',
                  background: isSelected ? 'rgba(56, 189, 248, 0.08)' : 'rgba(15, 23, 42, 0.5)',
                  marginBottom: '0.75rem',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                }}
                onClick={() => onSelectTemplate(tmpl.id)}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                  <h4 style={{ fontSize: '0.95rem', fontWeight: 600 }}>{tmpl.name}</h4>
                  <span className="tag tag-cyan">{tmpl.field_count} Fields</span>
                </div>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
                  {tmpl.description}
                </p>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    Default: {tmpl.default_row_count} rows • PKR currency
                  </span>
                  <button
                    className="btn-secondary"
                    style={{ padding: '0.35rem 0.75rem', fontSize: '0.8rem' }}
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectTemplate(tmpl.id);
                    }}
                  >
                    {isSelected ? '✓ Loaded' : 'Load Template'}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

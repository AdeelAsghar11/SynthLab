export interface StorageHealth {
  status: string;
  writable: boolean;
  db_path: string;
}

export interface InferenceHealth {
  status: 'connected' | 'offline' | 'unavailable';
  provider: string;
  base_url: string;
  available_models: string[];
}

export interface HealthResponse {
  status: string;
  version: string;
  timestamp: string;
  storage: StorageHealth;
  inference: InferenceHealth;
}

export interface TemplateSummary {
  id: string;
  name: string;
  description: string;
  field_count: number;
  default_row_count: number;
}

export interface GeneratorConfig {
  kind: string;
  [key: string]: any;
}

export interface FieldSpec {
  name: string;
  type: 'integer' | 'decimal' | 'category' | 'datetime' | 'boolean' | 'identifier' | 'text';
  nullable: boolean;
  null_probability: number;
  description?: string;
  generator: GeneratorConfig;
}

export interface DatasetSpec {
  spec_version: 1;
  name: string;
  row_count: number;
  seed: number;
  generation_mode: 'random' | 'fixed_proportions';
  fields: FieldSpec[];
  constraints: any[];
  text_options: {
    template_version: string;
    max_length: number;
    timeout_seconds: number;
  };
}

export interface SpecValidationResponse {
  valid: boolean;
  diagnostics: Array<{
    code: string;
    path: string;
    message: string;
  }>;
  generation_order: string[];
}

export type JobStatus = 'queued' | 'running' | 'completed' | 'failed' | 'cancelling' | 'cancelled';

export interface JobStatusResponse {
  id: string;
  status: JobStatus;
  progress: number;
  row_count: number;
  is_preview: boolean;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  error_message?: string;
  has_artifacts: boolean;
}

export interface ColumnSummary {
  name: string;
  type: string;
  null_count: number;
  unique_count: number;
  category_counts?: Record<string, number>;
  category_frequencies?: Record<string, number>;
  numeric_min?: number;
  numeric_max?: number;
  numeric_mean?: number;
  numeric_std?: number;
}

export interface DatasetValidationReport {
  is_valid: boolean;
  total_rows: number;
  accepted_rows: number;
  rule_violations_count: number;
  violations: Array<{
    row_index: number;
    field: string;
    rule: string;
    message: string;
  }>;
  column_summaries: Record<string, ColumnSummary>;
}

import {
  DatasetSpec,
  DatasetValidationReport,
  HealthResponse,
  JobStatusResponse,
  SpecValidationResponse,
  TemplateSummary,
} from './types';

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch('/api/health');
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json();
}

export async function fetchTemplates(): Promise<TemplateSummary[]> {
  const res = await fetch('/api/templates');
  if (!res.ok) throw new Error(`Failed to fetch templates: ${res.status}`);
  return res.json();
}

export async function fetchTemplate(id: string): Promise<DatasetSpec> {
  const res = await fetch(`/api/templates/${encodeURIComponent(id)}`);
  if (!res.ok) throw new Error(`Failed to load template ${id}: ${res.status}`);
  return res.json();
}

export async function validateSpecification(spec: DatasetSpec): Promise<SpecValidationResponse> {
  const res = await fetch('/api/specs/validate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(spec),
  });
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}));
    throw new Error(errorBody.detail || `Validation call failed with status: ${res.status}`);
  }
  return res.json();
}

export async function generateSpecification(prompt: string): Promise<DatasetSpec> {
  const res = await fetch('/api/specs/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt }),
  });
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}));
    const detail = errorBody.detail;
    const message = typeof detail === 'string'
      ? detail
      : detail?.message;
    throw new Error(message || `AI Generation failed with status: ${res.status}`);
  }
  return res.json();
}


export async function submitJob(
  spec: DatasetSpec,
  isPreview: boolean = false,
  rowCount?: number,
  useOllama: boolean = false,
): Promise<JobStatusResponse> {
  const res = await fetch('/api/jobs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      spec,
      is_preview: isPreview,
      row_count: rowCount,
      use_ollama: useOllama,
    }),
  });
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}));
    throw new Error(errorBody.detail || `Failed to submit job: ${res.status}`);
  }
  return res.json();
}

export async function fetchJobStatus(jobId: string): Promise<JobStatusResponse> {
  const res = await fetch(`/api/jobs/${encodeURIComponent(jobId)}`);
  if (!res.ok) throw new Error(`Failed to get status for job ${jobId}`);
  return res.json();
}

export async function cancelJob(jobId: string): Promise<void> {
  const res = await fetch(`/api/jobs/${encodeURIComponent(jobId)}/cancel`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error(`Failed to cancel job ${jobId}`);
}

export async function fetchJobPreview(jobId: string): Promise<Array<Record<string, any>>> {
  const res = await fetch(`/api/jobs/${encodeURIComponent(jobId)}/preview`);
  if (!res.ok) throw new Error(`Failed to load preview for job ${jobId}`);
  const data = await res.json();
  return data.rows || [];
}

export async function fetchJobReport(jobId: string): Promise<DatasetValidationReport> {
  const res = await fetch(`/api/jobs/${encodeURIComponent(jobId)}/report`);
  if (!res.ok) throw new Error(`Failed to load report for job ${jobId}`);
  return res.json();
}

export async function fetchJobManifest(jobId: string): Promise<Record<string, any>> {
  const res = await fetch(`/api/jobs/${encodeURIComponent(jobId)}/manifest`);
  if (!res.ok) throw new Error(`Failed to load manifest for job ${jobId}`);
  return res.json();
}

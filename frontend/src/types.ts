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

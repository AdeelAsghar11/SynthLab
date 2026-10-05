import asyncio
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import pandas as pd

from backend.config import settings
from backend.generation.adapters import FakeModelAdapter, OllamaModelAdapter, TemplateTextAdapter
from backend.generation.engine import GenerationEngine
from backend.generation.text_enricher import TextEnricher
from backend.jobs.models import JobRecord, JobStatus
from backend.jobs.repository import JobRepository
from backend.specs.models import DatasetSpec
from backend.validation.validator import validate_dataset
from backend.export.writers import export_dataset_csv, export_dataset_json, export_manifest, export_report

class JobManager:
    """Orchestrates job submission, execution, cancellation, and artifact persistence."""

    def __init__(self, repo: JobRepository | None = None):
        self.repo = repo if repo is not None else JobRepository()
        self.cancellation_requested: set[str] = set()

    def submit_job(
        self,
        spec: DatasetSpec,
        is_preview: bool = False,
        row_count: int | None = None,
        use_ollama: bool = False,
    ) -> str:
        job_id = str(uuid.uuid4())
        n_rows = row_count if row_count is not None else (20 if is_preview else spec.row_count)
        artifact_dir = settings.artifacts_dir / job_id

        now = datetime.now(timezone.utc).isoformat()
        record = JobRecord(
            id=job_id,
            spec_json=json.dumps(spec.model_dump(mode="json")),
            status=JobStatus.QUEUED,
            progress=0.0,
            row_count=n_rows,
            is_preview=is_preview,
            use_ollama=use_ollama,
            created_at=now,
            updated_at=now,
            artifact_dir=str(artifact_dir),
        )
        self.repo.create_job(record)
        return job_id

    def cancel_job(self, job_id: str) -> bool:
        """Idempotently requests job cancellation."""
        record = self.repo.get_job(job_id)
        if not record:
            return False

        if record.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
            return True

        self.cancellation_requested.add(job_id)
        self.repo.update_status(job_id, JobStatus.CANCELLING)
        return True

    def execute_job_sync(self, job_id: str) -> None:
        """Synchronously executes the job lifecycle (suitable for background worker threads)."""
        record = self.repo.get_job(job_id)
        if not record:
            return

        if job_id in self.cancellation_requested:
            self.repo.update_status(job_id, JobStatus.CANCELLED, progress=0.0)
            return

        self.repo.update_status(job_id, JobStatus.RUNNING, progress=0.1)
        artifact_dir = Path(record.artifact_dir)

        try:
            # 1. Parse specification
            spec_dict = json.loads(record.spec_json)
            spec = DatasetSpec.model_validate(spec_dict)

            # 2. Generate structured skeletons
            engine = GenerationEngine(spec)
            df_skeletons = engine.generate_skeletons(row_count=record.row_count, seed=spec.seed)

            # Check cancellation checkpoint
            if job_id in self.cancellation_requested:
                self.repo.update_status(job_id, JobStatus.CANCELLED, progress=0.4)
                return

            self.repo.update_progress(job_id, 0.4)

            # 3. Model Adapter Selection & Text Enrichment
            adapter_name = "template-adapter"
            if record.use_ollama:
                ollama = OllamaModelAdapter(
                    base_url=settings.ollama_base_url,
                    model=settings.default_model,
                )
                if ollama.health_check():
                    adapter = ollama
                    adapter_name = f"ollama/{settings.default_model}"
                else:
                    adapter = TemplateTextAdapter()
            else:
                adapter = TemplateTextAdapter()

            enricher = TextEnricher(adapter=adapter, max_retries=2)
            df_enriched, metrics = enricher.enrich_dataset(df_skeletons, spec)

            # Check cancellation checkpoint
            if job_id in self.cancellation_requested:
                self.repo.update_status(job_id, JobStatus.CANCELLED, progress=0.7)
                return

            self.repo.update_progress(job_id, 0.7)

            # 4. Dataset Validation & Quality Report
            report = validate_dataset(df_enriched, spec, allow_pending_text=False)

            # Check cancellation checkpoint
            if job_id in self.cancellation_requested:
                self.repo.update_status(job_id, JobStatus.CANCELLED, progress=0.85)
                return

            # 5. Atomic Artifact Persistence (Completed Only)
            artifact_dir.mkdir(parents=True, exist_ok=True)
            export_dataset_csv(df_enriched, artifact_dir / "dataset.csv", safe_mode=True)
            export_dataset_json(df_enriched, artifact_dir / "dataset.json")
            export_report(report, artifact_dir)
            export_manifest(
                spec=spec,
                output_dir=artifact_dir,
                row_count=record.row_count,
                accepted_count=report.accepted_rows,
                model_name=adapter_name,
                metrics=metrics,
            )

            # 6. Mark Job Completed
            self.repo.update_status(job_id, JobStatus.COMPLETED, progress=1.0)

        except Exception as e:
            self.repo.update_status(job_id, JobStatus.FAILED, error_message=str(e))
        finally:
            self.cancellation_requested.discard(job_id)

job_manager = JobManager()

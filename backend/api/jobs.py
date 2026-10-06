import json
from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import ValidationError

from backend.jobs.manager import job_manager
from backend.jobs.models import JobCreateRequest, JobRecord, JobStatus, JobStatusResponse
from backend.policies.schema_policy import SPEC_REJECTION_MESSAGE, screen_dataset_spec
from backend.specs.models import DatasetSpec
from backend.specs.validator import validate_spec_semantics

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

@router.post("", response_model=JobStatusResponse, status_code=status.HTTP_202_ACCEPTED)
def submit_job(req: JobCreateRequest, background_tasks: BackgroundTasks) -> JobStatusResponse:
    """Submits a dataset generation or preview job."""
    try:
        spec = DatasetSpec.model_validate(req.spec)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"code": "SPEC_INVALID", "message": "The dataset specification is invalid."},
        ) from exc

    policy_result = screen_dataset_spec(spec)
    if not policy_result.is_safe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "SPEC_POLICY_REJECTED", "message": SPEC_REJECTION_MESSAGE},
        )

    # Validate semantic contract
    diagnostics = validate_spec_semantics(spec)
    if diagnostics:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"errors": [d._asdict() for d in diagnostics]},
        )

    # Submit to queue
    job_id = job_manager.submit_job(
        spec=spec,
        is_preview=req.is_preview,
        row_count=req.row_count,
        use_ollama=req.use_ollama,
    )

    # Enqueue execution in background
    background_tasks.add_task(job_manager.execute_job_sync, job_id)

    record = job_manager.repo.get_job(job_id)
    return JobStatusResponse(
        id=record.id,
        status=record.status,
        progress=record.progress,
        row_count=record.row_count,
        is_preview=record.is_preview,
        created_at=record.created_at,
        updated_at=record.updated_at,
        completed_at=record.completed_at,
        error_message=record.error_message,
        has_artifacts=False,
    )

@router.get("/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str) -> JobStatusResponse:
    """Returns current status, progress, and error state for a job."""
    record = job_manager.repo.get_job(job_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job '{job_id}' not found.")

    artifact_dir = Path(record.artifact_dir)
    has_artifacts = (artifact_dir / "dataset.csv").exists() and (artifact_dir / "dataset.json").exists()

    return JobStatusResponse(
        id=record.id,
        status=record.status,
        progress=record.progress,
        row_count=record.row_count,
        is_preview=record.is_preview,
        created_at=record.created_at,
        updated_at=record.updated_at,
        completed_at=record.completed_at,
        error_message=record.error_message,
        has_artifacts=has_artifacts,
    )

@router.post("/{job_id}/cancel")
def cancel_job(job_id: str):
    """Idempotently requests job cancellation."""
    success = job_manager.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job '{job_id}' not found.")
    return {"status": "cancelling", "job_id": job_id}

@router.get("/{job_id}/preview")
def get_job_preview(job_id: str):
    """Returns accepted preview rows for a completed job."""
    record = job_manager.repo.get_job(job_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    if record.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Preview is only available for completed jobs. Current status: '{record.status}'.",
        )

    json_path = Path(record.artifact_dir) / "dataset.json"
    if not json_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifacts not found.")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return {"job_id": job_id, "rows": data[:20]}

@router.get("/{job_id}/report")
def get_job_report(job_id: str):
    """Returns dataset validation report and screening metrics for a completed job."""
    record = job_manager.repo.get_job(job_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    if record.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Report is only available for completed jobs. Current status: '{record.status}'.",
        )

    report_path = Path(record.artifact_dir) / "report.json"
    if not report_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report artifact not found.")

    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    return report

@router.get("/{job_id}/manifest")
def get_job_manifest(job_id: str):
    """Returns generation provenance manifest for a completed job."""
    record = job_manager.repo.get_job(job_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    if record.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Manifest is only available for completed jobs. Current status: '{record.status}'.",
        )

    manifest_path = Path(record.artifact_dir) / "manifest.json"
    if not manifest_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manifest artifact not found.")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    return manifest

@router.get("/{job_id}/exports/{format}")
def download_export(job_id: str, format: str):
    """Downloads dataset in requested format (csv or json) for completed jobs only."""
    record = job_manager.repo.get_job(job_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    if record.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Exports are only available for completed jobs. Current status: '{record.status}'.",
        )

    format_lower = format.lower()
    if format_lower not in ("csv", "json"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format '{format}'. Supported formats: csv, json.",
        )

    file_path = Path(record.artifact_dir) / f"dataset.{format_lower}"
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requested export file missing.")

    media_type = "text/csv" if format_lower == "csv" else "application/json"
    return FileResponse(
        path=str(file_path),
        filename=f"synthlab_{job_id[:8]}_dataset.{format_lower}",
        media_type=media_type,
    )

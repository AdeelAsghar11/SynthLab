import json
import pytest
import pandas as pd
from pathlib import Path
from fastapi.testclient import TestClient

from backend.main import app
from backend.jobs.models import JobRecord, JobStatus
from backend.jobs.repository import JobRepository
from backend.jobs.manager import JobManager
from backend.export.writers import sanitize_for_spreadsheet, export_dataset_csv, export_dataset_json
from backend.specs import get_default_support_ticket_spec

client = TestClient(app)

def test_spreadsheet_formula_sanitization():
    assert sanitize_for_spreadsheet("=SUM(A1:A10)") == "'=SUM(A1:A10)"
    assert sanitize_for_spreadsheet("+cmd|' /C calc'!A0") == "'+cmd|' /C calc'!A0"
    assert sanitize_for_spreadsheet("-100") == "'-100"
    assert sanitize_for_spreadsheet("@test") == "'@test"
    assert sanitize_for_spreadsheet("Safe Normal Text") == "Safe Normal Text"
    assert sanitize_for_spreadsheet(4500.5) == 4500.5

def test_job_repository_crud(tmp_path):
    db_file = tmp_path / "test_jobs.db"
    repo = JobRepository(db_path=db_file)

    record = JobRecord(
        id="test-job-1",
        spec_json="{}",
        status=JobStatus.QUEUED,
        progress=0.0,
        row_count=10,
        created_at="2026-10-06T00:00:00Z",
        updated_at="2026-10-06T00:00:00Z",
        artifact_dir=str(tmp_path / "artifacts"),
    )
    repo.create_job(record)

    fetched = repo.get_job("test-job-1")
    assert fetched is not None
    assert fetched.id == "test-job-1"
    assert fetched.status == JobStatus.QUEUED

    repo.update_progress("test-job-1", 0.5)
    updated = repo.get_job("test-job-1")
    assert updated.progress == 0.5

    repo.update_status("test-job-1", JobStatus.COMPLETED)
    completed = repo.get_job("test-job-1")
    assert completed.status == JobStatus.COMPLETED
    assert completed.completed_at is not None

def test_job_manager_execution(tmp_path):
    db_file = tmp_path / "test_manager.db"
    repo = JobRepository(db_path=db_file)
    manager = JobManager(repo=repo)

    spec = get_default_support_ticket_spec()
    spec.row_count = 10

    job_id = manager.submit_job(spec, is_preview=True, row_count=10)
    assert job_id is not None

    # Execute job synchronously
    manager.execute_job_sync(job_id)

    status_rec = repo.get_job(job_id)
    assert status_rec.status == JobStatus.COMPLETED
    assert status_rec.progress == 1.0

    art_dir = Path(status_rec.artifact_dir)
    assert (art_dir / "dataset.csv").exists()
    assert (art_dir / "dataset.json").exists()
    assert (art_dir / "manifest.json").exists()
    assert (art_dir / "report.json").exists()

def test_job_manager_cancellation(tmp_path):
    db_file = tmp_path / "test_cancel.db"
    repo = JobRepository(db_path=db_file)
    manager = JobManager(repo=repo)

    spec = get_default_support_ticket_spec()
    job_id = manager.submit_job(spec, is_preview=False, row_count=20)

    # Request cancellation before execution
    manager.cancel_job(job_id)

    manager.execute_job_sync(job_id)

    status_rec = repo.get_job(job_id)
    assert status_rec.status == JobStatus.CANCELLED
    art_dir = Path(status_rec.artifact_dir)
    # Cancelled job must not produce completed export artifacts
    assert not (art_dir / "dataset.csv").exists()

def test_api_jobs_full_flow():
    spec = get_default_support_ticket_spec()
    spec_dict = spec.model_dump(mode="json")

    # 1. Submit preview job
    post_resp = client.post(
        "/api/jobs",
        json={"spec": spec_dict, "is_preview": True, "row_count": 15},
    )
    assert post_resp.status_code == 202
    job_data = post_resp.json()
    job_id = job_data["id"]

    # 2. Synchronous test client executes background tasks inline, so check status
    get_resp = client.get(f"/api/jobs/{job_id}")
    assert get_resp.status_code == 200
    status_data = get_resp.json()
    assert status_data["status"] == "completed"
    assert status_data["has_artifacts"] is True

    # 3. Check preview endpoint
    prev_resp = client.get(f"/api/jobs/{job_id}/preview")
    assert prev_resp.status_code == 200
    rows = prev_resp.json()["rows"]
    assert len(rows) == 15
    assert "ticket_id" in rows[0]
    assert "message" in rows[0]

    # 4. Check report endpoint
    rep_resp = client.get(f"/api/jobs/{job_id}/report")
    assert rep_resp.status_code == 200
    report_json = rep_resp.json()
    assert report_json["is_valid"] is True
    assert report_json["total_rows"] == 15

    # 5. Check manifest endpoint
    man_resp = client.get(f"/api/jobs/{job_id}/manifest")
    assert man_resp.status_code == 200
    manifest_json = man_resp.json()
    assert manifest_json["dataset_metrics"]["requested_rows"] == 15

    # 6. Test CSV and JSON downloads
    csv_resp = client.get(f"/api/jobs/{job_id}/exports/csv")
    assert csv_resp.status_code == 200
    assert "text/csv" in csv_resp.headers["content-type"]
    assert "ticket_id,category,priority" in csv_resp.text

    json_resp = client.get(f"/api/jobs/{job_id}/exports/json")
    assert json_resp.status_code == 200
    assert "application/json" in json_resp.headers["content-type"]
    exported_data = json.loads(json_resp.text)
    assert len(exported_data) == 15

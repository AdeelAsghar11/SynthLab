import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import pandas as pd

from backend.specs.models import DatasetSpec
from backend.validation.validator import DatasetValidationReport
from backend.generation.text_enricher import EnrichmentMetrics

def sanitize_for_spreadsheet(val: Any) -> Any:
    """Neutralizes spreadsheet formula injection vulnerabilities in CSV cells."""
    if isinstance(val, str) and len(val) > 0:
        first_char = val[0]
        if first_char in ("=", "+", "-", "@", "\t", "\r"):
            return f"'{val}"
    return val

def export_dataset_csv(df: pd.DataFrame, output_path: Path, safe_mode: bool = True) -> None:
    """Exports DataFrame to CSV with optional spreadsheet formula injection sanitization."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if safe_mode:
        sanitized_df = df.map(sanitize_for_spreadsheet)
        sanitized_df.to_csv(output_path, index=False, encoding="utf-8")
    else:
        df.to_csv(output_path, index=False, encoding="utf-8")

def export_dataset_json(df: pd.DataFrame, output_path: Path) -> None:
    """Exports DataFrame to JSON records format."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # Serialize datetimes to ISO strings
    records = df.to_dict(orient="records")
    for r in records:
        for k, v in r.items():
            if isinstance(v, (datetime, pd.Timestamp)):
                r[k] = v.isoformat()
            elif pd.isna(v):
                r[k] = None

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

def export_manifest(
    spec: DatasetSpec,
    output_dir: Path,
    row_count: int,
    accepted_count: int,
    model_name: str,
    metrics: EnrichmentMetrics | None = None,
) -> Path:
    """Creates a comprehensive provenance manifest.json."""
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "manifest.json"

    spec_dict = spec.model_dump(mode="json")
    spec_bytes = json.dumps(spec_dict, sort_keys=True).encode("utf-8")
    spec_sha256 = hashlib.sha256(spec_bytes).hexdigest()

    manifest_data = {
        "manifest_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "specification": {
            "name": spec.name,
            "version": spec.spec_version,
            "sha256": spec_sha256,
            "generation_mode": spec.generation_mode,
            "seed": spec.seed,
            "field_count": len(spec.fields),
        },
        "dataset_metrics": {
            "requested_rows": row_count,
            "accepted_rows": accepted_count,
            "model_adapter": model_name,
        },
        "enrichment_metrics": metrics.model_dump() if metrics else None,
        "environment": {
            "local_only": True,
            "cloud_fallback": False,
            "synthetic_provenance": "visibly artificial fictional operational data",
        },
    }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    return manifest_path

def export_report(
    report: DatasetValidationReport,
    output_dir: Path,
) -> Path:
    """Writes validation quality report to report.json."""
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "report.json"

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report.model_dump(), f, indent=2)

    return report_path

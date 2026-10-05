from datetime import datetime, timezone
import httpx
from fastapi import APIRouter
from pydantic import BaseModel
from backend.config import settings

router = APIRouter(prefix="/api", tags=["health"])

class StorageHealth(BaseModel):
    status: str
    writable: bool
    db_path: str

class InferenceHealth(BaseModel):
    status: str
    provider: str
    base_url: str
    available_models: list[str]

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str
    storage: StorageHealth
    inference: InferenceHealth

@router.get("/health", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    # 1. Check storage directory
    storage_ok = True
    writable = False
    try:
        settings.db_path.parent.mkdir(parents=True, exist_ok=True)
        settings.artifacts_dir.mkdir(parents=True, exist_ok=True)
        # Test writability with a tiny temporary check
        test_file = settings.db_path.parent / ".write_test"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink(missing_ok=True)
        writable = True
    except Exception:
        storage_ok = False
        writable = False

    storage_info = StorageHealth(
        status="ok" if storage_ok else "error",
        writable=writable,
        db_path=str(settings.db_path),
    )

    # 2. Check local inference provider (Ollama)
    inference_status = "unavailable"
    models: list[str] = []
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            if resp.status_code == 200:
                inference_status = "connected"
                data = resp.json()
                models = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
    except Exception:
        inference_status = "offline"

    inference_info = InferenceHealth(
        status=inference_status,
        provider="ollama",
        base_url=settings.ollama_base_url,
        available_models=models,
    )

    return HealthResponse(
        status="ok",
        version=settings.version,
        timestamp=datetime.now(timezone.utc).isoformat(),
        storage=storage_info,
        inference=inference_info,
    )

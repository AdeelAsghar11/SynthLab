import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseModel):
    app_name: str = "SynthLab"
    version: str = "0.1.0"
    host: str = os.getenv("SYNTHLAB_HOST", "127.0.0.1")
    port: int = int(os.getenv("SYNTHLAB_PORT", "8000"))
    ollama_base_url: str = os.getenv("SYNTHLAB_OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    default_model: str = os.getenv("SYNTHLAB_DEFAULT_MODEL", "qwen2.5:7b")
    schema_generation_timeout_seconds: float = float(os.getenv("SYNTHLAB_SCHEMA_GENERATION_TIMEOUT_SECONDS", "90"))
    db_path: Path = Path(os.getenv("SYNTHLAB_DB_PATH", str(BASE_DIR / "backend" / "data" / "synthlab.db")))
    artifacts_dir: Path = Path(os.getenv("SYNTHLAB_ARTIFACTS_DIR", str(BASE_DIR / "backend" / "data" / "artifacts")))
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

settings = Settings()

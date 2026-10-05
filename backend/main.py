from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.api.health import router as health_router

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Local synthetic data studio for structured and LLM-enriched datasets.",
)

# CORS middleware for local frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health_router)

@app.get("/")
def root():
    return {
        "app": settings.app_name,
        "version": settings.version,
        "status": "online",
        "docs": "/docs",
        "health": "/api/health",
    }

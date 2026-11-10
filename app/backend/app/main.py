import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import Base, engine
from .migrations import run_additive_migrations
from .routers import (
    auth,
    career_chat,
    certificates,
    education,
    experience,
    guidance,
    job_preferences,
    portfolio,
    projects,
    public,
    skills,
)

logging.basicConfig(level=logging.INFO)
for noisy in ("httpx", "httpx2"):
    logging.getLogger(noisy).setLevel(logging.WARNING)

# Creates any tables that don't exist yet. It never alters existing tables, so
# column changes to an existing table need a migration (see README).
Base.metadata.create_all(bind=engine)
# Adds new nullable columns to existing tables; never drops or rewrites data.
run_additive_migrations(engine)

app = FastAPI(title="Projectory API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_origin_regex=settings.allowed_origin_regex or None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for module in (
    auth, portfolio, education, skills, experience, certificates, job_preferences, projects, guidance, career_chat, public,
):
    app.include_router(module.router)

if settings.storage_backend == "local":
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")


@app.get("/health")
def health():
    return {"status": "ok"}

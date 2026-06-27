"""Main FastAPI application."""
import asyncio
import os
import sys

from fastapi import FastAPI

from app.core.config import settings
from app.core.cors import setup_cors
from app.core.errors import (
    QuranNotesException,
    quran_notes_exception_handler,
    general_exception_handler,
)
from app.core.logging import setup_logging
from app.core.request_id import RequestIdMiddleware
from app.routers import languages, sessions, notes, highlights
from app.services.processing.sweeper import sweeper_loop

# Setup logging
setup_logging()

# Create FastAPI app
app = FastAPI(
    title="Quran Notes API",
    description="Backend API for Quran Notes mobile application",
    version="1.0.0",
    docs_url="/docs" if settings.env == "dev" else None,
    redoc_url="/redoc" if settings.env == "dev" else None,
)

# Middleware
app.add_middleware(RequestIdMiddleware)
setup_cors(app)

# Register exception handlers
app.add_exception_handler(QuranNotesException, quran_notes_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Register routers
app.include_router(languages.router)
app.include_router(sessions.router)
app.include_router(notes.router)
app.include_router(highlights.router)

@app.on_event("startup")
async def _start_sweeper() -> None:
    if not getattr(settings, "sweeper_enabled", True):
        return
    # Avoid running the infinite-loop sweeper during pytest runs (it can keep background
    # tasks alive across tests if clients aren't closed).
    if os.environ.get("PYTEST_CURRENT_TEST") or "pytest" in sys.modules:
        return
    # Run as a background asyncio task inside the API process.
    app.state.sweeper_task = asyncio.create_task(sweeper_loop())


@app.on_event("shutdown")
async def _stop_sweeper() -> None:
    task = getattr(app.state, "sweeper_task", None)
    if task:
        task.cancel()
        try:
            await task
        except Exception:
            pass


# Health check endpoint
@app.get("/v1/health")
async def health_check():
    """Health check endpoint with deployment metadata."""
    return {
        "status": "healthy",
        "environment": settings.env,
        "storage_backend": getattr(settings, "storage_backend", "local"),
        "version": "1.0.0",
        "git_sha": os.environ.get("GIT_SHA"),
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Quran Notes API",
        "version": "1.0.0",
        "docs": "/docs" if settings.env == "dev" else None,
    }


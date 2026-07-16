"""
Text Simplification Backend — FastAPI application entry point.

Run locally:
    uvicorn main:app --reload --port 8000

The service is configured through environment variables; see .env.example.
"""

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="Text Simplification API",
    description=(
        "FastAPI backend for the Android Text Simplification application. "
        "POST text and a target Flesch–Kincaid grade level to receive a simplified version."
    ),
    version="1.0.0",
)

# ── CORS ───────────────────────────────────────────────────────────────────────
# Allow all origins for development / emulator access.
# Restrict this in production.
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ─────────────────────────────────────────────────────────────────────
app.include_router(router)


@app.get("/health")
async def health() -> dict:
    """Simple health-check endpoint."""
    return {"status": "ok"}

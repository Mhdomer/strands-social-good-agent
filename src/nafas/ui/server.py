"""Web UI server for Nafas (نَفَس) Climate-Respiratory AI Guardian.

Serves an interactive single-page dashboard with real-time multi-agent chat,
live WBGT heat stress calculations, drug safety verification, and cooling shelter routing.
"""

import json
import os
from pathlib import Path
from typing import Any
import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, Response
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles

from nafas.config import APP_NAME, APP_ARABIC_NAME, APP_TAGLINE, DEFAULT_BEDROCK_REGION, DEFAULT_BEDROCK_MODEL_ID
from nafas.tools.environmental import get_environmental_hazard_index
from nafas.tools.medication import verify_respiratory_medication_safety
from nafas.tools.shelter import find_cooling_or_nebulizer_shelter
from nafas.agents.supervisor import NafasOrchestrator
from nafas.session.patient_memory import PatientSessionStore, PatientRespiratoryProfile
from nafas.runtime.bedrock_config import create_bedrock_model


STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# Shared orchestrator singleton
_ORCHESTRATOR = None
_STORE = PatientSessionStore(base_dir=".nafas_sessions")


def get_orchestrator(dialect: str = "saudi"):
    global _ORCHESTRATOR
    if _ORCHESTRATOR is None:
        try:
            model = create_bedrock_model()
        except Exception:
            model = None
        _ORCHESTRATOR = NafasOrchestrator(model=model, dialect=dialect)
    return _ORCHESTRATOR


async def index(request: Request) -> Response:
    """Serve main single-page dashboard."""
    html_file = STATIC_DIR / "index.html"
    if html_file.exists():
        with open(html_file, "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    return HTMLResponse("<h1>Nafas UI Loading...</h1>")


async def api_status(request: Request) -> JSONResponse:
    """System health check and Bedrock connectivity status."""
    return JSONResponse({
        "app": APP_NAME,
        "arabic_name": APP_ARABIC_NAME,
        "tagline": APP_TAGLINE,
        "bedrock_model": DEFAULT_BEDROCK_MODEL_ID,
        "bedrock_region": DEFAULT_BEDROCK_REGION,
        "status": "ready",
    })


import asyncio

_LOCK = asyncio.Lock()

async def api_chat(request: Request) -> JSONResponse:
    """Handle interactive multi-agent chat requests."""
    try:
        body = await request.json()
    except Exception:
        body = {}

    query = body.get("query", "").strip()
    session_id = body.get("session_id", "web_user")
    dialect = body.get("dialect", "saudi")

    if not query:
        return JSONResponse({"error": "Empty query"}, status_code=400)

    # Format baseline memory
    baseline_prompt = _STORE.format_profile_for_prompt(session_id)
    orchestrator = get_orchestrator(dialect=dialect)
    
    async with _LOCK:
        result = orchestrator.process_query(query, patient_baseline_prompt=baseline_prompt)

    return JSONResponse(result)


async def api_hazard(request: Request) -> JSONResponse:
    """Calculate WBGT heat index and air quality."""
    city = request.query_params.get("city", "Riyadh")
    sun = request.query_params.get("sun", "true").lower() == "true"
    result = get_environmental_hazard_index(city=city, direct_sunlight=sun)
    return JSONResponse(result)


async def api_medication(request: Request) -> JSONResponse:
    """Verify medication safety and check contraindications."""
    drug = request.query_params.get("drug", "Ventolin")
    asthma = request.query_params.get("asthma", "true").lower() == "true"
    result = verify_respiratory_medication_safety(drug_name=drug, patient_has_asthma=asthma)
    return JSONResponse(result)


async def api_shelters(request: Request) -> JSONResponse:
    """Locate nearest cooling shelter or nebulizer clinic."""
    city = request.query_params.get("city", "Riyadh")
    district = request.query_params.get("district")
    nebulizer = request.query_params.get("nebulizer", "false").lower() == "true"
    result = find_cooling_or_nebulizer_shelter(city=city, district=district, need_nebulizer=nebulizer)
    return JSONResponse(result)


routes = [
    Route("/", endpoint=index),
    Route("/api/status", endpoint=api_status),
    Route("/api/chat", endpoint=api_chat, methods=["POST"]),
    Route("/api/hazard", endpoint=api_hazard),
    Route("/api/medication", endpoint=api_medication),
    Route("/api/shelters", endpoint=api_shelters),
]

app = Starlette(routes=routes)


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run UI server with uvicorn."""
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    run_server()

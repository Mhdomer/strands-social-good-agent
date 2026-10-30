"""AWS Lambda entry point for Nafas (نَفَس).

Compatible with Amazon Bedrock AgentCore Runtime, Amazon API Gateway,
and direct serverless container invocation with scale-to-zero economics.
"""

import json
import os
import time
from typing import Any
from nafas.config import APP_NAME, APP_TAGLINE
from nafas.session.patient_memory import PatientSessionStore, PatientRespiratoryProfile
from nafas.agents.supervisor import NafasOrchestrator
from nafas.runtime.bedrock_config import create_bedrock_model


# Lazy singleton initialization to minimize Lambda cold-start latency
_ORCHESTRATOR: NafasOrchestrator | None = None
_SESSION_STORE: PatientSessionStore | None = None


def get_orchestrator(dialect: str = "saudi") -> NafasOrchestrator:
    """Retrieve or initialize the cached singleton orchestrator."""
    global _ORCHESTRATOR
    if _ORCHESTRATOR is None:
        # Check if AWS credentials exist; otherwise use None for fallback
        try:
            model = create_bedrock_model()
        except Exception:
            model = None
        _ORCHESTRATOR = NafasOrchestrator(model=model, dialect=dialect)
    return _ORCHESTRATOR


def get_session_store() -> PatientSessionStore:
    """Retrieve or initialize the cached session store."""
    global _SESSION_STORE
    if _SESSION_STORE is None:
        storage_dir = os.getenv("SESSION_STORAGE_DIR", "/tmp/nafas_sessions")
        _SESSION_STORE = PatientSessionStore(base_dir=storage_dir)
    return _SESSION_STORE


def lambda_handler(event: dict[str, Any], context: Any = None) -> dict[str, Any]:
    """Handle incoming AWS Lambda invocation from API Gateway or Bedrock AgentCore."""
    start_time = time.time()

    # Parse request body from API Gateway proxy or direct JSON
    body = event
    if "body" in event:
        try:
            body = json.loads(event["body"]) if isinstance(event["body"], str) else event["body"]
        except Exception:
            body = {}

    query = body.get("query", "").strip()
    session_id = body.get("session_id", "anonymous_session")
    dialect = body.get("dialect", "saudi")
    patient_data = body.get("patient_profile")

    if not query:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"error": "Missing required 'query' field."}),
        }

    # Retrieve or update persistent patient respiratory profile
    store = get_session_store()
    if patient_data and isinstance(patient_data, dict):
        profile = PatientRespiratoryProfile(
            patient_id=session_id,
            name=patient_data.get("name", "Anonymous Patient"),
            age=int(patient_data.get("age", 30)),
            primary_condition=patient_data.get("primary_condition", "Asthma"),
            known_allergies=patient_data.get("known_allergies", ["Aspirin"]),
            prescribed_inhalers=patient_data.get("prescribed_inhalers", ["Ventolin"]),
            notes=patient_data.get("notes", []),
        )
        store.save_profile(profile)

    baseline_prompt = store.format_profile_for_prompt(session_id)

    # Process query through orchestrator
    orchestrator = get_orchestrator(dialect=dialect)
    result = orchestrator.process_query(query, patient_baseline_prompt=baseline_prompt)

    latency_ms = round((time.time() - start_time) * 1000, 2)

    response_payload = {
        "app": APP_NAME,
        "tagline": APP_TAGLINE,
        "session_id": session_id,
        "status": result["status"],
        "triaged_by": result["triaged_by"],
        "red_flags_detected": result["red_flags"],
        "response": result["response"],
        "latency_ms": latency_ms,
    }

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
        "body": json.dumps(response_payload, ensure_ascii=False),
    }

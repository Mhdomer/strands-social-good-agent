"""Model configuration and runtime factory for Amazon Bedrock and offline evals.

Supports Amazon Bedrock Claude 3.5 Sonnet / Haiku for production,
and deterministic mock models for CI/CD trajectory evaluations.
"""

from typing import Any
import os
from strands.models.bedrock import BedrockModel
from strands.models.model import Model
from nafas.config import DEFAULT_BEDROCK_MODEL_ID, DEFAULT_BEDROCK_REGION, FAST_BEDROCK_MODEL_ID


def create_bedrock_model(
    model_id: str | None = None,
    region_name: str | None = None,
    **kwargs: Any,
) -> BedrockModel:
    """Instantiate Amazon Bedrock foundation model provider."""
    mid = model_id or os.getenv("BEDROCK_MODEL_ID", DEFAULT_BEDROCK_MODEL_ID)
    rname = region_name or os.getenv("AWS_DEFAULT_REGION", DEFAULT_BEDROCK_REGION)
    return BedrockModel(model_id=mid, region_name=rname, **kwargs)


def create_fast_bedrock_model(
    region_name: str | None = None,
    **kwargs: Any,
) -> BedrockModel:
    """Instantiate fast Amazon Bedrock model provider for low-latency triage."""
    rname = region_name or os.getenv("AWS_DEFAULT_REGION", DEFAULT_BEDROCK_REGION)
    return BedrockModel(model_id=FAST_BEDROCK_MODEL_ID, region_name=rname, **kwargs)

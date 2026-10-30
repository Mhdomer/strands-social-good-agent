"""Nafas runtime package exporting AWS Lambda handler and Bedrock model configurations."""

from nafas.runtime.lambda_handler import lambda_handler
from nafas.runtime.bedrock_config import create_bedrock_model, create_fast_bedrock_model

__all__ = ["lambda_handler", "create_bedrock_model", "create_fast_bedrock_model"]

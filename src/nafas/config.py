"""Configuration and constants for Nafas (نَفَس).

Maintains regional emergency hotlines, WBGT heat thresholds,
and clinical contraindication matrices.
"""

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class EmergencyHotlines:
    """Regional emergency medical dispatch numbers."""
    SAUDI_AMBULANCE: str = "997"
    SAUDI_CIVIL_DEFENSE: str = "998"
    SAUDI_UNIFIED_EMERGENCY: str = "911"
    EGYPT_AMBULANCE: str = "123"
    EGYPT_CIVIL_PROTECTION: str = "180"


@dataclass(frozen=True)
class WBGTThresholds:
    """OSHA and ISO 7243 Wet-Bulb Globe Temperature heat stress tiers (in Celsius)."""
    LOW_RISK_MAX: float = 25.6        # Standard work-rest schedule
    MODERATE_RISK_MAX: float = 29.4   # 45 min work / 15 min rest, 0.5L water/hr
    HIGH_RISK_MAX: float = 31.0       # 30 min work / 30 min rest, 0.75L water/hr
    VERY_HIGH_RISK_MAX: float = 32.2  # 15 min work / 45 min rest, 1.0L water/hr
    # WBGT above 32.2C mandates suspension of heavy physical outdoor manual labor


from dotenv import load_dotenv
load_dotenv()

# Bedrock defaults
DEFAULT_BEDROCK_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
DEFAULT_BEDROCK_MODEL_ID = os.getenv(
    "BEDROCK_MODEL_ID",
    "amazon.nova-pro-v1:0",
)
FAST_BEDROCK_MODEL_ID = os.getenv(
    "BEDROCK_FAST_MODEL_ID",
    "amazon.nova-lite-v1:0",
)

# Application metadata
APP_NAME = "Nafas"
APP_ARABIC_NAME = "نَفَس"
APP_TAGLINE = "Climate-Respiratory & Heat Stress AI Guardian"

"""Nafas tools package exporting domain tools for climate, medication, and shelter."""

from nafas.tools.environmental import get_environmental_hazard_index
from nafas.tools.medication import verify_respiratory_medication_safety
from nafas.tools.shelter import find_cooling_or_nebulizer_shelter

__all__ = [
    "get_environmental_hazard_index",
    "verify_respiratory_medication_safety",
    "find_cooling_or_nebulizer_shelter",
]

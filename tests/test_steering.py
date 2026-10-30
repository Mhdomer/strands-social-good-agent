"""Unit tests for Nafas clinical guardrails, emergency detection, and dialect steering."""

import pytest
from nafas.steering.clinical_guardrails import (
    check_red_flag_emergency,
    RedFlagCrisisIndicators,
    CLINICAL_SYSTEM_PROMPT_INVARIANTS,
)
from nafas.steering.dialect_prompts import get_dialect_steering


class TestClinicalGuardrails:
    """Test suite for clinical boundary invariants and emergency escalation."""

    def test_emergency_detection_cyanosis(self):
        """Verify cyanosis trigger routes to emergency dispatch immediately."""
        query = "My son has blue lips and is struggling for air."
        result = check_red_flag_emergency(query)
        assert result["is_emergency"] is True
        assert RedFlagCrisisIndicators.CYANOSIS in result["matched_red_flags"]
        assert "997" in result["emergency_dispatch_message"]
        assert "123" in result["emergency_dispatch_message"]

    def test_emergency_detection_chest_retractions(self):
        """Verify chest and rib retractions trigger emergency dispatch."""
        query = "The worker has severe ribs sucking in while breathing."
        result = check_red_flag_emergency(query)
        assert result["is_emergency"] is True
        assert RedFlagCrisisIndicators.CHEST_RETRACTIONS in result["matched_red_flags"]

    def test_emergency_detection_arabic_dialect(self):
        """Verify Arabic colloquial emergency phrases are captured."""
        query = "الولد شفايفه زرقاء ومش عارف يكمل جملة على بعضها"
        result = check_red_flag_emergency(query)
        assert result["is_emergency"] is True
        assert len(result["matched_red_flags"]) >= 1

    def test_non_emergency_routine_query(self):
        """Verify routine environmental or medication questions do not trigger false alarm."""
        query = "How often should I use Pulmicort every day?"
        result = check_red_flag_emergency(query)
        assert result["is_emergency"] is False
        assert len(result["matched_red_flags"]) == 0
        assert result["emergency_dispatch_message"] is None

    def test_clinical_invariants_content(self):
        """Verify system prompt contains non-negotiable medical rules."""
        prompt = CLINICAL_SYSTEM_PROMPT_INVARIANTS
        assert "ZERO UNPRESCRIBED DIAGNOSES" in prompt
        assert "ZERO DOSE ALTERATIONS" in prompt
        assert "LETHAL DRUG CONTRAINDICATIONS" in prompt
        assert "Aspirin" in prompt
        assert "Paracetamol" in prompt


class TestDialectSteering:
    """Test suite for linguistic and cultural localization."""

    def test_saudi_dialect_steering(self):
        """Verify Saudi dialect steering incorporates cultural warmth and 937/997."""
        prompt = get_dialect_steering("saudi")
        assert "Saudi" in prompt or "سعودي" in prompt
        assert "997" in prompt
        assert "937" in prompt

    def test_egyptian_dialect_steering(self):
        """Verify Egyptian dialect steering incorporates colloquial warmth and 123."""
        prompt = get_dialect_steering("egyptian")
        assert "Egyptian" in prompt or "مصر" in prompt
        assert "123" in prompt

    def test_migrant_worker_steering(self):
        """Verify worker English steering targets 6th-grade reading level."""
        prompt = get_dialect_steering("english_worker")
        assert "6th-grade" in prompt
        assert "short sentences" in prompt

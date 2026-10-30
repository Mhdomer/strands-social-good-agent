"""Unit tests for patient respiratory profile and session store memory."""

import tempfile
import pytest
from nafas.session.patient_memory import (
    PatientRespiratoryProfile,
    PatientSessionStore,
)


class TestPatientSessionMemory:
    """Test suite for persistent patient respiratory baseline across turns."""

    def test_profile_serialization(self):
        """Verify PatientRespiratoryProfile converts cleanly to and from dict."""
        profile = PatientRespiratoryProfile(
            patient_id="patient_test_01",
            name="Zaid",
            age=8,
            primary_condition="Allergic Asthma",
            known_allergies=["Aspirin", "Ibuprofen"],
            prescribed_inhalers=["Ventolin", "Pulmicort"],
            emergency_contact="Father (+966-500000000)",
            notes=["Hospitalized last year during Khamaseen dust storm"],
        )
        data = profile.to_dict()
        assert data["age"] == 8
        assert "Aspirin" in data["known_allergies"]

        restored = PatientRespiratoryProfile.from_dict(data)
        assert restored.patient_id == "patient_test_01"
        assert restored.primary_condition == "Allergic Asthma"
        assert len(restored.notes) == 1

    def test_session_store_save_and_retrieve(self):
        """Verify PatientSessionStore saves to disk and restores across instances."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = PatientSessionStore(base_dir=tmpdir)
            profile = PatientRespiratoryProfile(
                patient_id="patient_100",
                name="Fatima",
                age=65,
                primary_condition="COPD & Chronic Bronchitis",
                known_allergies=["Penicillin", "NSAIDs"],
            )
            store.save_profile(profile)

            # Reload in new store instance targeting same directory
            store_2 = PatientSessionStore(base_dir=tmpdir)
            loaded = store_2.get_profile("patient_100")
            assert loaded is not None
            assert loaded.name == "Fatima"
            assert loaded.primary_condition == "COPD & Chronic Bronchitis"
            assert "NSAIDs" in loaded.known_allergies

    def test_get_or_create_profile(self):
        """Verify get_or_create initializes defaults if session is new."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = PatientSessionStore(base_dir=tmpdir)
            p = store.get_or_create_profile("new_unknown_patient")
            assert p.patient_id == "new_unknown_patient"
            assert p.primary_condition == "Asthma"

    def test_format_profile_for_prompt(self):
        """Verify clinical baseline markdown block format for LLM injection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = PatientSessionStore(base_dir=tmpdir)
            profile = PatientRespiratoryProfile(
                patient_id="p_prompt_test",
                age=42,
                primary_condition="Severe Persistent Asthma",
                prescribed_inhalers=["Ventolin", "Symbicort"],
                known_allergies=["Aspirin"],
            )
            store.save_profile(profile)

            prompt_text = store.format_profile_for_prompt("p_prompt_test")
            assert "ACTIVE PATIENT BASELINE" in prompt_text
            assert "42 years old" in prompt_text
            assert "Severe Persistent Asthma" in prompt_text
            assert "Aspirin" in prompt_text
            assert "Symbicort" in prompt_text

    def test_create_strands_file_session_manager(self):
        """Verify official Strands FileSessionManager is created properly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = PatientSessionStore(base_dir=tmpdir)
            sm = store.create_strands_session_manager("session_abc")
            assert sm is not None
            assert hasattr(sm, "create_message")

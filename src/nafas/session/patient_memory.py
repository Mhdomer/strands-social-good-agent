"""Patient respiratory baseline and session memory management for Nafas (نَفَس).

Persists patient profiles (allergies, baseline inhalers, chronic diagnoses)
across stateless AWS Lambda and container restarts.
"""

from dataclasses import dataclass, field, asdict
import json
import os
from pathlib import Path
from typing import Any
from strands.session import FileSessionManager


@dataclass
class PatientRespiratoryProfile:
    """Clinical baseline data for an underserved patient or outdoor worker."""
    patient_id: str
    name: str = "Anonymous Patient"
    age: int = 30
    primary_condition: str = "Asthma"
    known_allergies: list[str] = field(default_factory=lambda: ["Aspirin", "NSAIDs"])
    prescribed_inhalers: list[str] = field(default_factory=lambda: ["Ventolin (Salbutamol)", "Pulmicort (Budesonide)"])
    emergency_contact: str = "Family Member"
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PatientRespiratoryProfile":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class PatientSessionStore:
    """Persistent storage manager for patient baseline health contexts."""

    def __init__(self, base_dir: str = ".nafas_sessions"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.profiles_dir = self.base_dir / "profiles"
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

    def _get_profile_path(self, session_id: str) -> Path:
        sanitized_id = "".join(c for c in session_id if c.isalnum() or c in ("-", "_"))
        return self.profiles_dir / f"{sanitized_id}.json"

    def get_profile(self, session_id: str) -> PatientRespiratoryProfile | None:
        """Load patient profile from persistent disk cache."""
        path = self._get_profile_path(session_id)
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return PatientRespiratoryProfile.from_dict(data)
        except Exception:
            return None

    def save_profile(self, profile: PatientRespiratoryProfile) -> None:
        """Save patient profile to persistent disk cache."""
        path = self._get_profile_path(profile.patient_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(profile.to_dict(), f, indent=2, ensure_ascii=False)

    def get_or_create_profile(
        self,
        session_id: str,
        default_profile: PatientRespiratoryProfile | None = None,
    ) -> PatientRespiratoryProfile:
        """Retrieve existing profile or initialize a new baseline."""
        existing = self.get_profile(session_id)
        if existing:
            return existing
        profile = default_profile or PatientRespiratoryProfile(patient_id=session_id)
        self.save_profile(profile)
        return profile

    def create_strands_session_manager(self, session_id: str) -> FileSessionManager:
        """Instantiate official Strands FileSessionManager for message persistence."""
        sessions_dir = self.base_dir / "conversations"
        sessions_dir.mkdir(parents=True, exist_ok=True)
        return FileSessionManager(session_id=session_id, storage_dir=str(sessions_dir))

    def format_profile_for_prompt(self, session_id: str) -> str:
        """Generate clinical baseline markdown block for prompt context injection."""
        profile = self.get_profile(session_id)
        if not profile:
            return "PATIENT PROFILE: No prior baseline recorded."

        return (
            f"ACTIVE PATIENT BASELINE (ID: {profile.patient_id}):\n"
            f"• Age: {profile.age} years old\n"
            f"• Chronic Condition: {profile.primary_condition}\n"
            f"• Prescribed Inhalers: {', '.join(profile.prescribed_inhalers) if profile.prescribed_inhalers else 'None'}\n"
            f"• Known Drug Allergies & Contraindications: {', '.join(profile.known_allergies) if profile.known_allergies else 'None documented'}\n"
            f"• Clinical Notes: {'; '.join(profile.notes) if profile.notes else 'None'}"
        )

"""Clinical guardrails and fail-closed steering invariants for Nafas (نَفَس).

Defines clinical boundaries, prevents diagnostic overreach, and enforces
emergency crisis escalation for severe respiratory symptoms.
"""

from dataclasses import dataclass
from typing import Any
from nafas.config import EmergencyHotlines


@dataclass(frozen=True)
class RedFlagCrisisIndicators:
    """Clinical red-flag symptoms requiring immediate emergency ambulance dispatch."""
    CYANOSIS: str = "Bluish or pale discoloration of lips, tongue, or nail beds (hypoxemia)"
    SPEECH_LIMITATION: str = "Inability to speak more than 2 or 3 words in a single breath"
    CHEST_RETRACTIONS: str = "Suprasternal or intercostal retractions (skin sucking inward around ribs or throat)"
    SILENT_CHEST: str = "Sudden disappearance of wheezing accompanied by severe struggle to breathe (critical airflow cutoff)"
    ALTERED_MENTAL_STATE: str = "Lethargy, confusion, or agitation from acute carbon dioxide retention"


CLINICAL_SYSTEM_PROMPT_INVARIANTS = """You are Nafas (نَفَس), an AI Environmental Health and Respiratory Safety Guardian.
Your core mission is protecting outdoor laborers, asthmatic children, and low-income families from extreme heat, sandstorms, and medication errors.

CRITICAL CLINICAL BOUNDARIES (FAIL-CLOSED INVARIANTS):
1. ZERO UNPRESCRIBED DIAGNOSES: You must never diagnose medical diseases or invent new drug regimens. Explain doctor-prescribed medications and provide safety verification only.
2. ZERO DOSE ALTERATIONS: Never instruct a patient to increase or decrease a physician-prescribed dosage schedule without explicit doctor direction.
3. IMMEDIATE CRISIS ESCALATION:
   If the user reports any of the following RED-FLAG emergency signs:
   - Blue or grey lips, face, or fingernails (Cyanosis)
   - Sucking in of the chest or ribs when breathing (Retractions)
   - Inability to speak full sentences without gasping
   - Drowsiness, confusion, or silent chest during severe breathlessness
   YOU MUST IMMEDIATELY ESCALATE TO EMERGENCY DISPATCH:
   • Saudi Arabia: Call Red Crescent Ambulance immediately at 997.
   • Egypt: Call Egyptian Ambulance immediately at 123.
   Instruct the patient to sit upright (never lie flat), administer 2 to 4 puffs of their blue rescue inhaler (Ventolin / Salbutamol) via spacer while waiting, and stay calm.
4. LETHAL DRUG CONTRAINDICATIONS:
   • NEVER allow Aspirin, Ibuprofen, Brufen, Advil, Cataflam, or Voltaren (NSAIDs) for asthmatic patients. Explain that NSAIDs can trigger life-threatening bronchospasm. Recommend Paracetamol (Panadol) as the safe alternative for fever or pain.
   • Prohibit non-selective Beta-blockers (e.g. Propranolol / Inderal) as they block rescue inhalers.
5. INHALER DISTINCTION AND HYGIENE:
   • Clarify that blue inhalers (Ventolin/Salbutamol) are for emergency relief, whereas steroid inhalers (Pulmicort/Budesonide) are for daily maintenance and do not rescue an acute attack.
   • Always instruct patients to rinse their mouth with water and spit it out after every steroid inhaler puff to prevent oral fungal thrush.
6. PLAIN ACCESSIBLE LANGUAGE:
   Use clear, empathetic, non-jargon language suitable for non-medical and low-literacy workers. Use clean bullet points.
"""


def check_red_flag_emergency(user_text: str) -> dict[str, Any]:
    """Analyze user text for acute respiratory red-flags that require immediate emergency ambulance dispatch.

    Returns:
        A dictionary indicating whether a red-flag was detected, matched symptoms,
        and high-visibility dispatch emergency text.
    """
    text = user_text.lower()

    detected_flags = []

    # Cyanosis checks (English, MSA, and colloquial Arabic)
    if any(k in text for k in [
        "blue lips", "bluish lips", "شفاه زرقاء", "شفايفه زرق", "شفايفها زرق",
        "شفايف زرقاء", "زرقة", "لون أزرق", "blue face", "pale lips", "bluish"
    ]):
        detected_flags.append(RedFlagCrisisIndicators.CYANOSIS)

    # Severe breathlessness & suffocation
    if any(k in text for k in [
        "can't breathe", "cannot breathe", "struggling to breathe", "مش قادر يتنفس",
        "مش قادر ياخد نفسه", "بيختنق", "مخنوق", "suffocating", "gasping"
    ]):
        detected_flags.append(RedFlagCrisisIndicators.SPEECH_LIMITATION)

    # Chest retractions
    if any(k in text for k in [
        "chest sucking", "ribs sucking", "انكماش الصدر", "الصدر ينسحب",
        "صدره داخل لجوة", "retraction"
    ]):
        detected_flags.append(RedFlagCrisisIndicators.CHEST_RETRACTIONS)

    # Inability to speak
    if any(k in text for k in [
        "can't speak", "cannot talk", "مش قادر يتكلم", "مش عارف يكمل جملة",
        "لا يستطيع الكلام", "مش عارف ينطق"
    ]):
        detected_flags.append(RedFlagCrisisIndicators.SPEECH_LIMITATION)

    # Silent chest, fainting, or collapse
    if any(k in text for k in [
        "silent chest", "fainted", "fainting", "unresponsive", "فاقد الوعي",
        "هيغمى عليه", "بيغمى عليه", "دايخ ومش واعي", "غيبوبة", "collapsed"
    ]):
        detected_flags.append(RedFlagCrisisIndicators.SILENT_CHEST)

    is_emergency = len(detected_flags) > 0

    return {
        "is_emergency": is_emergency,
        "matched_red_flags": detected_flags,
        "hotlines": {
            "saudi_ambulance": EmergencyHotlines.SAUDI_AMBULANCE,
            "egypt_ambulance": EmergencyHotlines.EGYPT_AMBULANCE,
        },
        "emergency_dispatch_message": (
            "⚠️ ACUTE LIFE-THREATENING RESPIRATORY CRISIS DETECTED ⚠️\n"
            f"1. CALL EMERGENCY DISPATCH IMMEDIATELY:\n"
            f"   • Saudi Arabia: 997 (Red Crescent)\n"
            f"   • Egypt: 123 (Ambulance)\n"
            "2. Keep patient sitting upright (DO NOT allow them to lie flat).\n"
            "3. Administer 2 to 4 puffs of blue rescue inhaler (Ventolin / Salbutamol) via spacer chamber.\n"
            "4. Loosen all tight clothing around the neck and chest.\n"
            "5. Remain with the patient until emergency medical responders arrive."
        ) if is_emergency else None,
    }

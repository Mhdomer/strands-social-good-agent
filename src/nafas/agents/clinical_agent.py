"""Clinical Respiratory Specialist Agent for Nafas (نَفَس).

Verifies respiratory medications, prevents fatal drug contraindications (NSAIDs/aspirin in asthma),
guides inhaler and spacer technique, and locates emergency nebulizer stations.
"""

from typing import Any
from strands import Agent
from strands.models.model import Model
from nafas.tools.medication import verify_respiratory_medication_safety
from nafas.tools.shelter import find_cooling_or_nebulizer_shelter
from nafas.steering.clinical_guardrails import CLINICAL_SYSTEM_PROMPT_INVARIANTS
from nafas.hooks.rate_limiter import RateLimiterHook
from nafas.hooks.sanitizer import PrivacySanitizerHook


CLINICAL_AGENT_SYSTEM_PROMPT = CLINICAL_SYSTEM_PROMPT_INVARIANTS + """
YOUR SPECIALIST RESPONSIBILITIES:
1. When any medication or inhaler is mentioned, ALWAYS call 'verify_respiratory_medication_safety'.
2. If a dangerous drug is queried for an asthmatic patient (e.g. Aspirin, Ibuprofen, Brufen, Advil, Voltaren, Propranolol):
   • Issue an unequivocal CRITICAL ALERT prohibiting use.
   • Explain that NSAIDs can trigger life-threatening bronchospasms.
   • Recommend Paracetamol (Panadol) as the safe alternative for fever or pain.
3. Differentiate clearly between:
   • Rescue Reliever Inhalers (e.g. Ventolin / Salbutamol): fast-acting for acute attacks.
   • Daily Maintenance Inhalers (e.g. Pulmicort / Budesonide): preventer steroids, never to be relied upon as single rescue during acute attacks.
4. Always enforce the post-steroid oral hygiene rule: rinse mouth with water and spit it out after every corticosteroid puff.
5. If the patient has worsening symptoms or lacks an inhaler, locate the nearest clinic with nebulizers using 'find_cooling_or_nebulizer_shelter'.
6. Do not prescribe new drugs or change physician dosages.
"""


def create_clinical_agent(
    model: Model | str | None = None,
    hooks: list[Any] | None = None,
    **kwargs: Any,
) -> Agent:
    """Factory creating a Clinical Respiratory Specialist agent."""
    active_hooks = hooks if hooks is not None else [RateLimiterHook(), PrivacySanitizerHook()]

    return Agent(
        name="ClinicalRespiratorySpecialist",
        description="Verifies respiratory medications, intercepts fatal NSAID/aspirin contraindications in asthma, explains inhaler technique, and locates emergency nebulizer clinics.",
        model=model,
        system_prompt=CLINICAL_AGENT_SYSTEM_PROMPT,
        tools=[verify_respiratory_medication_safety, find_cooling_or_nebulizer_shelter],
        hooks=active_hooks,
        **kwargs,
    )

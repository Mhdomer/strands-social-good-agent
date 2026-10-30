"""Safety Verification Auditor Agent for Nafas (نَفَس).

Independently audits agent responses against clinical invariants, verifying
emergency hotline numbers, zero unauthorized prescriptions, and contraindication flags.
"""

from typing import Any
from strands import Agent
from strands.models.model import Model
from nafas.steering.clinical_guardrails import CLINICAL_SYSTEM_PROMPT_INVARIANTS


AUDIT_AGENT_SYSTEM_PROMPT = CLINICAL_SYSTEM_PROMPT_INVARIANTS + """
YOUR AUDITOR RESPONSIBILITIES:
1. You review proposed guidance generated for vulnerable patients and outdoor laborers.
2. Verify that:
   • No unprescribed drug regimens were recommended.
   • Aspirin or NSAIDs are NEVER approved for asthmatic patients (must recommend Paracetamol).
   • Emergency cases (cyanosis, severe breathlessness) include official dispatch numbers (Saudi 997, Egypt 123).
   • Maintenance steroids include the mandatory mouth rinse instruction.
3. If the advice is safe and accurate, output:
   "VERIFICATION: PASSED" followed by any critical safety reminders.
4. If a safety boundary was violated, output:
   "VERIFICATION: FAILED" with the required clinical correction.
"""


def create_audit_agent(
    model: Model | str | None = None,
    **kwargs: Any,
) -> Agent:
    """Factory creating a Safety Verification Auditor agent."""
    return Agent(
        name="SafetyAuditor",
        description="Audits generated responses against clinical safety invariants, ensuring zero contraindicated drugs and correct emergency numbers.",
        model=model,
        system_prompt=AUDIT_AGENT_SYSTEM_PROMPT,
        tools=[],
        **kwargs,
    )

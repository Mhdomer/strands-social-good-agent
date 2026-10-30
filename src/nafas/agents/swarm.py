"""Collaborative Multi-Agent Swarm for Nafas (نَفَس).

Implements autonomous handoffs and shared working memory across
Triage, Climate, Clinical, and Safety Auditor agents using the Strands Swarm primitive.
"""

from typing import Any
from strands import Agent
from strands.multiagent.swarm import Swarm
from strands.session import SessionManager
from strands.models.model import Model
from nafas.agents.climate_agent import create_climate_agent
from nafas.agents.clinical_agent import create_clinical_agent
from nafas.agents.audit_agent import create_audit_agent
from nafas.steering.clinical_guardrails import CLINICAL_SYSTEM_PROMPT_INVARIANTS


SUPERVISOR_SWARM_PROMPT = CLINICAL_SYSTEM_PROMPT_INVARIANTS + """
You are the Swarm Lead Coordinator for Nafas (نَفَس).
You collaborate with fellow specialist agents:
• ClimateSpecialist: Analyzes weather, WBGT heat stress, OSHA work-rest cycles, and air quality.
• ClinicalRespiratorySpecialist: Verifies inhalers, contraindicated drugs, and spacer guidance.
• SafetyAuditor: Audits finalized advice before patient delivery.

SWARM HANDOFF PROTOCOL:
1. When receiving a climate query, transfer context to ClimateSpecialist.
2. When receiving a medication or inhaler query, transfer context to ClinicalRespiratorySpecialist.
3. Once specialist reasoning is complete, have SafetyAuditor verify the synthesized advice.
4. Output the final safe guidance in clean, empathetic bullet points.
"""


def create_nafas_swarm(
    model: Model | str | None = None,
    session_manager: SessionManager | None = None,
    hooks: list[Any] | None = None,
    id: str = "nafas_swarm",
    **kwargs: Any,
) -> Swarm:
    """Factory creating a collaborative Multi-Agent Swarm for environmental and respiratory health."""
    climate_agent = create_climate_agent(model=model, hooks=hooks)
    clinical_agent = create_clinical_agent(model=model, hooks=hooks)
    safety_auditor = create_audit_agent(model=model)

    supervisor = Agent(
        name="SwarmCoordinator",
        description="Coordinates environmental and respiratory health specialists in collaborative swarm.",
        model=model,
        system_prompt=SUPERVISOR_SWARM_PROMPT,
        hooks=hooks,
    )

    nodes = [supervisor, climate_agent, clinical_agent, safety_auditor]

    return Swarm(
        nodes=nodes,
        entry_point=supervisor,
        session_manager=session_manager,
        id=id,
        **kwargs,
    )

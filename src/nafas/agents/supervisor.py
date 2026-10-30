"""Supervisor Triage Agent for Nafas (نَفَس).

Triages incoming inquiries, screens for life-threatening acute respiratory red-flags,
delegates to specialized Climate and Clinical agents via agent-as-tool primitives,
and synthesizes a plain-language action plan.
"""

from typing import Any
from strands import Agent
from strands.models.model import Model
from nafas.steering.clinical_guardrails import (
    CLINICAL_SYSTEM_PROMPT_INVARIANTS,
    check_red_flag_emergency,
)
from nafas.steering.dialect_prompts import get_dialect_steering
from nafas.agents.climate_agent import create_climate_agent
from nafas.agents.clinical_agent import create_clinical_agent
from nafas.hooks.rate_limiter import RateLimiterHook
from nafas.hooks.sanitizer import PrivacySanitizerHook


def create_supervisor_agent(
    model: Model | str | None = None,
    climate_agent: Agent | None = None,
    clinical_agent: Agent | None = None,
    dialect: str = "saudi",
    hooks: list[Any] | None = None,
    **kwargs: Any,
) -> Agent:
    """Factory creating the Supervisor Triage Agent with specialist sub-agent tools."""
    c_agent = climate_agent or create_climate_agent(model=model)
    m_agent = clinical_agent or create_clinical_agent(model=model)

    active_hooks = hooks if hooks is not None else [RateLimiterHook(), PrivacySanitizerHook()]

    dialect_prompt = get_dialect_steering(dialect)

    system_prompt = (
        CLINICAL_SYSTEM_PROMPT_INVARIANTS
        + "\n\nSUPERVISOR ORCHESTRATION DIRECTIVE:\n"
        + "You are the Lead Triage Guardian for Nafas (نَفَس). "
        + "Assess incoming user questions and route to your specialist worker tools:\n"
        + "• Use 'ClimateSpecialist' when the user asks about outdoor heat, weather, dust, sandstorms, work-rest cycles, or cooling shelters.\n"
        + "• Use 'ClinicalRespiratorySpecialist' when the user asks about medications, inhalers (Ventolin, Pulmicort), fever pills, or cough/asthma symptoms.\n"
        + "• If the user's problem involves both (e.g. working outdoors in heat while experiencing asthma symptoms), call BOTH specialist tools.\n"
        + "• Synthesize the specialist findings into an empathetic, actionable, bulleted response.\n\n"
        + f"DIALECT & TONE STEERING:\n{dialect_prompt}\n"
    )

    tools = [
        c_agent.as_tool(
            name="ClimateSpecialist",
            description="Evaluates weather conditions, WBGT heat index, OSHA work-rest schedules, dust storms, and cooling shelters.",
        ),
        m_agent.as_tool(
            name="ClinicalRespiratorySpecialist",
            description="Verifies inhalers and medications, intercepts dangerous drug contraindications (aspirin/NSAIDs in asthma), and locates nebulizers.",
        ),
    ]

    return Agent(
        name="NafasSupervisor",
        description="Master triage and orchestrator agent coordinating climate and respiratory safety specialists.",
        model=model,
        system_prompt=system_prompt,
        tools=tools,
        hooks=active_hooks,
        **kwargs,
    )


class NafasOrchestrator:
    """End-to-end Nafas orchestrator integrating instant crisis triage, multi-agent delegation, and session baselines."""

    def __init__(
        self,
        model: Model | str | None = None,
        dialect: str = "saudi",
    ):
        self.model = model
        self.dialect = dialect
        self.climate_agent = create_climate_agent(model=model)
        self.clinical_agent = create_clinical_agent(model=model)
        self.supervisor = create_supervisor_agent(
            model=model,
            climate_agent=self.climate_agent,
            clinical_agent=self.clinical_agent,
            dialect=dialect,
        )

    def process_query(self, user_text: str, patient_baseline_prompt: str | None = None) -> dict[str, Any]:
        """Process user inquiry with immediate crisis filter followed by multi-agent reasoning."""
        # 1. Step 1: Sub-second fail-closed red-flag crisis detection
        red_flag_result = check_red_flag_emergency(user_text)
        if red_flag_result["is_emergency"]:
            return {
                "status": "EMERGENCY_DISPATCH_TRIGGERED",
                "red_flags": red_flag_result["matched_red_flags"],
                "response": red_flag_result["emergency_dispatch_message"],
                "hotlines": red_flag_result["hotlines"],
                "triaged_by": "instant_fail_closed_filter",
            }

        # 2. Step 2: Assemble prompt with persistent patient baseline if provided
        full_prompt = user_text
        if patient_baseline_prompt:
            full_prompt = f"{patient_baseline_prompt}\n\nUSER INQUIRY: {user_text}"

        # 3. Step 3: Run multi-agent supervisor loop
        agent_result = self.supervisor(full_prompt)

        response_text = ""
        if hasattr(agent_result, "message") and isinstance(agent_result.message, dict):
            content = agent_result.message.get("content", [])
            if isinstance(content, list):
                response_text = "".join(b.get("text", "") for b in content if isinstance(b, dict))
            elif isinstance(content, str):
                response_text = content
        elif hasattr(agent_result, "message"):
            response_text = str(agent_result.message)

        return {
            "status": "COMPLETED",
            "red_flags": [],
            "response": response_text,
            "triaged_by": "multi_agent_supervisor",
            "stop_reason": getattr(agent_result, "stop_reason", "end_turn"),
        }

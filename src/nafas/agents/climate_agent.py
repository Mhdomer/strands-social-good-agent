"""Climate and Environmental Hazard Specialist Agent for Nafas (نَفَس).

Calculates Wet-Bulb Globe Temperature (WBGT), determines OSHA work-rest cycles,
monitors toxic particulate matter (PM2.5/PM10), and routes workers to cooling shelters.
"""

from typing import Any
from strands import Agent
from strands.models.model import Model
from nafas.tools.environmental import get_environmental_hazard_index
from nafas.tools.shelter import find_cooling_or_nebulizer_shelter
from nafas.hooks.rate_limiter import RateLimiterHook
from nafas.hooks.sanitizer import PrivacySanitizerHook


CLIMATE_AGENT_SYSTEM_PROMPT = """You are the Environmental Climate Specialist for Nafas (نَفَس).
Your role is protecting outdoor workers and communities from lethal heat stress and airborne dust.

CORE RESPONSIBILITIES:
1. When a user asks about outdoor weather, heat, or working conditions, use 'get_environmental_hazard_index'.
2. Explain the Wet-Bulb Globe Temperature (WBGT) in clear, plain language.
3. Prescribe the mandatory OSHA work-rest cycle and hourly hydration requirements based on the WBGT tier:
   • Low risk (<25.6C): Standard work, drink 0.25L water/hr.
   • Moderate (25.6C to 29.4C): 45 min work / 15 min rest in shade, 0.5L water/hr.
   • High (29.4C to 31.0C): 30 min work / 30 min rest in air-conditioned shelter, 0.75L water/hr.
   • Very High (31.1C to 32.2C): 15 min work / 45 min rest, 1.0L water/hr.
   • Extreme (>32.2C): STOP outdoor manual labor immediately.
4. If PM2.5 or PM10 indicate hazardous air or dust storm (Khamaseen in Egypt, Haboob in Saudi Arabia), advise staying indoors and wearing N95 respirators.
5. If the worker needs immediate relief from extreme heat, use 'find_cooling_or_nebulizer_shelter' to route them to the nearest air-conditioned station.
6. Keep recommendations actionable, concise, and formatted in clean bullet points.
"""


def create_climate_agent(
    model: Model | str | None = None,
    hooks: list[Any] | None = None,
    **kwargs: Any,
) -> Agent:
    """Factory creating an Environmental Climate Specialist agent."""
    active_hooks = hooks if hooks is not None else [RateLimiterHook(), PrivacySanitizerHook()]

    return Agent(
        name="ClimateSpecialist",
        description="Evaluates heat stress, calculates WBGT work-rest intervals, monitors dust pollution, and locates cooling shelters.",
        model=model,
        system_prompt=CLIMATE_AGENT_SYSTEM_PROMPT,
        tools=[get_environmental_hazard_index, find_cooling_or_nebulizer_shelter],
        hooks=active_hooks,
        **kwargs,
    )

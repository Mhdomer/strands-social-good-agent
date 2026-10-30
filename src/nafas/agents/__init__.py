"""Nafas agents package exporting specialist agents, supervisor triage, and swarm."""

from nafas.agents.climate_agent import create_climate_agent
from nafas.agents.clinical_agent import create_clinical_agent
from nafas.agents.audit_agent import create_audit_agent
from nafas.agents.supervisor import create_supervisor_agent, NafasOrchestrator
from nafas.agents.swarm import create_nafas_swarm

__all__ = [
    "create_climate_agent",
    "create_clinical_agent",
    "create_audit_agent",
    "create_supervisor_agent",
    "create_nafas_swarm",
    "NafasOrchestrator",
]

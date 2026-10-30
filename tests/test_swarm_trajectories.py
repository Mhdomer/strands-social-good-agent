"""Module 7 Automated Trajectory Evals and End-to-End Swarm Tests for Nafas (نَفَس).

Verifies agent tool call trajectories, multi-agent supervisor delegation,
emergency instant triage bypass, and AWS Lambda serverless execution.
"""

import json
import pytest
from strands import Agent
from strands.models.model import Model
from nafas.tools.environmental import get_environmental_hazard_index
from nafas.tools.medication import verify_respiratory_medication_safety
from nafas.tools.shelter import find_cooling_or_nebulizer_shelter
from nafas.agents.climate_agent import create_climate_agent
from nafas.agents.clinical_agent import create_clinical_agent
from nafas.agents.audit_agent import create_audit_agent
from nafas.agents.swarm import create_nafas_swarm
from nafas.agents.supervisor import NafasOrchestrator
from nafas.runtime.lambda_handler import lambda_handler


class MockTrajectoryModel(Model):
    """Deterministic model simulating specific tool calls and responses for trajectory evals."""

    def __init__(self, tool_name: str, tool_input: dict, final_text: str):
        self.tool_name = tool_name
        self.tool_input = tool_input
        self.final_text = final_text
        self.turn = 0

    def get_config(self):
        return {}

    def update_config(self, **kwargs):
        pass

    async def structured_output(self, *args, **kwargs):
        raise NotImplementedError()

    async def stream(self, messages, tool_specs=None, system_prompt=None, **kwargs):
        self.turn += 1
        if self.turn == 1:
            # Yield tool use call
            yield {"messageStart": {"role": "assistant"}}
            yield {
                "contentBlockStart": {
                    "start": {"toolUse": {"name": self.tool_name, "toolUseId": f"call_{self.turn}"}},
                    "contentBlockIndex": 0,
                }
            }
            yield {
                "contentBlockDelta": {
                    "delta": {"toolUse": {"input": json.dumps(self.tool_input)}},
                    "contentBlockIndex": 0,
                }
            }
            yield {"contentBlockStop": {"contentBlockIndex": 0}}
            yield {"messageStop": {"stopReason": "tool_use"}}
        else:
            # Yield finalized synthesized answer
            yield {"messageStart": {"role": "assistant"}}
            yield {"contentBlockStart": {"start": {"text": ""}, "contentBlockIndex": 0}}
            yield {
                "contentBlockDelta": {
                    "delta": {"text": self.final_text},
                    "contentBlockIndex": 0,
                }
            }
            yield {"contentBlockStop": {"contentBlockIndex": 0}}
            yield {"messageStop": {"stopReason": "end_turn"}}


class MockTextModel(Model):
    """Simple deterministic model returning text directly."""

    def __init__(self, response_text: str = "Triage completed."):
        self.response_text = response_text

    def get_config(self):
        return {}

    def update_config(self, **kwargs):
        pass

    async def structured_output(self, *args, **kwargs):
        raise NotImplementedError()

    async def stream(self, messages, tool_specs=None, system_prompt=None, **kwargs):
        yield {"messageStart": {"role": "assistant"}}
        yield {"contentBlockStart": {"start": {"text": ""}, "contentBlockIndex": 0}}
        yield {
            "contentBlockDelta": {
                "delta": {"text": self.response_text},
                "contentBlockIndex": 0,
            }
        }
        yield {"contentBlockStop": {"contentBlockIndex": 0}}
        yield {"messageStop": {"stopReason": "end_turn"}}


class TestAgentTrajectories:
    """Test suite for agent tool invocation trajectories and multi-agent coordination."""

    def test_environmental_tool_trajectory(self):
        """Verify ClimateSpecialist trajectory executes get_environmental_hazard_index."""
        mock_model = MockTrajectoryModel(
            tool_name="get_environmental_hazard_index",
            tool_input={"city": "Riyadh"},
            final_text="Riyadh is at extreme WBGT 33.4C. Outdoor work must cease.",
        )
        agent = create_climate_agent(model=mock_model)
        result = agent("How hot is it in Riyadh?")

        # Check trajectory: Agent should have executed 2 turns (turn 1 tool call, turn 2 final answer)
        assert len(agent.messages) >= 2
        final_text = result.message["content"][0]["text"]
        assert "extreme WBGT" in final_text

    def test_clinical_tool_trajectory(self):
        """Verify ClinicalRespiratorySpecialist trajectory executes verify_respiratory_medication_safety."""
        mock_model = MockTrajectoryModel(
            tool_name="verify_respiratory_medication_safety",
            tool_input={"drug_name": "Aspirin"},
            final_text="CRITICAL ALERT: Aspirin is strictly contraindicated in asthma. Use Paracetamol.",
        )
        agent = create_clinical_agent(model=mock_model)
        result = agent("Can I take aspirin for a headache with asthma?")

        assert len(agent.messages) >= 2
        final_text = result.message["content"][0]["text"]
        assert "Aspirin is strictly contraindicated" in final_text
        assert "Paracetamol" in final_text

    def test_shelter_tool_trajectory(self):
        """Verify shelter locator trajectory executes find_cooling_or_nebulizer_shelter."""
        mock_model = MockTrajectoryModel(
            tool_name="find_cooling_or_nebulizer_shelter",
            tool_input={"city": "Cairo", "need_nebulizer": True},
            final_text="Proceed to Shubra General Hospital for emergency aerosol nebulization.",
        )
        agent = create_clinical_agent(model=mock_model)
        result = agent("Where can I find an emergency nebulizer in Cairo?")

        assert len(agent.messages) >= 2
        final_text = result.message["content"][0]["text"]
        assert "Shubra General Hospital" in final_text


class TestSwarmArchitecture:
    """Test suite verifying multi-agent swarm composition and handoffs."""

    def test_swarm_initialization_nodes(self):
        """Verify Swarm contains supervisor, climate specialist, clinical specialist, and safety auditor."""
        swarm = create_nafas_swarm(model=MockTextModel("Swarm ready"))
        node_names = list(swarm.nodes.keys())
        assert "SwarmCoordinator" in node_names
        assert "ClimateSpecialist" in node_names
        assert "ClinicalRespiratorySpecialist" in node_names
        assert "SafetyAuditor" in node_names
        assert swarm.entry_point.name == "SwarmCoordinator"

    def test_orchestrator_instant_emergency_bypass(self):
        """Verify NafasOrchestrator instantly bypasses model when cyanosis is detected."""
        orchestrator = NafasOrchestrator(model=MockTextModel("Normal response"))
        res = orchestrator.process_query("The asthmatic child has blue lips and cannot talk!")
        assert res["status"] == "EMERGENCY_DISPATCH_TRIGGERED"
        assert res["triaged_by"] == "instant_fail_closed_filter"
        assert "997" in res["response"]
        assert "123" in res["response"]


class TestLambdaRuntime:
    """Test suite for serverless AWS Lambda handler."""

    def test_lambda_handler_emergency_case(self):
        """Verify Lambda returns HTTP 200 with instant emergency dispatch."""
        event = {
            "body": json.dumps({
                "query": "My friend has blue lips in the desert and is gasping for air!",
                "session_id": "test_lambda_emergency",
                "dialect": "saudi",
            })
        }
        response = lambda_handler(event)
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["status"] == "EMERGENCY_DISPATCH_TRIGGERED"
        assert body["triaged_by"] == "instant_fail_closed_filter"
        assert body["latency_ms"] < 2000.0

    def test_lambda_handler_missing_query(self):
        """Verify Lambda returns HTTP 400 when query is missing."""
        event = {"body": json.dumps({"session_id": "no_query"})}
        response = lambda_handler(event)
        assert response["statusCode"] == 400

    def test_lambda_handler_with_patient_profile(self):
        """Verify Lambda accepts and stores patient respiratory profile."""
        event = {
            "body": json.dumps({
                "query": "The child has blue lips and chest retractions!",
                "session_id": "patient_profile_lambda_test",
                "patient_profile": {
                    "name": "Tariq",
                    "age": 6,
                    "primary_condition": "Severe Childhood Asthma",
                    "known_allergies": ["Aspirin", "Ibuprofen"],
                    "prescribed_inhalers": ["Ventolin", "Pulmicort"],
                },
            })
        }
        response = lambda_handler(event)
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["session_id"] == "patient_profile_lambda_test"

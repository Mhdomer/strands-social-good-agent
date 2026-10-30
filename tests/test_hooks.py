"""Unit tests for Nafas rate limiting and privacy sanitization hooks."""

import pytest
from nafas.hooks.rate_limiter import RateLimiterHook
from nafas.hooks.sanitizer import PrivacySanitizerHook
from strands.hooks import BeforeToolCallEvent, BeforeInvocationEvent


class DummyToolUse:
    """Mock tool use object for hook event testing."""
    def __init__(self, name: str, input_data: dict):
        self.name = name
        self.input = input_data

    def get(self, key, default=None):
        return getattr(self, key, default)


class TestRateLimiterHook:
    """Test suite for rate limiting and circuit breaking."""

    def test_rate_limiter_allows_within_quota(self):
        """Verify calls within the quota are allowed without cancellation."""
        hook = RateLimiterHook(max_tool_calls_per_turn=3)
        event = BeforeToolCallEvent(
            agent=None,
            selected_tool=None,
            tool_use=DummyToolUse("get_weather", {"city": "Riyadh"}),
            invocation_state={},
            cancel_tool=False,
        )

        hook.on_before_tool_call(event)
        assert event.cancel_tool is False
        assert hook.tool_call_count == 1

    def test_rate_limiter_blocks_over_quota(self):
        """Verify calls exceeding the quota are cancelled."""
        hook = RateLimiterHook(max_tool_calls_per_turn=2)

        for i in range(2):
            event = BeforeToolCallEvent(
                agent=None,
                selected_tool=None,
                tool_use=DummyToolUse(f"tool_{i}", {}),
                invocation_state={},
                cancel_tool=False,
            )
            hook.on_before_tool_call(event)
            assert event.cancel_tool is False

        # Third call must be cancelled
        over_event = BeforeToolCallEvent(
            agent=None,
            selected_tool=None,
            tool_use=DummyToolUse("tool_3", {}),
            invocation_state={},
            cancel_tool=False,
        )
        hook.on_before_tool_call(over_event)
        assert over_event.cancel_tool is not False
        assert "Rate limit exceeded" in str(over_event.cancel_tool)

    def test_circuit_breaker_duplicate_calls(self):
        """Verify circuit breaker catches 3 identical consecutive tool calls."""
        hook = RateLimiterHook(max_tool_calls_per_turn=10)
        tool_call = DummyToolUse("verify_drug", {"name": "aspirin"})

        # First call
        ev1 = BeforeToolCallEvent(agent=None, selected_tool=None, tool_use=tool_call, invocation_state={}, cancel_tool=False)
        hook.on_before_tool_call(ev1)
        assert ev1.cancel_tool is False

        # Second identical call
        ev2 = BeforeToolCallEvent(agent=None, selected_tool=None, tool_use=tool_call, invocation_state={}, cancel_tool=False)
        hook.on_before_tool_call(ev2)
        assert ev2.cancel_tool is False

        # Third identical call triggers circuit breaker
        ev3 = BeforeToolCallEvent(agent=None, selected_tool=None, tool_use=tool_call, invocation_state={}, cancel_tool=False)
        hook.on_before_tool_call(ev3)
        assert ev3.cancel_tool is not False
        assert "Circuit breaker triggered" in str(ev3.cancel_tool)


class TestPrivacySanitizerHook:
    """Test suite for healthcare PII masking."""

    def test_saudi_iqama_redaction(self):
        """Verify 10-digit Saudi Iqama or National ID is masked."""
        sanitizer = PrivacySanitizerHook()
        text = "Patient Iqama is 2458921478 for worker Ahmed."
        sanitized = sanitizer.sanitize_text(text)
        assert "2458921478" not in sanitized
        assert "[REDACTED_SAUDI_ID]" in sanitized
        assert sanitizer.redaction_count == 1

    def test_egypt_national_id_redaction(self):
        """Verify 14-digit Egyptian National ID is masked."""
        sanitizer = PrivacySanitizerHook()
        text = "National ID number 29801011234567 reported asthma flare-up."
        sanitized = sanitizer.sanitize_text(text)
        assert "29801011234567" not in sanitized
        assert "[REDACTED_EGYPT_ID]" in sanitized

    def test_phone_number_redaction(self):
        """Verify Saudi and Egyptian mobile numbers are masked."""
        sanitizer = PrivacySanitizerHook()
        text = "Contact worker at 0533741162 or Cairo relative at +201012345678 immediately."
        sanitized = sanitizer.sanitize_text(text)
        assert "0533741162" not in sanitized
        assert "+201012345678" not in sanitized
        assert "[REDACTED_PHONE]" in sanitized

    def test_hook_event_message_sanitization(self):
        """Verify BeforeInvocationEvent messages are sanitized in-place."""
        sanitizer = PrivacySanitizerHook()
        messages = [
            {
                "role": "user",
                "content": [{"text": "My phone is 0551234567 and my ID is 1087654321."}],
            }
        ]
        event = BeforeInvocationEvent(
            agent=None,
            invocation_state={},
            messages=messages,
            cancel=False,
        )
        sanitizer.on_before_invocation(event)

        redacted_text = messages[0]["content"][0]["text"]
        assert "0551234567" not in redacted_text
        assert "1087654321" not in redacted_text
        assert "[REDACTED_PHONE]" in redacted_text
        assert "[REDACTED_SAUDI_ID]" in redacted_text

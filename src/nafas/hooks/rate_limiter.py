"""Rate limiting and loop circuit breaker hook for Nafas (نَفَس).

Prevents runaway tool calling cycles, enforces per-turn execution quotas,
and detects circular tool invocations.
"""

from typing import Any
from strands.hooks import (
    HookProvider,
    HookRegistry,
    BeforeToolCallEvent,
    BeforeInvocationEvent,
)


class RateLimiterHook(HookProvider):
    """Lifecycle hook that limits tool execution count and breaks infinite loops."""

    def __init__(self, max_tool_calls_per_turn: int = 6):
        self.max_tool_calls_per_turn = max_tool_calls_per_turn
        self.tool_call_count = 0
        self.invocation_history: list[tuple[str, str]] = []

    def register_hooks(self, registry: HookRegistry, **kwargs: Any) -> None:
        """Register callbacks for invocation start and pre-tool execution."""
        registry.add_callback(BeforeInvocationEvent, self.on_before_invocation)
        registry.add_callback(BeforeToolCallEvent, self.on_before_tool_call)

    def on_before_invocation(self, event: BeforeInvocationEvent) -> None:
        """Reset turn-based counters on new incoming user turn."""
        self.tool_call_count = 0
        self.invocation_history.clear()

    def on_before_tool_call(self, event: BeforeToolCallEvent) -> None:
        """Inspect and enforce execution limits prior to tool execution."""
        self.tool_call_count += 1
        tool_name = event.tool_use.get("name", "unknown") if isinstance(event.tool_use, dict) else getattr(event.tool_use, "name", "unknown")
        tool_input = str(event.tool_use.get("input", {})) if isinstance(event.tool_use, dict) else str(getattr(event.tool_use, "input", {}))

        # Check turn quota limit
        if self.tool_call_count > self.max_tool_calls_per_turn:
            event.cancel_tool = (
                f"Rate limit exceeded: capped at {self.max_tool_calls_per_turn} tool calls per turn. "
                "Synthesize existing findings and formulate final response."
            )
            return

        # Check circuit breaker for duplicate consecutive identical calls
        current_call = (tool_name, tool_input)
        if len(self.invocation_history) >= 2 and self.invocation_history[-1] == current_call and self.invocation_history[-2] == current_call:
            event.cancel_tool = (
                f"Circuit breaker triggered: tool '{tool_name}' was called 3 times with identical parameters. "
                "Halting recursive loop."
            )
            return

        self.invocation_history.append(current_call)

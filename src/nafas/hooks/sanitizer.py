"""Privacy sanitization hook for Nafas (نَفَس).

Sanitizes Personally Identifiable Information (PII) including Saudi Iqama/National IDs,
Egyptian National IDs, and regional phone numbers before prompt transmission.
"""

import re
from typing import Any
from strands.hooks import (
    HookProvider,
    HookRegistry,
    BeforeInvocationEvent,
)


class PrivacySanitizerHook(HookProvider):
    """Lifecycle hook that strips healthcare PII and identifiers prior to model invocation."""

    # Regex patterns for regional identifiers
    SAUDI_ID_PATTERN = re.compile(r"\b[12]\d{9}\b")
    EGYPT_ID_PATTERN = re.compile(r"\b[23]\d{13}\b")
    SAUDI_PHONE_PATTERN = re.compile(r"(?:\+966|00966|0)?5\d{8}\b")
    EGYPT_PHONE_PATTERN = re.compile(r"(?:\+20|0020|0)?1[0125]\d{8}\b")

    def __init__(self):
        self.redaction_count = 0

    def register_hooks(self, registry: HookRegistry, **kwargs: Any) -> None:
        """Register the sanitization callback on the start of invocation."""
        registry.add_callback(BeforeInvocationEvent, self.on_before_invocation)

    def sanitize_text(self, text: str) -> str:
        """Sanitize PII patterns from a plain string."""
        sanitized = text

        # Redact Saudi Iqama / National ID (10 digits starting with 1 or 2)
        sanitized, count_sa = self.SAUDI_ID_PATTERN.subn("[REDACTED_SAUDI_ID]", sanitized)
        # Redact Egyptian National ID (14 digits starting with 2 or 3)
        sanitized, count_eg = self.EGYPT_ID_PATTERN.subn("[REDACTED_EGYPT_ID]", sanitized)
        # Redact phone numbers
        sanitized, count_sp = self.SAUDI_PHONE_PATTERN.subn("[REDACTED_PHONE]", sanitized)
        sanitized, count_ep = self.EGYPT_PHONE_PATTERN.subn("[REDACTED_PHONE]", sanitized)

        total_new_redactions = count_sa + count_eg + count_sp + count_ep
        self.redaction_count += total_new_redactions
        return sanitized

    def on_before_invocation(self, event: BeforeInvocationEvent) -> None:
        """Inspect and sanitize incoming message content blocks in-place."""
        if not event.messages:
            return

        for message in event.messages:
            content = message.get("content", [])
            if isinstance(content, str):
                message["content"] = self.sanitize_text(content)
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and "text" in block:
                        block["text"] = self.sanitize_text(block["text"])

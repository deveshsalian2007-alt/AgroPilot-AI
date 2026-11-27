"""LLM provider interface and optional Bedrock adapter for AgroPilot AI.

Per AGENT_WORKFLOW.md, Amazon Bedrock is a candidate dependency, not an
assumed working dependency. Provider failures raise LLMUnavailableError so
the orchestrator can cleanly fall back to deterministic templates.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from schemas.evidence import FarmerReport, GeospatialEvidence


class LLMUnavailableError(RuntimeError):
    """Raised when an LLM backend is unconfigured, unreachable, or fails."""


class LLMProvider(ABC):
    """Abstract interface for LLM-backed report generation."""

    @abstractmethod
    def generate_report(self, evidence: GeospatialEvidence) -> FarmerReport:
        """Generate a FarmerReport grounded strictly in the provided evidence."""


class UnavailableLLMProvider(LLMProvider):
    """Default provider used when no LLM backend is configured or verified."""

    def __init__(self, reason: str = "No verified LLM provider configured.") -> None:
        self.reason = reason

    def generate_report(self, evidence: GeospatialEvidence) -> FarmerReport:
        raise LLMUnavailableError(self.reason)


class BedrockLLMProvider(LLMProvider):
    """Placeholder Amazon Bedrock adapter.

    Requires boto3 and verified Bedrock credentials/model access before use.
    """

    def __init__(self, model_id: str, region_name: Optional[str] = None) -> None:
        self.model_id = model_id
        self.region_name = region_name

    def generate_report(self, evidence: GeospatialEvidence) -> FarmerReport:
        try:
            import boto3  # type: ignore  # noqa: F401
        except ImportError as exc:
            raise LLMUnavailableError("boto3 is not installed; falling back to deterministic reporter.") from exc

        raise LLMUnavailableError(
            "Bedrock integration is not yet verified in this environment; using deterministic fallback."
        )

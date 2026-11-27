"""Output validation for generated FarmerReport objects.

Verifies:
1. Required sections are present and non-empty.
2. No forbidden disease diagnosis or chemical/fertiliser prescription wording.
3. Every numeric measurement in summary/findings exists in validated evidence.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from schemas.evidence import ConfidenceLevel, FarmerReport, GeospatialEvidence

_ISO_DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)?\b")
_NUMBER_RE = re.compile(r"(?<![A-Za-z0-9_.-])-?\d+(?:\.\d+)?(?![A-Za-z0-9_])")

_FORBIDDEN_PHRASES = (
    "diagnosed with",
    "confirmed disease",
    "confirmed infection",
    "apply pesticide",
    "spray pesticide",
    "apply fungicide",
    "spray fungicide",
    "apply insecticide",
    "spray insecticide",
    "apply fertiliser",
    "apply fertilizer",
    "recommended dosage",
    "kg/ha",
    "ml/l",
)


@dataclass(frozen=True)
class OutputValidationResult:
    is_valid: bool
    violations: list[str] = field(default_factory=list)


def _extract_measurements(text: str) -> list[float]:
    stripped = _ISO_DATE_RE.sub(" ", text)
    return [float(match.group(0)) for match in _NUMBER_RE.finditer(stripped)]


def _number_in_evidence(value: float, evidence_numbers: set[float]) -> bool:
    return any(abs(value - ref) <= 1e-6 for ref in evidence_numbers)


def validate_report_output(report: FarmerReport, evidence: GeospatialEvidence) -> OutputValidationResult:
    """Validate that a FarmerReport is safe, complete, and grounded in evidence."""
    violations: list[str] = []

    if not report.summary or not report.summary.strip():
        violations.append("Report summary must not be empty.")

    if report.confidence not in {c.value for c in ConfidenceLevel}:
        violations.append(f"Invalid report confidence: '{report.confidence}'.")

    if report.language != evidence.language.value:
        violations.append(
            f"Report language '{report.language}' does not match requested '{evidence.language.value}'."
        )

    if not report.disclaimers:
        violations.append("Report must include safety disclaimers.")

    if not report.findings:
        violations.append("Report must include at least one finding.")

    evidence_numbers = evidence.numeric_values()
    texts_to_check = [report.summary]
    for finding in report.findings:
        texts_to_check.append(finding.observation)
        texts_to_check.append(finding.interpretation)

    combined_lower = " ".join(texts_to_check).lower()
    for phrase in _FORBIDDEN_PHRASES:
        if phrase in combined_lower:
            violations.append(f"Forbidden diagnostic or prescriptive phrase detected: '{phrase}'.")

    for text in texts_to_check:
        for num in _extract_measurements(text):
            if not _number_in_evidence(num, evidence_numbers):
                violations.append(
                    f"Ungrounded numeric value '{num:g}' in report text is not present in validated evidence."
                )

    return OutputValidationResult(is_valid=len(violations) == 0, violations=violations)

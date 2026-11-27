"""End-to-end AI agent pipeline orchestrator for AgroPilot AI.

Stages (per docs/architecture/AGENT_WORKFLOW.md):
1. Input validator
2. Evidence normaliser
3. Report generation (LLM provider if available, otherwise deterministic fallback)
4. Output validator (falls back to deterministic template if LLM output fails checks)
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Optional

from reporter.deterministic_reporter import generate_deterministic_report
from reporter.llm_provider import LLMProvider, LLMUnavailableError, UnavailableLLMProvider
from reporter.output_validator import validate_report_output
from schemas.evidence import AgentResult, ConfidenceLevel, FarmerReport, WeatherEvidence, WeatherStatus
from tools.evidence_normaliser import normalise_evidence
from tools.input_validator import SYNTHETIC_DATA_NOTICE, validate_raw_evidence
from tools.weather_tool import JsonFetcher, fetch_open_meteo_weather


def run_agent_pipeline(
    payload: dict[str, Any],
    llm_provider: Optional[LLMProvider] = None,
    weather_fetcher: Optional[JsonFetcher] = None,
    production_mode: bool = False,
) -> AgentResult:
    """Execute the full validation, normalisation, reporting, and safety pipeline."""
    job_id = str(payload.get("job_id", "unknown")) if isinstance(payload, dict) else "unknown"

    if isinstance(payload, dict) and isinstance(payload.get("weather"), WeatherEvidence):
        payload = {**payload, "weather": payload["weather"].to_dict()}

    input_check = validate_raw_evidence(payload, production_mode=production_mode)
    if not input_check.is_valid:
        return AgentResult(
            job_id=job_id,
            status="FAILED",
            report=None,
            validation_errors=input_check.errors,
            validation_warnings=input_check.warnings,
            sources=[],
        )

    evidence = normalise_evidence(payload)
    warnings = list(input_check.warnings)

    # Optional Open-Meteo enrichment when weather is unavailable and field_location is supplied
    field_loc = payload.get("field_location")
    if (
        evidence.weather.status == WeatherStatus.UNAVAILABLE
        and isinstance(field_loc, dict)
        and "latitude" in field_loc
        and "longitude" in field_loc
    ):
        date_range = payload.get("date_range") if isinstance(payload.get("date_range"), dict) else {}
        fetched_weather = fetch_open_meteo_weather(
            latitude=field_loc["latitude"],
            longitude=field_loc["longitude"],
            start_date=date_range.get("start"),
            end_date=date_range.get("end"),
            fetcher=weather_fetcher,
        )
        sources = list(evidence.provenance.sources)
        if fetched_weather.status != WeatherStatus.UNAVAILABLE and "open-meteo" not in sources:
            sources.append("open-meteo")
        evidence = replace(
            evidence,
            weather=fetched_weather,
            provenance=replace(evidence.provenance, sources=sources),
        )
        if fetched_weather.limitations:
            warnings.extend(fetched_weather.limitations)

    provider = llm_provider if llm_provider is not None else UnavailableLLMProvider()

    report: Optional[FarmerReport] = None
    try:
        candidate = provider.generate_report(evidence)
        output_check = validate_report_output(candidate, evidence)
        if output_check.is_valid:
            report = candidate
        else:
            warnings.append(
                "LLM output failed safety/grounding validation ("
                + "; ".join(output_check.violations)
                + "); used deterministic fallback."
            )
    except LLMUnavailableError as exc:
        warnings.append(f"LLM unavailable ({exc}); used deterministic fallback.")
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"LLM provider error ({exc}); used deterministic fallback.")

    if report is None:
        report = generate_deterministic_report(evidence)
        det_check = validate_report_output(report, evidence)
        if not det_check.is_valid:
            return AgentResult(
                job_id=evidence.job_id,
                status="FAILED",
                report=None,
                validation_errors=det_check.violations,
                validation_warnings=warnings,
                sources=list(evidence.provenance.sources),
            )

    if SYNTHETIC_DATA_NOTICE in warnings and SYNTHETIC_DATA_NOTICE not in report.limitations:
        report = replace(report, limitations=[*report.limitations, SYNTHETIC_DATA_NOTICE])

    result_status = "PARTIAL" if report.confidence == ConfidenceLevel.INSUFFICIENT.value else "COMPLETED"
    return AgentResult(
        job_id=evidence.job_id,
        status=result_status,
        report=report,
        validation_errors=[],
        validation_warnings=warnings,
        sources=list(evidence.provenance.sources),
    )

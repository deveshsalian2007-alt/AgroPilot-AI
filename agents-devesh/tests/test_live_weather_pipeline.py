"""Optional manual live integration test: Open-Meteo (Vellore) -> AI Report Pipeline.

Run manually with network access:
    python agents-devesh/tests/test_live_weather_pipeline.py

This script is intentionally NOT a unittest.TestCase so it does not run
during the regular offline unit-test suite (`unittest discover`).
It uses real Open-Meteo data for Vellore (12.9165 N, 79.1325 E) and does not
fabricate any satellite imagery.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_AGENTS_DIR = Path(__file__).resolve().parents[1]
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))

from orchestrator.pipeline import run_agent_pipeline  # noqa: E402
from reporter.output_validator import validate_report_output  # noqa: E402
from schemas.evidence import WeatherStatus  # noqa: E402
from tools.evidence_normaliser import normalise_evidence  # noqa: E402
from tools.weather_tool import fetch_open_meteo_weather  # noqa: E402

VELLORE_LAT = 12.9165
VELLORE_LON = 79.1325


def run_live_vellore_test() -> int:
    """Fetch live Vellore weather from Open-Meteo and run it through run_agent_pipeline."""
    weather = fetch_open_meteo_weather(
        latitude=VELLORE_LAT,
        longitude=VELLORE_LON,
        forecast_days=5,
        timeout_seconds=15.0,
    )

    if weather.status == WeatherStatus.UNAVAILABLE:
        print(f"LIVE WEATHER UNAVAILABLE: {weather.limitations}")
        return 1

    payload = {
        "job_id": "live-vellore-weather-test",
        "crop": "paddy",
        "language": "en",
        "imagery_quality": {
            "status": "UNAVAILABLE",
            "valid_pixel_percent": None,
            "limitations": ["Satellite imagery not supplied in weather-only live test."],
        },
        "ndvi": {"observations": [], "change": None},
        "flood_analysis": {
            "status": "NOT_ANALYSED",
            "indicator": None,
            "method": None,
            "limitations": [],
        },
        "weather": weather,
        "provenance": {
            "generated_at": weather.retrieved_at,
            "processing_version": "0.1.0-live-weather",
            "sources": ["open-meteo"],
        },
    }

    result = run_agent_pipeline(payload)
    if result.status == "FAILED" or result.report is None:
        print(f"PIPELINE FAILED: {result.validation_errors}")
        return 1

    # Verify output grounding against normalised evidence
    normalised_payload = {**payload, "weather": weather.to_dict()}
    evidence = normalise_evidence(normalised_payload)
    check = validate_report_output(result.report, evidence)
    if not check.is_valid:
        print(f"OUTPUT VALIDATION FAILED: {check.violations}")
        return 1

    weather_finding = next((f for f in result.report.findings if f.indicator == "weather"), None)
    if weather_finding is None:
        print("MISSING WEATHER FINDING IN REPORT")
        return 1

    obs_text = weather_finding.observation
    if "Historical observed weather" not in obs_text or "Weather forecast" not in obs_text:
        print(f"HISTORICAL VS FORECAST NOT DISTINGUISHED: {obs_text}")
        return 1

    print("=== LIVE VELLORE WEATHER EVIDENCE ===")
    print(json.dumps(weather.to_dict(), indent=2))
    print("\n=== PIPELINE RESULT ===")
    print(f"Status: {result.status} | Confidence: {result.report.confidence} | Mode: {result.report.generation_mode}")
    print(json.dumps(result.report.to_dict(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(run_live_vellore_test())

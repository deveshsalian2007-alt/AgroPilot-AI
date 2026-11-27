"""Input validation for incoming geospatial and weather evidence payloads."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Optional

from schemas.evidence import FloodStatus, ImageryStatus, Language, WeatherStatus

REQUIRED_TOP_LEVEL_KEYS = (
    "job_id",
    "imagery_quality",
    "ndvi",
    "flood_analysis",
    "weather",
    "provenance",
)


@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _is_number(value: Any) -> bool:
    """Return True if value is a finite int/float and not bool."""
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _is_valid_iso_date(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        date.fromisoformat(value.strip())
        return True
    except ValueError:
        return False


_SYNTHETIC_MARKERS = ("synthetic", "mock", "fixture")
SYNTHETIC_DATA_NOTICE = "Synthetic/test data detected — not real field observations."


def detect_synthetic_markers(payload: dict[str, Any]) -> list[str]:
    """Return list of field paths containing synthetic/mock/fixture markers."""
    hits: list[str] = []

    def _has_marker(val: Any) -> bool:
        return isinstance(val, str) and any(m in val.lower() for m in _SYNTHETIC_MARKERS)

    if _has_marker(payload.get("job_id")):
        hits.append("job_id")
    prov = payload.get("provenance")
    if isinstance(prov, dict):
        if _has_marker(prov.get("processing_version")):
            hits.append("provenance.processing_version")
        sources = prov.get("sources")
        if isinstance(sources, list) and any(_has_marker(s) for s in sources):
            hits.append("provenance.sources")
    wx = payload.get("weather")
    if isinstance(wx, dict) and _has_marker(wx.get("provider")):
        hits.append("weather.provider")
    ndvi = payload.get("ndvi")
    if isinstance(ndvi, dict) and isinstance(ndvi.get("observations"), list):
        for idx, obs in enumerate(ndvi["observations"]):
            if isinstance(obs, dict) and _has_marker(obs.get("source_id")):
                hits.append(f"ndvi.observations[{idx}].source_id")
                break
    return hits


def _has_measured_values(payload: dict[str, Any]) -> bool:
    ndvi = payload.get("ndvi")
    if isinstance(ndvi, dict) and isinstance(ndvi.get("observations"), list):
        for obs in ndvi["observations"]:
            if isinstance(obs, dict) and (obs.get("mean") is not None or obs.get("median") is not None):
                return True
    wx = payload.get("weather")
    if isinstance(wx, dict) and any(
        wx.get(k) is not None for k in ("rainfall_mm", "temperature_c_mean", "humidity_percent_mean")
    ):
        return True
    flood = payload.get("flood_analysis")
    if isinstance(flood, dict) and flood.get("indicator") is not None:
        return True
    return False


def validate_raw_evidence(payload: Any, production_mode: bool = False) -> ValidationResult:
    """Validate raw evidence dictionary before normalisation.

    Missing or low-quality observations produce warnings rather than errors so
    the pipeline can still return an honest inconclusive/low-confidence report.
    """
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(payload, dict):
        return ValidationResult(is_valid=False, errors=["Payload must be a JSON object."])

    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in payload:
            errors.append(f"Missing required field: '{key}'.")

    job_id = payload.get("job_id")
    if "job_id" in payload and (not isinstance(job_id, str) or not job_id.strip()):
        errors.append("'job_id' must be a non-empty string.")

    language = payload.get("language")
    if language is not None and language not in {lang.value for lang in Language}:
        errors.append(f"Unsupported language '{language}'. Supported: en, ta.")

    # Imagery quality checks
    imagery = payload.get("imagery_quality")
    if imagery is not None:
        if not isinstance(imagery, dict):
            errors.append("'imagery_quality' must be an object.")
        else:
            status = imagery.get("status")
            if status not in {s.value for s in ImageryStatus}:
                errors.append(f"Invalid imagery_quality.status: '{status}'.")
            elif status in {ImageryStatus.CLOUDY.value, ImageryStatus.STALE.value, ImageryStatus.UNAVAILABLE.value}:
                warnings.append(f"Imagery quality is {status}; conclusions will be limited.")

            valid_pct = imagery.get("valid_pixel_percent")
            if valid_pct is not None:
                if not _is_number(valid_pct) or not (0.0 <= float(valid_pct) <= 100.0):
                    errors.append("'imagery_quality.valid_pixel_percent' must be between 0 and 100 or null.")

    # NDVI checks
    ndvi = payload.get("ndvi")
    if ndvi is not None:
        if not isinstance(ndvi, dict):
            errors.append("'ndvi' must be an object.")
        else:
            observations = ndvi.get("observations")
            if observations is None or not isinstance(observations, list):
                errors.append("'ndvi.observations' must be a list.")
            else:
                if len(observations) == 0:
                    warnings.append("No NDVI observations supplied.")
                for idx, obs in enumerate(observations):
                    if not isinstance(obs, dict):
                        errors.append(f"'ndvi.observations[{idx}]' must be an object.")
                        continue
                    if not _is_valid_iso_date(obs.get("date")):
                        errors.append(f"'ndvi.observations[{idx}].date' must be a valid YYYY-MM-DD date.")
                    for metric in ("mean", "median"):
                        val = obs.get(metric)
                        if val is not None and (not _is_number(val) or not (-1.0 <= float(val) <= 1.0)):
                            errors.append(
                                f"'ndvi.observations[{idx}].{metric}' must be between -1.0 and 1.0 or null."
                            )

            change = ndvi.get("change")
            if change is not None:
                if not isinstance(change, dict):
                    errors.append("'ndvi.change' must be an object or null.")
                else:
                    for key in ("absolute", "percent"):
                        val = change.get(key)
                        if val is not None and not _is_number(val):
                            errors.append(f"'ndvi.change.{key}' must be a number or null.")

    # Flood analysis checks
    flood = payload.get("flood_analysis")
    if flood is not None:
        if not isinstance(flood, dict):
            errors.append("'flood_analysis' must be an object.")
        else:
            f_status = flood.get("status")
            if f_status not in {s.value for s in FloodStatus}:
                errors.append(f"Invalid flood_analysis.status: '{f_status}'.")
            indicator = flood.get("indicator")
            if indicator is not None and not _is_number(indicator):
                errors.append("'flood_analysis.indicator' must be a number or null.")

    # Weather checks
    weather = payload.get("weather")
    if weather is not None:
        if not isinstance(weather, dict):
            errors.append("'weather' must be an object.")
        else:
            w_status = weather.get("status")
            if w_status not in {s.value for s in WeatherStatus}:
                errors.append(f"Invalid weather.status: '{w_status}'.")
            elif w_status == WeatherStatus.UNAVAILABLE.value:
                warnings.append("Weather data is unavailable.")
            rainfall = weather.get("rainfall_mm")
            if rainfall is not None and (not _is_number(rainfall) or float(rainfall) < 0.0):
                errors.append("'weather.rainfall_mm' must be non-negative or null.")
            fc_rainfall = weather.get("forecast_rainfall_mm")
            if fc_rainfall is not None and (not _is_number(fc_rainfall) or float(fc_rainfall) < 0.0):
                errors.append("'weather.forecast_rainfall_mm' must be non-negative or null.")
            for hum_key in ("humidity_percent_mean", "forecast_humidity_percent_mean"):
                hum_val = weather.get(hum_key)
                if hum_val is not None and (not _is_number(hum_val) or not (0.0 <= float(hum_val) <= 100.0)):
                    errors.append(f"'weather.{hum_key}' must be between 0 and 100 or null.")
            for temp_key in ("temperature_c_mean", "forecast_temperature_c_mean"):
                temp_val = weather.get(temp_key)
                if temp_val is not None and not _is_number(temp_val):
                    errors.append(f"'weather.{temp_key}' must be a finite number or null.")

    # Provenance checks
    provenance = payload.get("provenance")
    if provenance is not None:
        if not isinstance(provenance, dict):
            errors.append("'provenance' must be an object.")
        else:
            sources = provenance.get("sources")
            if sources is not None and not isinstance(sources, list):
                errors.append("'provenance.sources' must be a list or null.")

    for section_name in ("imagery_quality", "flood_analysis", "weather"):
        section = payload.get(section_name)
        if isinstance(section, dict):
            lims = section.get("limitations")
            if lims is not None and not isinstance(lims, list):
                errors.append(f"'{section_name}.limitations' must be a list or null.")

    synthetic_hits = detect_synthetic_markers(payload)
    if synthetic_hits:
        if production_mode:
            errors.append(
                "Synthetic/test data is not permitted in production_mode "
                f"(detected in: {', '.join(synthetic_hits)})."
            )
        else:
            warnings.append(SYNTHETIC_DATA_NOTICE)

    if production_mode and _has_measured_values(payload):
        prov_sources = provenance.get("sources") if isinstance(provenance, dict) else None
        if not isinstance(prov_sources, list) or len(prov_sources) == 0:
            errors.append("Provenance sources must be provided for measured observations in production_mode.")

    return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)

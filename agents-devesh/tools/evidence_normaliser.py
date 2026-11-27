"""Normalise validated raw evidence payloads into typed GeospatialEvidence."""

from __future__ import annotations

from typing import Any, Optional

from schemas.evidence import (
    FloodAnalysis,
    FloodStatus,
    GeospatialEvidence,
    ImageryQuality,
    ImageryStatus,
    Language,
    NdviChange,
    NdviEvidence,
    NdviObservation,
    Provenance,
    WeatherEvidence,
    WeatherStatus,
)


def _to_optional_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    return float(value)


def _to_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item is not None]


def normalise_evidence(payload: dict[str, Any]) -> GeospatialEvidence:
    """Convert a validated raw evidence dictionary into GeospatialEvidence.

    Preserves missing values as None and sorts NDVI observations by date.
    """
    imagery_raw = payload["imagery_quality"]
    imagery = ImageryQuality(
        status=ImageryStatus(imagery_raw["status"]),
        valid_pixel_percent=_to_optional_float(imagery_raw.get("valid_pixel_percent")),
        limitations=_to_str_list(imagery_raw.get("limitations")),
    )

    ndvi_raw = payload["ndvi"]
    observations = [
        NdviObservation(
            date=str(obs["date"]).strip(),
            mean=_to_optional_float(obs.get("mean")),
            median=_to_optional_float(obs.get("median")),
            source_id=str(obs["source_id"]) if obs.get("source_id") is not None else None,
        )
        for obs in ndvi_raw.get("observations", [])
    ]
    observations.sort(key=lambda item: item.date)

    change_raw = ndvi_raw.get("change")
    ndvi_change = None
    if isinstance(change_raw, dict):
        ndvi_change = NdviChange(
            absolute=_to_optional_float(change_raw.get("absolute")),
            percent=_to_optional_float(change_raw.get("percent")),
            method=str(change_raw["method"]) if change_raw.get("method") is not None else None,
        )

    ndvi = NdviEvidence(observations=observations, change=ndvi_change)

    flood_raw = payload["flood_analysis"]
    flood = FloodAnalysis(
        status=FloodStatus(flood_raw["status"]),
        indicator=_to_optional_float(flood_raw.get("indicator")),
        method=str(flood_raw["method"]) if flood_raw.get("method") is not None else None,
        limitations=_to_str_list(flood_raw.get("limitations")),
    )

    weather_raw = payload["weather"]
    fc_days_raw = weather_raw.get("forecast_days")
    fc_days = int(fc_days_raw) if isinstance(fc_days_raw, int) and not isinstance(fc_days_raw, bool) else None
    weather = WeatherEvidence(
        status=WeatherStatus(weather_raw["status"]),
        provider=str(weather_raw["provider"]) if weather_raw.get("provider") is not None else None,
        rainfall_mm=_to_optional_float(weather_raw.get("rainfall_mm")),
        retrieved_at=str(weather_raw["retrieved_at"]) if weather_raw.get("retrieved_at") is not None else None,
        limitations=_to_str_list(weather_raw.get("limitations")),
        temperature_c_mean=_to_optional_float(weather_raw.get("temperature_c_mean")),
        humidity_percent_mean=_to_optional_float(weather_raw.get("humidity_percent_mean")),
        period_start=str(weather_raw["period_start"]) if weather_raw.get("period_start") is not None else None,
        period_end=str(weather_raw["period_end"]) if weather_raw.get("period_end") is not None else None,
        forecast_days=fc_days,
        forecast_rainfall_mm=_to_optional_float(weather_raw.get("forecast_rainfall_mm")),
        forecast_temperature_c_mean=_to_optional_float(weather_raw.get("forecast_temperature_c_mean")),
        forecast_humidity_percent_mean=_to_optional_float(weather_raw.get("forecast_humidity_percent_mean")),
    )

    prov_raw = payload["provenance"]
    provenance = Provenance(
        generated_at=str(prov_raw["generated_at"]) if prov_raw.get("generated_at") is not None else None,
        processing_version=(
            str(prov_raw["processing_version"]) if prov_raw.get("processing_version") is not None else None
        ),
        sources=_to_str_list(prov_raw.get("sources")),
    )

    lang_raw = payload.get("language")
    language = Language(lang_raw) if lang_raw is not None else Language.EN
    crop_raw = payload.get("crop")
    crop = str(crop_raw).strip() if isinstance(crop_raw, str) and crop_raw.strip() else None

    return GeospatialEvidence(
        job_id=str(payload["job_id"]).strip(),
        imagery_quality=imagery,
        ndvi=ndvi,
        flood_analysis=flood,
        weather=weather,
        provenance=provenance,
        crop=crop,
        language=language,
    )

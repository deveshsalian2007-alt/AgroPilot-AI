"""Lightweight Open-Meteo weather retrieval, validation, and normalisation.

Clearly separates historical observations from upcoming forecasts and never
fabricates measurements when the API fails or returns missing values.
"""

from __future__ import annotations

import json
import math
from datetime import date, datetime, timezone
from typing import Any, Callable, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from schemas.evidence import WeatherEvidence, WeatherStatus

OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
DAILY_VARIABLES = "precipitation_sum,temperature_2m_mean,relative_humidity_2m_mean"

JsonFetcher = Callable[[str, float], dict[str, Any]]


def _default_http_get_json(url: str, timeout_seconds: float) -> dict[str, Any]:
    with urlopen(url, timeout=timeout_seconds) as response:  # noqa: S310
        raw_bytes = response.read()
    data = json.loads(raw_bytes.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Open-Meteo response must be a JSON object.")
    return data


def _is_finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _extract_valid_series(
    daily: dict[str, Any],
    key: str,
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
) -> list[float]:
    values = daily.get(key)
    if not isinstance(values, list):
        return []
    valid: list[float] = []
    for item in values:
        if item is None or not _is_finite_number(item):
            continue
        num = float(item)
        if min_val is not None and num < min_val:
            continue
        if max_val is not None and num > max_val:
            continue
        valid.append(num)
    return valid


def _safe_sum(values: list[float]) -> Optional[float]:
    if not values:
        return None
    return round(sum(values), 2)


def _safe_mean(values: list[float]) -> Optional[float]:
    if not values:
        return None
    return round(sum(values) / len(values), 2)


def _parse_iso_date(value: Optional[str]) -> Optional[date]:
    if value is None:
        return None
    try:
        return date.fromisoformat(value.strip())
    except (AttributeError, ValueError):
        return None


def _summarise_daily_payload(
    payload: dict[str, Any],
) -> tuple[Optional[float], Optional[float], Optional[float], Optional[str], Optional[str]]:
    daily = payload.get("daily")
    if not isinstance(daily, dict):
        raise ValueError("Open-Meteo response missing 'daily' object.")

    precip = _extract_valid_series(daily, "precipitation_sum", min_val=0.0)
    temps = _extract_valid_series(daily, "temperature_2m_mean", min_val=-90.0, max_val=70.0)
    hums = _extract_valid_series(daily, "relative_humidity_2m_mean", min_val=0.0, max_val=100.0)

    times = daily.get("time")
    start_str: Optional[str] = None
    end_str: Optional[str] = None
    if isinstance(times, list) and times:
        valid_times = [str(t) for t in times if isinstance(t, str) and t.strip()]
        if valid_times:
            start_str = valid_times[0]
            end_str = valid_times[-1]

    return _safe_sum(precip), _safe_mean(temps), _safe_mean(hums), start_str, end_str


def fetch_open_meteo_weather(
    latitude: float,
    longitude: float,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    forecast_days: int = 7,
    timeout_seconds: float = 10.0,
    fetcher: Optional[JsonFetcher] = None,
) -> WeatherEvidence:
    """Retrieve historical weather observations and optional forecast from Open-Meteo.

    Never raises on network/API errors; returns WeatherStatus.UNAVAILABLE or PARTIAL
    with explicit limitations and None for missing measurements.
    """
    limitations: list[str] = []

    if not _is_finite_number(latitude) or not (-90.0 <= float(latitude) <= 90.0):
        return WeatherEvidence(
            status=WeatherStatus.UNAVAILABLE,
            provider="open-meteo",
            limitations=["Invalid latitude; weather retrieval skipped."],
        )
    if not _is_finite_number(longitude) or not (-180.0 <= float(longitude) <= 180.0):
        return WeatherEvidence(
            status=WeatherStatus.UNAVAILABLE,
            provider="open-meteo",
            limitations=["Invalid longitude; weather retrieval skipped."],
        )
    if isinstance(forecast_days, bool) or not isinstance(forecast_days, int) or not (0 <= forecast_days <= 16):
        return WeatherEvidence(
            status=WeatherStatus.UNAVAILABLE,
            provider="open-meteo",
            limitations=["Invalid forecast_days (must be 0..16); weather retrieval skipped."],
        )

    parsed_start = _parse_iso_date(start_date)
    parsed_end = _parse_iso_date(end_date)
    if (start_date is not None and parsed_start is None) or (end_date is not None and parsed_end is None):
        return WeatherEvidence(
            status=WeatherStatus.UNAVAILABLE,
            provider="open-meteo",
            limitations=["Invalid historical date format (expected YYYY-MM-DD)."],
        )
    if parsed_start is not None and parsed_end is not None and parsed_start > parsed_end:
        return WeatherEvidence(
            status=WeatherStatus.UNAVAILABLE,
            provider="open-meteo",
            limitations=["Historical start_date must not be after end_date."],
        )

    http_get = fetcher if fetcher is not None else _default_http_get_json
    retrieved_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # 1. Historical observations
    hist_ok = False
    rainfall_mm: Optional[float] = None
    temp_mean: Optional[float] = None
    hum_mean: Optional[float] = None
    period_start: Optional[str] = start_date
    period_end: Optional[str] = end_date

    if parsed_start is not None and parsed_end is not None:
        hist_params = urlencode(
            {
                "latitude": float(latitude),
                "longitude": float(longitude),
                "start_date": parsed_start.isoformat(),
                "end_date": parsed_end.isoformat(),
                "daily": DAILY_VARIABLES,
                "timezone": "UTC",
            }
        )
        hist_url = f"{OPEN_METEO_ARCHIVE_URL}?{hist_params}"
    else:
        hist_params = urlencode(
            {
                "latitude": float(latitude),
                "longitude": float(longitude),
                "past_days": 7,
                "forecast_days": 0,
                "daily": DAILY_VARIABLES,
                "timezone": "UTC",
            }
        )
        hist_url = f"{OPEN_METEO_FORECAST_URL}?{hist_params}"

    try:
        hist_payload = http_get(hist_url, timeout_seconds)
        rainfall_mm, temp_mean, hum_mean, obs_start, obs_end = _summarise_daily_payload(hist_payload)
        period_start = period_start or obs_start
        period_end = period_end or obs_end
        if rainfall_mm is not None or temp_mean is not None or hum_mean is not None:
            hist_ok = True
        else:
            limitations.append("Historical weather response contained no valid daily measurements.")
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as exc:
        limitations.append(f"Historical weather retrieval failed ({exc}).")

    # 2. Forecast
    fc_ok = False
    fc_rain: Optional[float] = None
    fc_temp: Optional[float] = None
    fc_hum: Optional[float] = None
    fc_days_out: Optional[int] = forecast_days if forecast_days > 0 else None

    if forecast_days > 0:
        fc_params = urlencode(
            {
                "latitude": float(latitude),
                "longitude": float(longitude),
                "forecast_days": forecast_days,
                "daily": DAILY_VARIABLES,
                "timezone": "UTC",
            }
        )
        fc_url = f"{OPEN_METEO_FORECAST_URL}?{fc_params}"
        try:
            fc_payload = http_get(fc_url, timeout_seconds)
            fc_rain, fc_temp, fc_hum, _, _ = _summarise_daily_payload(fc_payload)
            if fc_rain is not None or fc_temp is not None or fc_hum is not None:
                fc_ok = True
            else:
                limitations.append("Weather forecast response contained no valid daily measurements.")
        except (HTTPError, URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as exc:
            limitations.append(f"Weather forecast retrieval failed ({exc}).")

    if hist_ok and (forecast_days == 0 or fc_ok):
        status = WeatherStatus.AVAILABLE
    elif hist_ok or fc_ok:
        status = WeatherStatus.PARTIAL
    else:
        status = WeatherStatus.UNAVAILABLE

    return WeatherEvidence(
        status=status,
        provider="open-meteo",
        rainfall_mm=rainfall_mm,
        retrieved_at=retrieved_at,
        limitations=limitations,
        temperature_c_mean=temp_mean,
        humidity_percent_mean=hum_mean,
        period_start=period_start,
        period_end=period_end,
        forecast_days=fc_days_out if fc_ok else None,
        forecast_rainfall_mm=fc_rain,
        forecast_temperature_c_mean=fc_temp,
        forecast_humidity_percent_mean=fc_hum,
    )

"""Unit tests for Open-Meteo Weather Intelligence component (synthetic fixtures only)."""

from __future__ import annotations

import math
import unittest
from typing import Any
from urllib.error import URLError

from orchestrator.pipeline import run_agent_pipeline
from schemas.evidence import WeatherStatus
from tests.synthetic_fixtures import make_synthetic_evidence
from tools.weather_tool import fetch_open_meteo_weather

SYNTHETIC_HISTORICAL_RESPONSE: dict[str, Any] = {
    "latitude": 11.0168,
    "longitude": 76.9558,
    "daily": {
        "time": ["2026-10-01", "2026-10-02", "2026-10-03"],
        "precipitation_sum": [10.0, 5.5, 2.5],
        "temperature_2m_mean": [28.0, 29.0, 30.0],
        "relative_humidity_2m_mean": [78.0, 80.0, 82.0],
    },
}

SYNTHETIC_FORECAST_RESPONSE: dict[str, Any] = {
    "latitude": 11.0168,
    "longitude": 76.9558,
    "daily": {
        "time": ["2026-10-17", "2026-10-18"],
        "precipitation_sum": [12.0, 8.0],
        "temperature_2m_mean": [27.0, 28.0],
        "relative_humidity_2m_mean": [84.0, 86.0],
    },
}


class TestWeatherTool(unittest.TestCase):
    def test_historical_and_forecast_separation(self) -> None:
        def fake_fetcher(url: str, timeout: float) -> dict[str, Any]:
            if "archive-api.open-meteo.com" in url:
                return SYNTHETIC_HISTORICAL_RESPONSE
            return SYNTHETIC_FORECAST_RESPONSE

        wx = fetch_open_meteo_weather(
            latitude=11.0168,
            longitude=76.9558,
            start_date="2026-10-01",
            end_date="2026-10-03",
            forecast_days=2,
            fetcher=fake_fetcher,
        )
        self.assertEqual(wx.status, WeatherStatus.AVAILABLE)
        self.assertEqual(wx.provider, "open-meteo")
        self.assertEqual(wx.rainfall_mm, 18.0)
        self.assertEqual(wx.temperature_c_mean, 29.0)
        self.assertEqual(wx.humidity_percent_mean, 80.0)
        self.assertEqual(wx.period_start, "2026-10-01")
        self.assertEqual(wx.period_end, "2026-10-03")
        self.assertEqual(wx.forecast_days, 2)
        self.assertEqual(wx.forecast_rainfall_mm, 20.0)
        self.assertEqual(wx.forecast_temperature_c_mean, 27.5)
        self.assertEqual(wx.forecast_humidity_percent_mean, 85.0)
        self.assertEqual(wx.limitations, [])

    def test_partial_failure_when_forecast_fails(self) -> None:
        def fake_fetcher(url: str, timeout: float) -> dict[str, Any]:
            if "archive-api.open-meteo.com" in url:
                return SYNTHETIC_HISTORICAL_RESPONSE
            raise URLError("forecast timeout")

        wx = fetch_open_meteo_weather(
            latitude=11.0168,
            longitude=76.9558,
            start_date="2026-10-01",
            end_date="2026-10-03",
            forecast_days=5,
            fetcher=fake_fetcher,
        )
        self.assertEqual(wx.status, WeatherStatus.PARTIAL)
        self.assertEqual(wx.rainfall_mm, 18.0)
        self.assertIsNone(wx.forecast_rainfall_mm)
        self.assertIsNone(wx.forecast_days)
        self.assertTrue(any("forecast" in lim.lower() for lim in wx.limitations))

    def test_full_api_failure_returns_unavailable_without_fabricating(self) -> None:
        def failing_fetcher(url: str, timeout: float) -> dict[str, Any]:
            raise TimeoutError("timed out")

        wx = fetch_open_meteo_weather(
            latitude=11.0168,
            longitude=76.9558,
            start_date="2026-10-01",
            end_date="2026-10-03",
            fetcher=failing_fetcher,
        )
        self.assertEqual(wx.status, WeatherStatus.UNAVAILABLE)
        self.assertIsNone(wx.rainfall_mm)
        self.assertIsNone(wx.temperature_c_mean)
        self.assertIsNone(wx.humidity_percent_mean)
        self.assertIsNone(wx.forecast_rainfall_mm)
        self.assertGreaterEqual(len(wx.limitations), 2)

    def test_missing_and_nan_values_stay_none_when_all_missing(self) -> None:
        def sparse_fetcher(url: str, timeout: float) -> dict[str, Any]:
            return {
                "daily": {
                    "time": ["2026-10-01", "2026-10-02"],
                    "precipitation_sum": [None, math.nan],
                    "temperature_2m_mean": [28.5, None],
                    "relative_humidity_2m_mean": [None, None],
                }
            }

        wx = fetch_open_meteo_weather(
            latitude=11.0168,
            longitude=76.9558,
            start_date="2026-10-01",
            end_date="2026-10-02",
            forecast_days=0,
            fetcher=sparse_fetcher,
        )
        self.assertEqual(wx.status, WeatherStatus.AVAILABLE)
        self.assertIsNone(wx.rainfall_mm)
        self.assertEqual(wx.temperature_c_mean, 28.5)
        self.assertIsNone(wx.humidity_percent_mean)

    def test_invalid_coordinates_and_dates_skip_network_calls(self) -> None:
        called = False

        def guard_fetcher(url: str, timeout: float) -> dict[str, Any]:
            nonlocal called
            called = True
            return {}

        bad_lat = fetch_open_meteo_weather(latitude=95.0, longitude=76.9, fetcher=guard_fetcher)
        self.assertEqual(bad_lat.status, WeatherStatus.UNAVAILABLE)
        bad_dates = fetch_open_meteo_weather(
            latitude=11.0,
            longitude=76.9,
            start_date="2026-10-10",
            end_date="2026-10-01",
            fetcher=guard_fetcher,
        )
        self.assertEqual(bad_dates.status, WeatherStatus.UNAVAILABLE)
        self.assertFalse(called)

    def test_pipeline_enriches_unavailable_weather_for_en_and_ta(self) -> None:
        def fake_fetcher(url: str, timeout: float) -> dict[str, Any]:
            if "archive-api.open-meteo.com" in url:
                return SYNTHETIC_HISTORICAL_RESPONSE
            return SYNTHETIC_FORECAST_RESPONSE

        for lang, expected_phrase in (("en", "Historical observed weather"), ("ta", "கடந்த கால வானிலை")):
            payload = make_synthetic_evidence(language=lang)
            payload["weather"] = {"status": "UNAVAILABLE", "provider": None, "rainfall_mm": None}
            payload["field_location"] = {"latitude": 11.0168, "longitude": 76.9558}
            payload["date_range"] = {"start": "2026-10-01", "end": "2026-10-03"}

            result = run_agent_pipeline(payload, weather_fetcher=fake_fetcher)
            self.assertEqual(result.status, "COMPLETED")
            self.assertIn("open-meteo", result.sources)
            assert result.report is not None
            self.assertEqual(result.report.confidence, "HIGH")
            weather_finding = next(f for f in result.report.findings if f.indicator == "weather")
            self.assertIn(expected_phrase, weather_finding.observation)
            self.assertIn("20", weather_finding.observation)

    def test_pipeline_accepts_weather_evidence_object_directly(self) -> None:
        def fake_fetcher(url: str, timeout: float) -> dict[str, Any]:
            if "archive-api.open-meteo.com" in url:
                return SYNTHETIC_HISTORICAL_RESPONSE
            return SYNTHETIC_FORECAST_RESPONSE

        wx = fetch_open_meteo_weather(
            latitude=11.0168,
            longitude=76.9558,
            start_date="2026-10-01",
            end_date="2026-10-03",
            forecast_days=2,
            fetcher=fake_fetcher,
        )
        payload = make_synthetic_evidence(language="en")
        payload["weather"] = wx
        result = run_agent_pipeline(payload)
        self.assertEqual(result.status, "COMPLETED")
        assert result.report is not None
        weather_finding = next(f for f in result.report.findings if f.indicator == "weather")
        self.assertIn("Historical observed weather", weather_finding.observation)
        self.assertIn("Weather forecast", weather_finding.observation)
        self.assertIn("29 C", weather_finding.observation)
        self.assertIn("80%", weather_finding.observation)


if __name__ == "__main__":
    unittest.main()

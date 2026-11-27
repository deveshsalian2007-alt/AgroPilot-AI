"""Schemas for AgroPilot AI agent inputs, normalized evidence, and reports.

Aligned with the draft contracts in docs/architecture/API_CONTRACT.md.
Missing values are preserved as None (JSON null) and never converted to 0.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Optional


class ImageryStatus(str, Enum):
    USABLE = "USABLE"
    CLOUDY = "CLOUDY"
    STALE = "STALE"
    UNAVAILABLE = "UNAVAILABLE"


class FloodStatus(str, Enum):
    NOT_ANALYSED = "NOT_ANALYSED"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    INCONCLUSIVE = "INCONCLUSIVE"


class WeatherStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    PARTIAL = "PARTIAL"


class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INSUFFICIENT = "INSUFFICIENT"


class Language(str, Enum):
    EN = "en"
    TA = "ta"


@dataclass(frozen=True)
class ImageryQuality:
    status: ImageryStatus
    valid_pixel_percent: Optional[float] = None
    limitations: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class NdviObservation:
    date: str
    mean: Optional[float] = None
    median: Optional[float] = None
    source_id: Optional[str] = None


@dataclass(frozen=True)
class NdviChange:
    absolute: Optional[float] = None
    percent: Optional[float] = None
    method: Optional[str] = None


@dataclass(frozen=True)
class NdviEvidence:
    observations: list[NdviObservation] = field(default_factory=list)
    change: Optional[NdviChange] = None


@dataclass(frozen=True)
class FloodAnalysis:
    status: FloodStatus = FloodStatus.NOT_ANALYSED
    indicator: Optional[float] = None
    method: Optional[str] = None
    limitations: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class WeatherEvidence:
    status: WeatherStatus = WeatherStatus.UNAVAILABLE
    provider: Optional[str] = None
    rainfall_mm: Optional[float] = None
    retrieved_at: Optional[str] = None
    limitations: list[str] = field(default_factory=list)
    temperature_c_mean: Optional[float] = None
    humidity_percent_mean: Optional[float] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    forecast_days: Optional[int] = None
    forecast_rainfall_mm: Optional[float] = None
    forecast_temperature_c_mean: Optional[float] = None
    forecast_humidity_percent_mean: Optional[float] = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize WeatherEvidence to a JSON-compatible dictionary."""
        return {
            "status": self.status.value,
            "provider": self.provider,
            "rainfall_mm": self.rainfall_mm,
            "retrieved_at": self.retrieved_at,
            "limitations": list(self.limitations),
            "temperature_c_mean": self.temperature_c_mean,
            "humidity_percent_mean": self.humidity_percent_mean,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "forecast_days": self.forecast_days,
            "forecast_rainfall_mm": self.forecast_rainfall_mm,
            "forecast_temperature_c_mean": self.forecast_temperature_c_mean,
            "forecast_humidity_percent_mean": self.forecast_humidity_percent_mean,
        }


@dataclass(frozen=True)
class Provenance:
    generated_at: Optional[str] = None
    processing_version: Optional[str] = None
    sources: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class GeospatialEvidence:
    job_id: str
    imagery_quality: ImageryQuality
    ndvi: NdviEvidence
    flood_analysis: FloodAnalysis
    weather: WeatherEvidence
    provenance: Provenance
    crop: Optional[str] = None
    language: Language = Language.EN

    def numeric_values(self) -> set[float]:
        """Return all exact numeric measurements present in the evidence."""
        values: set[float] = set()
        if self.imagery_quality.valid_pixel_percent is not None:
            values.add(float(self.imagery_quality.valid_pixel_percent))
        for obs in self.ndvi.observations:
            if obs.mean is not None:
                values.add(float(obs.mean))
            if obs.median is not None:
                values.add(float(obs.median))
        if self.ndvi.change is not None:
            if self.ndvi.change.absolute is not None:
                values.add(float(self.ndvi.change.absolute))
            if self.ndvi.change.percent is not None:
                values.add(float(self.ndvi.change.percent))
        if self.flood_analysis.indicator is not None:
            values.add(float(self.flood_analysis.indicator))
        if self.weather.rainfall_mm is not None:
            values.add(float(self.weather.rainfall_mm))
        if self.weather.temperature_c_mean is not None:
            values.add(float(self.weather.temperature_c_mean))
        if self.weather.humidity_percent_mean is not None:
            values.add(float(self.weather.humidity_percent_mean))
        if self.weather.forecast_days is not None:
            values.add(float(self.weather.forecast_days))
        if self.weather.forecast_rainfall_mm is not None:
            values.add(float(self.weather.forecast_rainfall_mm))
        if self.weather.forecast_temperature_c_mean is not None:
            values.add(float(self.weather.forecast_temperature_c_mean))
        if self.weather.forecast_humidity_percent_mean is not None:
            values.add(float(self.weather.forecast_humidity_percent_mean))
        return values


@dataclass(frozen=True)
class ReportFinding:
    indicator: str
    observation: str
    interpretation: str
    observation_date: Optional[str] = None


@dataclass(frozen=True)
class FarmerReport:
    language: str
    summary: str
    findings: list[ReportFinding]
    confidence: str
    limitations: list[str]
    generation_mode: str = "deterministic"
    disclaimers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AgentResult:
    job_id: str
    status: str
    report: Optional[FarmerReport] = None
    validation_errors: list[str] = field(default_factory=list)
    validation_warnings: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "status": self.status,
            "report": self.report.to_dict() if self.report is not None else None,
            "validation_errors": list(self.validation_errors),
            "validation_warnings": list(self.validation_warnings),
            "sources": list(self.sources),
        }

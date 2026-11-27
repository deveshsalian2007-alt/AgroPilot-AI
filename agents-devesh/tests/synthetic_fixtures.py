"""Reusable SYNTHETIC integration fixtures for AgroPilot AI agent tests.

WARNING: All data in this module is synthetic test data, NOT real satellite
or weather observations.
"""

from __future__ import annotations

import copy
from typing import Any

SYNTHETIC_INTEGRATION_EVIDENCE: dict[str, Any] = {
    "job_id": "synthetic-job-001",
    "crop": "paddy",
    "language": "en",
    "imagery_quality": {
        "status": "USABLE",
        "valid_pixel_percent": 86.5,
        "limitations": [],
    },
    "ndvi": {
        "observations": [
            {
                "date": "2026-10-15",
                "mean": 0.62,
                "median": 0.64,
                "source_id": "SYNTHETIC-S2-B",
            },
            {
                "date": "2026-10-01",
                "mean": 0.71,
                "median": 0.72,
                "source_id": "SYNTHETIC-S2-A",
            },
        ],
        "change": {
            "absolute": -0.09,
            "percent": -12.68,
            "method": "mean_diff",
        },
    },
    "flood_analysis": {
        "status": "LOW",
        "indicator": 0.12,
        "method": "synthetic_s1_threshold",
        "limitations": ["Synthetic test fixture only."],
    },
    "weather": {
        "status": "AVAILABLE",
        "provider": "synthetic-open-meteo",
        "rainfall_mm": 18.4,
        "retrieved_at": "2026-10-16",
        "limitations": [],
    },
    "provenance": {
        "generated_at": "2026-10-16T06:00:00Z",
        "processing_version": "0.1.0-synthetic",
        "sources": ["SYNTHETIC-S2-A", "SYNTHETIC-S2-B", "synthetic-open-meteo"],
    },
}


def make_synthetic_evidence(**overrides: Any) -> dict[str, Any]:
    """Return a deep copy of SYNTHETIC_INTEGRATION_EVIDENCE with top-level overrides."""
    payload = copy.deepcopy(SYNTHETIC_INTEGRATION_EVIDENCE)
    payload.update(overrides)
    return payload

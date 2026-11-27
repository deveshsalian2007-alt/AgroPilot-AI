# Geospatial Integration Proposal — Member 2 (`geospatial-snehendu/`)

Last updated: 2026-11-27  
Status: **PROPOSAL FOR TEAM AGREEMENT** (aligned with implemented `agents-devesh/` input validator and normaliser)

> [!IMPORTANT]
> `geospatial-snehendu/` currently contains only empty scaffold folders (`anomaly/`, `ndvi/`, `processing/`, `sentinel1/`, `sentinel2/`, `tests/`).  
> `agents-devesh/` has implemented strict input validation (`validate_raw_evidence`) and normalisation (`normalise_evidence`) expecting the structure below.

---

## 1. What Satellite-Derived Evidence `geospatial-snehendu/` Must Provide

All numeric raster and geospatial calculations **must** be computed deterministically in `geospatial-snehendu/` (never by an LLM). For each analysis job, `geospatial-snehendu/` should produce structured evidence covering:

1. **Imagery Quality (`imagery_quality`)**
   - Overall usability status: `"USABLE"`, `"CLOUDY"`, `"STALE"`, or `"UNAVAILABLE"`.
   - `valid_pixel_percent`: Percentage of cloud-free / valid pixels inside the field polygon (`0.0` to `100.0`), or `null` if not calculated.
   - `limitations`: List of plain-text quality notes (e.g., `"High cloud cover over northern boundary"`).
2. **NDVI Observations & Change (`ndvi`)**
   - `observations`: List of per-scene NDVI statistics within the requested date range:
     - `date`: ISO-8601 date (`"YYYY-MM-DD"`) of the satellite acquisition.
     - `mean`: Mean NDVI across valid pixels (`-1.0` to `1.0`), or `null` if unavailable.
     - `median`: Median NDVI across valid pixels (`-1.0` to `1.0`), or `null` if unavailable.
     - `source_id`: Satellite scene/product identifier (e.g., Sentinel-2 granule/product ID).
   - `change`: Period change between earliest and latest usable observations (or `null` if `< 2` usable scenes):
     - `absolute`: `latest - earliest` (float or `null`).
     - `percent`: Percentage change (float or `null`).
     - `method`: Aggregation/comparison method name (e.g., `"mean_diff"`, `"median_diff"`), or `null`.
3. **Flood / Surface Water Screening (`flood_analysis`)**
   - `status`: `"NOT_ANALYSED"`, `"LOW"`, `"MODERATE"`, `"HIGH"`, or `"INCONCLUSIVE"`.
   - `indicator`: Numeric screening metric (e.g., Sentinel-1 VV backscatter index or water-fraction score), or `null` if not computed.
   - `method`: Method identifier (e.g., `"s1_vv_threshold"`), or `null`.
   - `limitations`: Explicit caveats (e.g., `"Sentinel-1 inundation screening is experimental for small plots"`).
4. **Provenance (`provenance`)**
   - `generated_at`: UTC ISO-8601 timestamp when geospatial processing finished.
   - `processing_version`: Version tag of the geospatial pipeline (e.g., `"0.1.0"`).
   - `sources`: List of all satellite scene IDs / datasets used.

*(Note: `weather` is also part of the evidence payload consumed by `agents-devesh/`. Whether `geospatial-snehendu/` or `backend-amit/` populates `weather` is an open team decision; if `geospatial-snehendu/` does not fetch weather, `backend-amit/` will merge it before calling `agents-devesh/`.)*

---

## 2. How Missing, Cloudy, Stale, or Insufficient Data Must Be Represented

**Critical Rule**: Never convert missing data to `0` or `0.0`. Use JSON `null` (`None` in Python).

| Condition | `imagery_quality.status` | `valid_pixel_percent` | `ndvi.observations` | `ndvi.change` | Expected AI Report Outcome |
|---|---|---|---|---|---|
| **No satellite scenes found** | `"UNAVAILABLE"` | `null` | `[]` | `null` or all fields `null` | `status="PARTIAL"`, `confidence="INSUFFICIENT"`, honest inconclusive report |
| **Scene found, but masked by clouds** | `"CLOUDY"` | Actual `%` (e.g. `18.5`) or `null` | Omit unusable scene or set `mean: null, median: null` | `absolute: null, percent: null` | `confidence="LOW"` (or `"INSUFFICIENT"` if 0 valid NDVI) |
| **Only old scenes outside/near edge of window** | `"STALE"` | Actual `%` | Include observation with its **actual** acquisition `date` | `null` if single scene | `confidence="LOW"`, states staleness limitation |
| **Single usable scene only** | `"USABLE"` | Actual `%` (e.g. `91.0`) | 1 observation | `absolute: null, percent: null, method: null` | `confidence="MEDIUM"`, states single-date limitation |
| **Sentinel-1 not run / unsupported** | *(any)* | *(any)* | *(any)* | `flood_analysis.status = "NOT_ANALYSED"`, `indicator = null` | Flood section omitted or marked not analysed |

---

## 3. Exact JSON Structure Expected by `agents-devesh/`

When `geospatial-snehendu/` returns its output (to `backend-amit/` or directly to `agents-devesh/`), it should match this structure:

```json
{
  "job_id": "job-20261127-001",
  "imagery_quality": {
    "status": "USABLE",
    "valid_pixel_percent": 86.5,
    "limitations": []
  },
  "ndvi": {
    "observations": [
      {
        "date": "2026-10-01",
        "mean": 0.71,
        "median": 0.72,
        "source_id": "S2A_MSIL2A_20261001"
      },
      {
        "date": "2026-10-15",
        "mean": 0.62,
        "median": 0.64,
        "source_id": "S2B_MSIL2A_20261015"
      }
    ],
    "change": {
      "absolute": -0.09,
      "percent": -12.68,
      "method": "mean_diff"
    }
  },
  "flood_analysis": {
    "status": "LOW",
    "indicator": 0.12,
    "method": "s1_vv_threshold",
    "limitations": ["Sentinel-1 screening indicates surface wetness, not confirmed crop loss."]
  },
  "weather": {
    "status": "UNAVAILABLE",
    "provider": null,
    "rainfall_mm": null,
    "retrieved_at": null,
    "limitations": []
  },
  "provenance": {
    "generated_at": "2026-10-16T06:00:00Z",
    "processing_version": "0.1.0",
    "sources": ["S2A_MSIL2A_20261001", "S2B_MSIL2A_20261015"]
  }
}
```

### Validation Constraints Enforced by `agents-devesh/`
`validate_raw_evidence()` will reject (`status="FAILED"`) payloads that violate:
- `ndvi.observations[*].date` must be valid ISO `YYYY-MM-DD`.
- `ndvi.observations[*].mean` and `median` must be `null` or in `[-1.0, 1.0]` (booleans rejected).
- `imagery_quality.valid_pixel_percent` must be `null` or in `[0.0, 100.0]`.
- `imagery_quality.status` must be one of `USABLE`, `CLOUDY`, `STALE`, `UNAVAILABLE`.
- `flood_analysis.status` must be one of `NOT_ANALYSED`, `LOW`, `MODERATE`, `HIGH`, `INCONCLUSIVE`.
- `weather.rainfall_mm` must be `null` or `>= 0.0`.

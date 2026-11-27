# Shared Data Contract — AgroPilot AI

Last updated: 2026-11-27  
Status: **PROPOSED SHARED CONTRACT** (based on `docs/architecture/API_CONTRACT.md` and implemented schemas in `agents-devesh/schemas/evidence.py`)

> [!NOTE]
> **Implementation vs Proposal**:
> - **Implemented**: `agents-devesh/` validates, normalises, and consumes the **Evidence Input Schema** below and produces the **Agent Output Schema** below.
> - **Proposed (not yet implemented)**: `backend-amit/` HTTP endpoints (`POST /api/analyze`, `GET /api/analyze/{job_id}`, `GET /api/results/{job_id}`), `geospatial-snehendu/` producers, and JSON Schema files in `shared/api_schemas/`.

---

## 1. Evidence Input Schema (Geospatial + Backend -> AI Agent)

### Input JSON Example
```json
{
  "job_id": "job-20261127-001",
  "crop": "paddy",
  "language": "en",
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
    "limitations": []
  },
  "weather": {
    "status": "AVAILABLE",
    "provider": "open-meteo",
    "rainfall_mm": 18.4,
    "retrieved_at": "2026-10-16",
    "limitations": []
  },
  "provenance": {
    "generated_at": "2026-10-16T06:00:00Z",
    "processing_version": "0.1.0",
    "sources": ["S2A_MSIL2A_20261001", "S2B_MSIL2A_20261015", "open-meteo"]
  }
}
```

### Input Field Specification

| Field | Type | Required | Units / Format | Null / Validation Rules |
|---|---|---|---|---|
| `job_id` | `string` | Yes | Non-empty ID | Must be non-empty string |
| `crop` | `string \| null` | No | Crop name (e.g. `"paddy"`) | Defaults to generic crop label if omitted/`null` |
| `language` | `string` | No | `"en"` or `"ta"` | Defaults to `"en"` if omitted |
| `imagery_quality` | `object` | Yes | — | Must be object |
| `imagery_quality.status` | `string` | Yes | Enum | `"USABLE" \| "CLOUDY" \| "STALE" \| "UNAVAILABLE"` |
| `imagery_quality.valid_pixel_percent` | `number \| null` | No | Percent (`%`) | `0.0 <= x <= 100.0` or `null` |
| `imagery_quality.limitations` | `string[]` | No | Plain text | Defaults to `[]` |
| `ndvi` | `object` | Yes | — | Must be object |
| `ndvi.observations` | `object[]` | Yes | — | List (may be `[]` if unavailable) |
| `ndvi.observations[].date` | `string` | Yes | `YYYY-MM-DD` (ISO date) | Must parse as valid ISO date |
| `ndvi.observations[].mean` | `number \| null` | No | Dimensionless NDVI | `-1.0 <= x <= 1.0` or `null` |
| `ndvi.observations[].median` | `number \| null` | No | Dimensionless NDVI | `-1.0 <= x <= 1.0` or `null` |
| `ndvi.observations[].source_id` | `string \| null` | No | Scene/product ID | `null` if unknown |
| `ndvi.change` | `object \| null` | No | — | `null` if `< 2` usable observations |
| `ndvi.change.absolute` | `number \| null` | No | NDVI delta | Number or `null` |
| `ndvi.change.percent` | `number \| null` | No | Percent (`%`) | Number or `null` |
| `ndvi.change.method` | `string \| null` | No | Method name | e.g. `"mean_diff"` or `null` |
| `flood_analysis` | `object` | Yes | — | Must be object |
| `flood_analysis.status` | `string` | Yes | Enum | `"NOT_ANALYSED" \| "LOW" \| "MODERATE" \| "HIGH" \| "INCONCLUSIVE"` |
| `flood_analysis.indicator` | `number \| null` | No | Dimensionless index | Number or `null` |
| `flood_analysis.method` | `string \| null` | No | Method name | String or `null` |
| `flood_analysis.limitations` | `string[]` | No | Plain text | Defaults to `[]` |
| `weather` | `object` | Yes | — | Must be object |
| `weather.status` | `string` | Yes | Enum | `"AVAILABLE" \| "UNAVAILABLE" \| "PARTIAL"` |
| `weather.provider` | `string \| null` | No | Provider name | e.g. `"open-meteo"` or `null` |
| `weather.rainfall_mm` | `number \| null` | No | Millimetres (`mm`) | `>= 0.0` or `null` |
| `weather.retrieved_at` | `string \| null` | No | ISO date/timestamp | String or `null` |
| `weather.limitations` | `string[]` | No | Plain text | Defaults to `[]` |
| `provenance` | `object` | Yes | — | Must be object |
| `provenance.generated_at` | `string \| null` | No | UTC ISO-8601 | e.g. `"2026-10-16T06:00:00Z"` |
| `provenance.processing_version` | `string \| null` | No | Semver string | e.g. `"0.1.0"` |
| `provenance.sources` | `string[]` | No | Source IDs | Defaults to `[]` |

---

## 2. Agent Output Schema (AI Agent -> Backend)

### Output JSON Example
```json
{
  "job_id": "job-20261127-001",
  "status": "COMPLETED",
  "report": {
    "language": "en",
    "summary": "Satellite vegetation and context summary for paddy (confidence: HIGH). Review measured indicators and field conditions carefully.",
    "findings": [
      {
        "indicator": "ndvi",
        "observation": "Latest NDVI on 2026-10-15: mean NDVI 0.62, median NDVI 0.64. Period change: absolute change -0.09, percent change -12.68%.",
        "interpretation": "Greenness declined over the period for the paddy; this may reflect crop stress, harvesting, cloud artefacts, or moisture changes. Field inspection is recommended.",
        "observation_date": "2026-10-15"
      }
    ],
    "confidence": "HIGH",
    "limitations": [],
    "generation_mode": "deterministic",
    "disclaimers": [
      "This advisory is based on satellite and weather indicators only and is not a confirmed disease diagnosis.",
      "Do not apply pesticides, fertilisers, or chemical treatments based solely on this report; consult a local agricultural officer or inspect the field directly."
    ]
  },
  "validation_errors": [],
  "validation_warnings": [],
  "sources": ["S2A_MSIL2A_20261001", "S2B_MSIL2A_20261015", "open-meteo"]
}
```

### Output Field Specification
- `status`: `"COMPLETED"` | `"PARTIAL"` (when `confidence == "INSUFFICIENT"`) | `"FAILED"` (when input validation fails).
- `report`: `object | null` (`null` when `status == "FAILED"`).
  - `confidence`: `"HIGH"` | `"MEDIUM"` | `"LOW"` | `"INSUFFICIENT"`.
  - `generation_mode`: `"deterministic"` | `"llm"`.
  - `findings[].observation` vs `findings[].interpretation`: Strictly separates measured facts from possible explanations.
- `validation_errors`: `string[]` — populated when `status == "FAILED"`.
- `validation_warnings`: `string[]` — non-fatal quality or fallback notices.

---

## 3. Null / Missing-Value & Validation Conventions

1. **Null means unavailable, never zero**: `rainfall_mm: null` means no rainfall measurement was available; `rainfall_mm: 0` means 0 mm of rain was actually measured.
2. **Type strictness**: Python booleans (`True`/`False`) are rejected as numeric fields.
3. **Output safety**: `agents-devesh/` blocks any report text containing disease diagnoses, chemical/fertiliser prescriptions, or numeric values absent from the validated input evidence.

---

## 4. Error Response Format (API Layer — Proposed in `API_CONTRACT.md`)

When `backend-amit/` returns an HTTP error (4xx/5xx), use the draft format from `docs/architecture/API_CONTRACT.md`:

```json
{
  "error": {
    "code": "INVALID_EVIDENCE_PAYLOAD",
    "message": "Evidence validation failed.",
    "details": [
      "'ndvi.observations[0].mean' must be between -1.0 and 1.0 or null."
    ]
  }
}
```

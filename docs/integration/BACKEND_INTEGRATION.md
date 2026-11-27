# Backend Integration Proposal — Member 1 (`backend-amit/`)

Last updated: 2026-11-27  
Status: **PROPOSAL FOR TEAM AGREEMENT** (documents implemented `agents-devesh/` interface + proposed `backend-amit/` integration)

> [!IMPORTANT]
> `backend-amit/` currently contains only empty scaffold folders (`api/`, `database/`, `models/`, `routes/`, `services/`, `tests/`). Nothing in `backend-amit/` is implemented yet.  
> `agents-devesh/` has an implemented, unit-tested Python vertical slice (`run_agent_pipeline`).

---

## 1. Recommended Invocation Architecture

### Recommendation: Direct Python In-Process Call First (HTTP Microservice Optional Later)

| Option | Pros | Cons | Recommendation |
|---|---|---|---|
| **Option A: Direct Python import (`run_agent_pipeline`)** | Zero network latency, zero extra container/Lambda deployment, no serialization overhead, uses Python 3.14 stdlib only (no extra dependencies) | Requires `backend-amit/` worker/API to run in Python | **Recommended for hackathon MVP** |
| **Option B: Internal HTTP API wrapper around `agents-devesh/`** | Language-agnostic (works if `backend-amit/` uses Node.js/TypeScript or separate container) | Extra service to deploy, manage, secure, and handle timeouts/retries | Use only if `backend-amit/` is non-Python or deployed as a separate service |

### How Option A Works in Python
If `backend-amit/` runs in Python (e.g., FastAPI/Flask or an async worker):

```python
import sys
from pathlib import Path

# Ensure agents-devesh/ is importable (or package it once team agrees)
AGENTS_DIR = Path(__file__).resolve().parents[2] / "agents-devesh"
if str(AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(AGENTS_DIR))

from orchestrator.pipeline import run_agent_pipeline

agent_result = run_agent_pipeline(evidence_payload)
response_dict = agent_result.to_dict()
```

**Implemented today in `agents-devesh/`**:
- Entrypoint: `run_agent_pipeline(payload: dict[str, Any], llm_provider: Optional[LLMProvider] = None) -> AgentResult` in `agents-devesh/orchestrator/pipeline.py`.
- Return helper: `agent_result.to_dict()` returns a JSON-serializable `dict`.
- Default LLM behavior: When `llm_provider=None`, it uses `UnavailableLLMProvider` and automatically runs the deterministic English/Tamil reporter (`generation_mode="deterministic"`).

---

## 2. JSON Payload `backend-amit/` Must Send to `agents-devesh/`

The backend assembles the geospatial output (from `geospatial-snehendu/`) + weather context + request metadata (`crop`, `language`) into the payload below.

> See [SHARED_DATA_CONTRACT.md](file:///c:/Users/HP/OneDrive/Desktop/Hack%20ideas%20and%20projects/AgroPilot-AI/docs/integration/SHARED_DATA_CONTRACT.md) for full field-by-field definitions and validation rules.

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

### Key Backend Responsibilities When Building the Payload
1. **Preserve `null`**: If weather or a metric was not retrieved, send `null` (`None` in Python) — **never** replace missing values with `0`.
2. **Pass `crop` and `language`**: Forward the farmer's requested `crop` (optional string) and `language` (`"en"` or `"ta"`, defaults to `"en"` if omitted).
3. **Weather retrieval (open decision)**: Decide with Member 3 whether `backend-amit/` fetches Open-Meteo weather data during job execution or `agents-devesh/` adds a weather tool. Currently, `agents-devesh/` expects `weather` inside the input payload.

---

## 3. Response JSON `backend-amit/` Will Receive

`run_agent_pipeline(...).to_dict()` returns:

```json
{
  "job_id": "job-20261127-001",
  "status": "COMPLETED",
  "report": {
    "language": "en",
    "summary": "Satellite vegetation and context summary for paddy (confidence: HIGH). Review measured indicators and field conditions carefully.",
    "findings": [
      {
        "indicator": "imagery_quality",
        "observation": "Satellite imagery status is USABLE (valid pixel coverage 86.5%).",
        "interpretation": "Observations are usable for general vegetation monitoring.",
        "observation_date": null
      },
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
  "validation_warnings": [
    "LLM unavailable (No verified LLM provider configured.); used deterministic fallback."
  ],
  "sources": ["S2A_MSIL2A_20261001", "S2B_MSIL2A_20261015", "open-meteo"]
}
```

### Mapping `AgentResult` to `GET /api/results/{job_id}` (Proposed)
Per `docs/architecture/API_CONTRACT.md`, the frontend expects `GET /api/results/{job_id}` to include `observations`, `weather`, `report`, `sources`, and `status`. `backend-amit/` should store:
- `observations` and `weather` from `geospatial-snehendu/` + weather service
- `report` and `sources` from `AgentResult.to_dict()`
- `status` mapped from `AgentResult.status` (`COMPLETED`, `PARTIAL`, or `FAILED`)

---

## 4. Error Handling, Invalid Inputs, and Unavailable AI Services

| Scenario | Behavior in `agents-devesh/` (Implemented) | Recommended `backend-amit/` Action |
|---|---|---|
| **Invalid payload schema / out-of-range values** (e.g. NDVI `> 1.0`, bad date format, missing required keys) | Returns `AgentResult` with `status="FAILED"`, `report=None`, and detailed `validation_errors`. Does **not** raise an unhandled exception. | Log `validation_errors`, mark job `FAILED`, and return `{"error": {"code": "INVALID_EVIDENCE_PAYLOAD", ...}}` or safe diagnostic message. |
| **Cloudy / stale / unavailable satellite imagery** | Returns `status="COMPLETED"` (if some valid NDVI exists, `confidence="LOW"`) or `status="PARTIAL"` (`confidence="INSUFFICIENT"`). | Persist and return the result normally so the farmer sees the honest inconclusive/low-confidence advisory and `limitations`. |
| **LLM / Amazon Bedrock unavailable or fails validation** | Automatically falls back to `generate_deterministic_report()` (`generation_mode="deterministic"`) and records a note in `validation_warnings`. | No retry storm needed; treat `COMPLETED` / `PARTIAL` with `generation_mode="deterministic"` as a valid, safe result. |
| **Unhandled exception in worker** | N/A | Catch at job worker boundary, mark job `FAILED` in DB, and return safe error shape without exposing stack traces or credentials. |

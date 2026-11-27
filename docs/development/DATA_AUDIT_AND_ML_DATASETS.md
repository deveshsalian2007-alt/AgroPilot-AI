# Real Data Audit, Production Safeguards & ML Dataset Feasibility

Last updated: 2026-11-27  
Scope: `agents-devesh/` and ML preparation for AgroPilot AI

---

## 1. Phase 1 — Data Usage Audit (`agents-devesh/`)

| Category | Exact Location | Purpose | Can Reach Production Reports? |
|---|---|---|---|
| **1. Synthetic Test Fixtures** | `agents-devesh/tests/synthetic_fixtures.py` (`SYNTHETIC_INTEGRATION_EVIDENCE`), `tests/test_agent_pipeline.py`, `tests/test_weather_tool.py`, `tests/smoke_test.py` (CLI default only) | Offline unit tests, fallback verification, and schema smoke checks | **No** in production code (`schemas/`, `tools/`, `reporter/`, `orchestrator/` never import `tests/`). Protected by `production_mode=True` safeguard. |
| **2. Real External Weather Data** | `agents-devesh/tools/weather_tool.py` (`fetch_open_meteo_weather`), `tests/test_live_weather_pipeline.py` (manual live test) | Queries Open-Meteo Archive & Forecast APIs for historical observations and upcoming forecasts | **Yes** (verified live for Vellore `12.9165, 79.1325`). Returns `UNAVAILABLE` / `PARTIAL` on API errors without fabricating numbers. |
| **3. Real Satellite / Geospatial Data** | None yet in `agents-devesh/` or `geospatial-snehendu/` (`geospatial-snehendu/` is empty scaffold) | `agents-devesh/` only validates and consumes satellite evidence supplied in `run_agent_pipeline(payload)` | N/A until Member 2 implements `geospatial-snehendu/`. |
| **4. ML / LLM Model Predictions** | `agents-devesh/reporter/llm_provider.py` (`BedrockLLMProvider` placeholder only) | Optional LLM narrative layer; currently raises `LLMUnavailableError` so deterministic templates run | **No** model predictions are active; all reports are deterministic and evidence-grounded. |

---

## 2. Phase 2 — Production Data Safeguards Implemented

1. **Strict `production_mode=True` Gate** (`tools/input_validator.py`, `orchestrator/pipeline.py`):
   - `detect_synthetic_markers()` checks `job_id`, `provenance.processing_version`, `provenance.sources`, `weather.provider`, and `ndvi.observations[*].source_id` for `synthetic`, `mock`, or `fixture`.
   - When `production_mode=True`:
     - Any synthetic marker fails validation (`status="FAILED"`).
     - Any measured numeric value with empty `provenance.sources` fails validation.
2. **Explicit Synthetic Labelling in Demo/Test Mode** (`production_mode=False`):
   - Adds `"Synthetic/test data detected — not real field observations."` to both `validation_warnings` and `report.limitations` so test fixtures can never be mistaken for real field observations.
3. **Missing Data & Provenance Integrity**:
   - Missing values stay `None` (`null`), never `0`.
   - Incomplete/cloudy/stale/unavailable imagery produces `LOW` or `INSUFFICIENT` confidence and `PARTIAL` status where appropriate.

---

## 3. Phase 3 — ML Dataset Feasibility Assessment

### A. Crop Stress Detection

| Candidate Dataset / Platform | Modalities & Labels | Suitability for Small Indian Farms | Feasibility & Caveats |
|---|---|---|---|
| **Microsoft Planetary Computer / Google Earth Engine (Sentinel-2 L2A)** | 10–20 m multispectral bands (B4, B8, Red-Edge), QA60/SCL cloud masks; custom NDVI/NDWI/NDRE time-series | **High** — covers India globally at 10 m resolution (smallholder plots) | **Best for custom regional data**, but requires field-level ground-truth stress labels (from local agronomy/extension or crop-cutting surveys). |
| **AI4Copernicus / Zenodo Spatiotemporal Sentinel-2 NDVI Datasets** | Sentinel-2 NDVI time-series and phenology extractions | **Medium** — good for NDVI anomaly / forecasting baselines (e.g., LSTM/temporal baseline) | Often trained on European/North American parcels; domain shift to Indian Kharif/Rabi cropping calendars must be validated. |
| **Mendeley Sentinel-1 SAR + Sentinel-2 NDVI Chips (512x512)** | Co-registered S1 SAR + S2 NDVI GeoTIFF chips | **Medium** — useful for cloud-gap filling (SAR when S2 is cloudy during monsoon) | Requires verification of crop-stress label granularity and regional representativeness. |
| **Kaggle Crop Health & Environmental Stress Datasets** | Tabular multispectral + weather/soil/NDVI features with stress labels | **Low–Medium** — quick prototyping for tabular classifiers | Often lacks spatial coordinates, provenance, or Indian smallholder validation; do not treat as production ground truth without provenance audit. |

**Recommendation for AgroPilot AI**: Start with **deterministic NDVI anomaly baselines** (using Sentinel-2 L2A via Planetary Computer/GEE + Open-Meteo weather context) before training a custom stress classifier, and collect verified local ground-truth labels for Tamil Nadu / Indian target districts before claiming ML stress classification.

### B. Flood / Water Inundation Detection

| Candidate Dataset | Modalities & Labels | Suitability for Small Indian Farms | Feasibility & Caveats |
|---|---|---|---|
| **Sen1Floods11** (Cloud to Street; GCS `gs://sen1floods11` / GitHub) | **Sentinel-1** (VV, VH backscatter in dB) + **Sentinel-2** (13 bands), 4,831 chips (512x512 @ 10 m) across 11 global flood events; hand-labeled water masks (`1` water, `0` non-water, `-1` invalid) + weak labels | **High** — Sentinel-1 penetrates monsoon cloud cover when optical Sentinel-2 is unusable | **Top public benchmark** (~14 GB). **Key agricultural caveat**: Paddy rice fields are intentionally flooded during early growth stages, so surface water detection ≠ crop damage. Model output must be framed as *surface-water screening* combined with crop calendar/weather, not automatic flood-damage confirmation. |

**Recommendation for AgroPilot AI**: Use **Sen1Floods11** to train/benchmark a lightweight Sentinel-1 VV/VH water-screening model (or calibrate VV backscatter thresholds) in `geospatial-snehendu/`, and keep `agents-devesh/` framing flood output strictly as surface-water screening with explicit paddy-field caveats.

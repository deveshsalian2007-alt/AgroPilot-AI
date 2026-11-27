# Development Handoff

Last updated: 2026-11-27

## Project
AgroPilot AI — satellite-based crop-risk advisor for small Indian farms.

## Ownership
- Member 1: `backend-amit/`, `infrastructure-amit/`
- Member 2: `geospatial-snehendu/`
- Member 3: `agents-devesh/`
- Member 4: `frontend-mehul/`
- `shared/` and architecture contracts require coordination.

## Last verified repository state
A VS Code Explorer screenshot showed the top-level folders and AI subfolders. This confirms visible folder names only. The actual code contents and Git status have not been inspected for this handoff.

## Current objective
Agree module boundaries and API/evidence interfaces before implementing tightly coupled features.

## Next steps
1. Inspect actual files and dependencies in every module.
2. Confirm backend and frontend framework/runtime.
3. Review `API_CONTRACT.md` with all members.
4. Members 2 and 3 finalise geospatial evidence schema.
5. Members 1 and 3 agree how backend invokes agents.
6. Member 3 builds a small deterministic reporter and tests it.
7. Update this file with actual changed files and test outcomes.

## Important cautions
The architecture/API docs are proposals until approved. Example JSON is placeholder data. Bedrock and satellite access must be verified. Inspect `git status` before switching branches or tools; preserve uncommitted work.

## Session checkpoint template
- Date/time: 2026-11-27T10:10+05:30
- Person/AI: Member 3 / Antigravity
- Branch: `feature/agents`
- Goal: Real data audit, production data safeguards (`production_mode`), and ML dataset feasibility assessment
- Files created/modified/deleted:
  - Created (this phase): `docs/development/DATA_AUDIT_AND_ML_DATASETS.md`
  - Modified (this phase): `agents-devesh/tools/input_validator.py`, `agents-devesh/orchestrator/pipeline.py`, `agents-devesh/tests/test_agent_pipeline.py`, `docs/development/HANDOFF.md`
- Completed / Integration readiness:
  - Audited all data sources in `agents-devesh/` (synthetic fixtures strictly isolated to `tests/`).
  - Added `production_mode=True` safeguard to `validate_raw_evidence()` and `run_agent_pipeline()` (rejects synthetic/mock/fixture markers and requires `provenance.sources` for measured values); non-production mode explicitly labels synthetic data in `validation_warnings` and `report.limitations`.
  - Documented ML dataset feasibility for crop stress (Sentinel-2 L2A / Planetary Computer / GEE, AI4Copernicus/Zenodo) and flood/water detection (`Sen1Floods11`).
- Tests and exact results:
  - `python -m unittest discover -s agents-devesh/tests -t agents-devesh -v` -> Ran 22 tests in 0.007s, OK (offline synthetic fixtures).
  - `python agents-devesh/tests/smoke_test.py` -> `SMOKE OK [SYNTHETIC_INTEGRATION_EVIDENCE]: job_id=synthetic-job-001 status=COMPLETED confidence=HIGH mode=deterministic`.
- Decisions awaiting Amit & Snehendu:
  - Amit: runtime/framework, direct Python call vs HTTP wrapper, Open-Meteo ownership, `AgentResult` -> API/DB mapping, job trigger/retrieval flow.
  - Snehendu: satellite evidence generation, exact NDVI/flood/imagery-quality/provenance/null fields, sample Sentinel-2/1 JSON payload.
- Errors/blockers: `boto3`/Bedrock unverified; `backend-amit/` and `geospatial-snehendu/` not yet implemented.
- Exact next task: Test Snehendu's first real or sample Sentinel-2/1 evidence JSON using `python agents-devesh/tests/smoke_test.py <path/to/evidence.json>` and lock the schema in `shared/api_schemas/`.

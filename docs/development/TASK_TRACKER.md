# Task Tracker

Statuses: TODO / IN_PROGRESS / BLOCKED / DONE. Do not mark DONE without evidence.

## Cross-team
- [ ] Confirm folder ownership and branch names — All
- [ ] Agree API contract — Members 1, 2, 3, 4
- [ ] Agree geospatial evidence schema, units, dates and null semantics — Members 2 and 3
- [ ] Agree backend-to-agent invocation — Members 1 and 3
- [ ] Verify demo crop, district, dates and usable imagery — Members 2 and 3
- [ ] Verify AWS permissions, budget alerts and deployment approach — Member 1

## Member 1 — Backend and Cloud
- [ ] Confirm backend framework/runtime.
- [ ] Define request validation and job lifecycle.
- [ ] Define persistence model and access patterns.
- [ ] Implement agreed API endpoints.
- [ ] Configure secure AWS infrastructure and deployment.
- [ ] Add logging, error handling and budget monitoring.

## Member 2 — Geospatial
- [ ] Confirm initial area, crop and date range.
- [ ] Verify Sentinel-2 observations and data access.
- [ ] Implement geometry validation and imagery quality checks.
- [ ] Calculate NDVI with documented aggregation.
- [ ] Implement historical comparison/anomaly logic.
- [ ] Evaluate Sentinel-1 potential inundation method.
- [ ] Return evidence using agreed schema.

## Member 3 — AI and Agents
- [x] Inspect existing `agents-devesh/` code and dependencies.
- [ ] Agree evidence schema with Member 2.
- [ ] Agree invocation interface with Member 1.
- [x] Implement input validation and normalisation.
- [x] Implement deterministic report fallback.
- [ ] Verify Bedrock access; add provider adapter if feasible. (Interface & placeholder `BedrockLLMProvider` added; live Bedrock call pending verification)
- [x] Implement orchestrator and report generation. (Deterministic pipeline complete; live LLM integration pending)
- [x] Add evidence-grounding and output-validation tests.
- [x] Test English and Tamil output. (Verified with synthetic test fixtures)
- [ ] Integrate with backend and test failure paths.

## Member 4 — Frontend
- [ ] Confirm frontend framework and run instructions.
- [ ] Implement field selection/drawing.
- [ ] Add crop, date and language inputs.
- [ ] Integrate create-job/status/result APIs.
- [ ] Display approved indicators and observation dates.
- [ ] Display report, confidence and limitations.
- [ ] Test loading, error and responsive states.

## End-to-end acceptance
- [ ] Valid field request creates a job.
- [ ] Geospatial returns real quality-checked observations.
- [ ] Weather is included or clearly marked unavailable.
- [ ] Reporter uses only supplied evidence.
- [ ] Frontend displays metrics, report and limitations.
- [ ] No secrets are committed.
- [ ] Demo can be repeated reliably.

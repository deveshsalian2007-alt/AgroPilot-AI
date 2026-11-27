# AgroPilot AI — Coding Agent Instructions

## AI Tool Compatibility

These instructions are the shared project rules for all AI assistants and coding agents working on this repository, including OpenAI Codex, Google Antigravity, Claude, and ChatGPT.

Before making changes:
1. Read this `AGENTS.md` file.
2. Read the relevant documentation under `docs/`.
3. Inspect the actual repository structure and existing code.
4. Follow the same project rules regardless of which AI tool is being used.
5. If your tool cannot access a file or perform an action, explain the limitation instead of assuming it was completed.

Do not assume that another AI assistant has access to your conversation history or previous work. Use the project's documentation and handoff files to recover context.

## 1. Project Overview

AgroPilot AI is a satellite-based crop-risk advisor for small Indian farms.

It combines satellite-derived indicators and weather context into an understandable, evidence-based report for farmers.

The system must not claim confirmed disease diagnosis or prescribe treatments.

All AI coding agents must follow the instructions in this file when working on the project.

## 2. Repository Structure and Team Ownership

| Folder | Responsibility | Owner |
|---|---|---|
| `agents-devesh/` | AI agents, orchestration, schemas, reports and tests | Member 3 – Devesh |
| `backend-amit/` | Backend APIs, jobs, persistence and integrations | Member 1 – Amit |
| `infrastructure-amit/` | AWS, IAM, deployment, monitoring and budgets | Member 1 – Amit |
| `geospatial-snehendu/` | Satellite retrieval and geospatial processing | Member 2 – Snehendu |
| `frontend-mehul/` | Web UI, field map, charts and report display | Member 4 – Mehul |
| `shared/` | Cross-module contracts and common schemas | All members |
| `docs/` | Project documentation and development tracking | All members |

Work mainly in the folder assigned to the task.

Do not rename, restructure or modify another member's module without discussing it with the respective owner.

### Member 3 – AI Module Scope

The primary assigned module is `agents-devesh/`.

The AI module is responsible for:

- AI orchestrator.
- Agent tools and integrations.
- Evidence validation.
- Report generation.
- English and Tamil farmer-friendly output.
- LLM integration and deterministic fallback.
- AI-related schemas and tests.

Coordinate with:

- Member 1 for backend-to-agent integration.
- Member 2 for satellite evidence and data schemas.
- Member 4 for report output and frontend integration.

## 3. Before Starting Any Task

Every coding agent must:

1. Inspect the repository structure.
2. Check the current Git branch and `git status`.
3. Read this file and relevant documentation under `docs/`.
4. Inspect existing code before creating new files.
5. Understand how the requested feature connects to other modules.
6. Explain the proposed implementation plan.
7. Identify files that will be created or modified.
8. Ask before major architecture changes, destructive operations or edits outside the assigned scope.

Do not assume that a feature exists simply because it is described in project documentation.

## 4. Git and Collaboration Rules

- Work on the assigned feature branch.
- Never directly modify `main` unless explicitly instructed.
- Do not overwrite or discard another member's changes.
- Check for uncommitted changes before switching branches.
- Do not force-push or rewrite shared Git history.
- Use Pull Requests for integrating work into `main`.
- Do not commit, push or merge without explicit permission.
- Coordinate changes to shared files and schemas with affected members.

## 5. Engineering Rules

1. Preserve existing working code.
2. Make small, modular and reviewable changes.
3. Never invent satellite observations, weather values, test results or deployment status.
4. Numeric raster and geospatial calculations must use deterministic code, not LLM guesses.
5. Reports must distinguish observations from interpretations.
6. Reports must include confidence and limitations.
7. Missing data must remain missing; never silently convert `null` to zero.
8. If imagery is cloudy, stale or unavailable, report inconclusive results.
9. Do not diagnose crop diseases.
10. Do not prescribe pesticides, fertilisers or treatments.
11. Validate inputs and outputs.
12. Add tests for meaningful functionality.
13. Never claim code works unless it has actually been tested.
14. Report exact commands and test results.
15. Never commit `.env`, AWS credentials, API tokens or private keys.
16. `.env.example` must contain placeholders only.
17. Coordinate API and evidence contract changes with affected members.
18. Do not introduce duplicate folders, modules or files without checking existing structure.
19. Do not add dependencies without explaining why and updating the appropriate dependency file.

## 6. Cross-Module Communication

The modules depend on each other. Coding agents must respect the agreed interfaces.

- Frontend and backend must agree on API endpoints and request/response formats.
- Backend and geospatial must agree on analysis-job inputs, outputs, status and error handling.
- Backend and AI agents must agree on how the backend invokes the agent workflow.
- Geospatial and AI agents must agree on evidence JSON structure, units, timestamps, quality flags and data sources.
- Shared schemas should be maintained in `shared/`.
- Approved interfaces must be documented in `docs/architecture/API_CONTRACT.md`.

Do not independently change a shared contract.

## 7. AI and Data Reliability Rules

- Use LLMs for interpreting and explaining verified evidence, not calculating satellite measurements.
- Never fabricate NDVI values, rainfall measurements or flood indicators.
- Preserve original measurement values and units.
- Identify the source and observation date wherever possible.
- Distinguish actual measurements from possible interpretations.
- Include uncertainty when the available evidence is insufficient.
- Use deterministic templates if the LLM is unavailable or fails validation.
- Amazon Bedrock access must be verified before depending on it.

## 8. Project Documentation

Read relevant documentation before implementing a feature.

Important documents:

### Project information
- `docs/proposal/PROJECT_OVERVIEW.md`
- `docs/proposal/TECH_STACK.md`
- `docs/proposal/TEAM_ROLES.md`

### Architecture
- `docs/architecture/SYSTEM_ARCHITECTURE.md`
- `docs/architecture/DATA_FLOW.md`
- `docs/architecture/API_CONTRACT.md`
- `docs/architecture/DATABASE_SCHEMA.md`
- `docs/architecture/AGENT_WORKFLOW.md`

### Development tracking
- `docs/development/PROJECT_STATUS.md`
- `docs/development/TASK_TRACKER.md`
- `docs/development/HANDOFF.md`
- `docs/development/DECISIONS.md`
- `docs/development/KNOWN_ISSUES.md`

Documentation must reflect actual implementation. Do not mark proposed or planned features as completed.

## 9. Progress and Context Management

At the end of every major development task:

1. Update `PROJECT_STATUS.md`.
2. Update `TASK_TRACKER.md`.
3. Update `HANDOFF.md` when substantial progress has been made.

Before a long session ends or context limits approach:

- Inspect the actual source files.
- Record completed and incomplete work.
- Record files created and modified.
- Record errors and test results.
- Identify unfinished functions and partially implemented features.
- Document the exact next steps.
- Preserve all unfinished code.

Do not rely only on conversation memory when preparing a handoff.

If the AI context or usage limit is approaching, prioritise saving progress and updating documentation before starting another implementation task.

## 10. Before Finishing Any Task

Every coding agent must:

1. Run relevant tests or checks.
2. Inspect `git diff` and `git status`.
3. List files created, modified and deleted.
4. Explain what was completed.
5. Explain what remains incomplete.
6. Report any errors or blockers.
7. State which tests were actually performed and their results.
8. Update relevant project documentation.
9. Provide clear next steps.

Never commit, push, merge or deploy without explicit user permission.

## 11. Important Final Rule

The actual repository code is the source of truth for implementation.

Project documentation provides context and intended design, but it must not be treated as proof that a feature has been implemented.

If documentation conflicts with actual code or a newer team decision:

- Identify the conflict.
- Explain the difference.
- Ask for clarification.
- Do not guess or silently overwrite existing decisions.

All AI agents must prioritise code safety, collaboration, consistency and reliable project progress.
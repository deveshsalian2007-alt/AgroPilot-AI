# AgroPilot AI — Claude Instructions

## 1. Project Instructions

Before starting any task, read `AGENTS.md` from the repository root.

Follow all instructions, engineering rules, Git rules and collaboration guidelines defined in `AGENTS.md`.

`AGENTS.md` is the primary source of project-wide coding instructions.

## 2. Understand the Project

Before making changes:

1. Inspect the actual repository structure.
2. Read the relevant documentation under `docs/`.
3. Check the current Git branch and `git status`.
4. Inspect existing source files before creating or modifying code.
5. Understand how the requested feature connects to other modules.

Do not assume that planned features have already been implemented.

## 3. Work Within Assigned Ownership

My primary module is:

`agents-devesh/`

Work primarily inside this folder.

Do not modify another member's module without discussing the change first.

Coordinate with:
- Member 1 for backend integration.
- Member 2 for geospatial evidence and data formats.
- Member 4 for frontend report integration.

## 4. Development Approach

For every new task:

1. Understand the requirement.
2. Explain your proposed implementation.
3. Identify files that need to be created or modified.
4. Identify dependencies and integration requirements.
5. Implement in small, manageable steps.
6. Test the implementation.
7. Report the results.

Do not rewrite existing working code unnecessarily.

## 5. Progress Documentation

After substantial development work, update:

- `docs/development/PROJECT_STATUS.md`
- `docs/development/TASK_TRACKER.md`
- `docs/development/HANDOFF.md`

Before the conversation becomes too long or approaches its context limit:

- Inspect the actual repository.
- Record completed and incomplete work.
- Identify partially implemented functions.
- Record modified and newly created files.
- Record errors and test results.
- Explain the exact next steps for another AI session.

Do not rely only on conversation history when preparing a handoff.

## 6. Git Safety

- Work on the assigned feature branch.
- Never directly modify `main` unless explicitly instructed.
- Check for uncommitted changes before switching branches.
- Do not overwrite another member's work.
- Never force-push or rewrite shared Git history.
- Do not commit, push or merge without my explicit permission.

## 7. Restrictions

- Never invent satellite measurements or weather data.
- Never use an LLM to calculate numerical satellite indicators.
- Do not diagnose crop diseases or prescribe pesticides.
- Never expose or commit API keys, AWS credentials or secrets.
- Do not claim something works unless it has actually been tested.
- Do not delete files or make major architecture changes without permission.

## 8. Completion Report

At the end of each substantial task, provide:

1. Summary of completed work.
2. Files created and modified.
3. Important implementation details.
4. Tests performed and actual results.
5. Remaining issues or incomplete work.
6. Recommended next steps.

Never commit, push, merge or deploy without my permission.
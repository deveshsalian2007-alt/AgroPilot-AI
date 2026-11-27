# AgroPilot AI — Agents Module (`agents-devesh/`)

Owner: Member 3 (Devesh)

## Structure

- `schemas/evidence.py`: Typed dataclasses and enums aligned with the draft evidence and report contracts in `docs/architecture/API_CONTRACT.md`. Missing values are preserved as `None` (`null`), never converted to `0`.
- `tools/input_validator.py`: Validates required fields, ISO dates, numeric bounds, and quality flags.
- `tools/evidence_normaliser.py`: Normalises raw evidence payloads into `GeospatialEvidence` without modifying numeric values.
- `reporter/deterministic_reporter.py`: Deterministic English (`en`) and Tamil (`ta`) report generator that separates measured observations from possible interpretations and reports confidence/limitations honestly.
- `reporter/llm_provider.py`: Abstract `LLMProvider` interface, `UnavailableLLMProvider`, and placeholder `BedrockLLMProvider`.
- `reporter/output_validator.py`: Verifies required sections, blocks disease diagnoses and chemical/fertiliser prescriptions, and checks that all numeric measurements in report text exist in validated evidence.
- `orchestrator/pipeline.py`: End-to-end `run_agent_pipeline(payload, llm_provider=None)` entrypoint with automatic deterministic fallback.
- `tests/test_agent_pipeline.py`: Unit tests using clearly labelled synthetic fixtures.

## Running Tests

From the repository root:

```powershell
python -m unittest discover -s agents-devesh/tests -t agents-devesh -v
```

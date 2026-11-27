"""Lightweight integration smoke test for agents-devesh/.

Usage:
    python agents-devesh/tests/smoke_test.py
    python agents-devesh/tests/smoke_test.py path/to/geospatial_evidence.json

When no file path is passed, runs against the clearly labelled synthetic
integration fixture in tests/synthetic_fixtures.py.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_AGENTS_DIR = Path(__file__).resolve().parents[1]
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))

from orchestrator.pipeline import run_agent_pipeline  # noqa: E402
from tests.synthetic_fixtures import make_synthetic_evidence  # noqa: E402

REQUIRED_RESULT_KEYS = {
    "job_id",
    "status",
    "report",
    "validation_errors",
    "validation_warnings",
    "sources",
}


def run_smoke_check(payload: dict[str, Any]) -> dict[str, Any]:
    """Run payload through run_agent_pipeline and verify backend JSON contract."""
    result = run_agent_pipeline(payload)
    serialized = json.dumps(result.to_dict(), ensure_ascii=False)
    decoded = json.loads(serialized)

    missing = REQUIRED_RESULT_KEYS - set(decoded.keys())
    if missing:
        raise AssertionError(f"Result JSON missing required backend keys: {sorted(missing)}")

    if decoded["status"] == "FAILED":
        raise AssertionError(f"Smoke check failed validation: {decoded['validation_errors']}")

    report = decoded["report"]
    if not isinstance(report, dict) or not report.get("summary"):
        raise AssertionError("Expected non-empty report object in non-FAILED result.")

    return decoded


def main(argv: list[str]) -> int:
    if len(argv) > 1:
        evidence_path = Path(argv[1])
        payload = json.loads(evidence_path.read_text(encoding="utf-8"))
        source_label = str(evidence_path)
    else:
        payload = make_synthetic_evidence()
        source_label = "SYNTHETIC_INTEGRATION_EVIDENCE"

    decoded = run_smoke_check(payload)
    print(
        f"SMOKE OK [{source_label}]: job_id={decoded['job_id']} "
        f"status={decoded['status']} confidence={decoded['report']['confidence']} "
        f"mode={decoded['report']['generation_mode']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

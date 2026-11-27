"""AgroPilot AI — Agent & Reporting Module (Member 3: Devesh)."""

import sys
from pathlib import Path

_MODULE_DIR = str(Path(__file__).resolve().parent)
if _MODULE_DIR not in sys.path:
    sys.path.insert(0, _MODULE_DIR)

from orchestrator.pipeline import run_agent_pipeline  # noqa: E402
from reporter.deterministic_reporter import generate_deterministic_report  # noqa: E402
from schemas.evidence import AgentResult, FarmerReport, GeospatialEvidence  # noqa: E402

__all__ = [
    "AgentResult",
    "FarmerReport",
    "GeospatialEvidence",
    "generate_deterministic_report",
    "run_agent_pipeline",
]

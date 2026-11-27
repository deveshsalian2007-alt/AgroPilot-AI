"""Unit tests for input validation, normalisation, deterministic reporting,
output safety/grounding validation, and orchestrator fallback behaviour.

All payloads in this file are SYNTHETIC TEST FIXTURES, not real satellite observations.
"""

from __future__ import annotations

import json
import math
import unittest

from orchestrator.pipeline import run_agent_pipeline
from reporter.llm_provider import LLMProvider
from reporter.output_validator import validate_report_output
from schemas.evidence import FarmerReport, GeospatialEvidence, ReportFinding
from tests.smoke_test import run_smoke_check
from tests.synthetic_fixtures import make_synthetic_evidence
from tools.evidence_normaliser import normalise_evidence
from tools.input_validator import validate_raw_evidence


class _HallucinatingNumberLLM(LLMProvider):
    def generate_report(self, evidence: GeospatialEvidence) -> FarmerReport:
        return FarmerReport(
            language="en",
            summary="Synthetic crop NDVI dropped to 0.41 with 999 mm rainfall.",
            findings=[
                ReportFinding(
                    indicator="ndvi",
                    observation="Measured NDVI was 0.41.",
                    interpretation="Possible stress.",
                )
            ],
            confidence="HIGH",
            limitations=["None"],
            generation_mode="llm",
            disclaimers=["Not a diagnosis."],
        )


class _UnsafeDiagnosisLLM(LLMProvider):
    def generate_report(self, evidence: GeospatialEvidence) -> FarmerReport:
        return FarmerReport(
            language="en",
            summary="The crop has a confirmed disease and you should apply pesticide at 2 kg/ha.",
            findings=[
                ReportFinding(
                    indicator="ndvi",
                    observation="NDVI mean is 0.62.",
                    interpretation="Crop is diagnosed with leaf blight; spray fungicide immediately.",
                )
            ],
            confidence="HIGH",
            limitations=[],
            generation_mode="llm",
            disclaimers=["Advisory only."],
        )


class _InvalidConfidenceLLM(LLMProvider):
    def generate_report(self, evidence: GeospatialEvidence) -> FarmerReport:
        return FarmerReport(
            language="en",
            summary="Paddy NDVI mean on 2026-10-15 was 0.62.",
            findings=[
                ReportFinding(
                    indicator="ndvi",
                    observation="Mean NDVI on 2026-10-15 was 0.62.",
                    interpretation="Inspect field directly.",
                    observation_date="2026-10-15",
                )
            ],
            confidence="CERTAIN",
            limitations=[],
            generation_mode="llm",
            disclaimers=["Advisory only."],
        )


class _WrongLanguageLLM(LLMProvider):
    def generate_report(self, evidence: GeospatialEvidence) -> FarmerReport:
        return FarmerReport(
            language="ta",
            summary="Paddy NDVI mean on 2026-10-15 was 0.62.",
            findings=[
                ReportFinding(
                    indicator="ndvi",
                    observation="Mean NDVI on 2026-10-15 was 0.62.",
                    interpretation="Inspect field directly.",
                    observation_date="2026-10-15",
                )
            ],
            confidence="HIGH",
            limitations=[],
            generation_mode="llm",
            disclaimers=["Advisory only."],
        )


class _ValidGroundedLLM(LLMProvider):
    def generate_report(self, evidence: GeospatialEvidence) -> FarmerReport:
        return FarmerReport(
            language="en",
            summary="Paddy NDVI changed by -0.09 (-12.68%) to mean 0.62 on 2026-10-15.",
            findings=[
                ReportFinding(
                    indicator="ndvi",
                    observation="Mean NDVI on 2026-10-15 was 0.62 (median 0.64).",
                    interpretation="Greenness decreased compared to 2026-10-01; inspect field conditions.",
                    observation_date="2026-10-15",
                )
            ],
            confidence="HIGH",
            limitations=["Synthetic test fixture only."],
            generation_mode="llm",
            disclaimers=["Not a confirmed disease diagnosis; do not apply chemicals based solely on this report."],
        )


class TestAgentPipeline(unittest.TestCase):
    def test_valid_english_deterministic_pipeline_and_json_contract(self) -> None:
        result = run_agent_pipeline(make_synthetic_evidence())
        self.assertEqual(result.status, "COMPLETED")
        self.assertEqual(result.validation_errors, [])
        self.assertIsNotNone(result.report)
        assert result.report is not None
        self.assertEqual(result.report.language, "en")
        self.assertEqual(result.report.confidence, "HIGH")
        self.assertEqual(result.report.generation_mode, "deterministic")
        ndvi_finding = next(f for f in result.report.findings if f.indicator == "ndvi")
        self.assertIn("2026-10-15", ndvi_finding.observation)
        self.assertIn("0.62", ndvi_finding.observation)
        self.assertIn("18.4 mm", " ".join(f.observation for f in result.report.findings))

        decoded = json.loads(json.dumps(result.to_dict(), ensure_ascii=False))
        self.assertEqual(decoded["job_id"], "synthetic-job-001")
        self.assertEqual(decoded["report"]["confidence"], "HIGH")

    def test_valid_tamil_deterministic_pipeline(self) -> None:
        result = run_agent_pipeline(make_synthetic_evidence(language="ta"))
        self.assertEqual(result.status, "COMPLETED")
        self.assertIsNotNone(result.report)
        assert result.report is not None
        self.assertEqual(result.report.language, "ta")
        self.assertIn("NDVI", result.report.summary + " ".join(f.observation for f in result.report.findings))
        self.assertTrue(len(result.report.disclaimers) >= 2)

    def test_missing_ndvi_observations_returns_insufficient_and_partial(self) -> None:
        payload = make_synthetic_evidence()
        payload["ndvi"] = {"observations": [], "change": None}
        result = run_agent_pipeline(payload)
        self.assertEqual(result.status, "PARTIAL")
        assert result.report is not None
        self.assertEqual(result.report.confidence, "INSUFFICIENT")
        self.assertTrue(any("No NDVI observations" in w for w in result.validation_warnings))

    def test_stale_imagery_produces_low_confidence_and_limitation(self) -> None:
        payload = make_synthetic_evidence()
        payload["imagery_quality"]["status"] = "STALE"
        result = run_agent_pipeline(payload)
        self.assertEqual(result.status, "COMPLETED")
        assert result.report is not None
        self.assertEqual(result.report.confidence, "LOW")
        self.assertTrue(any("STALE" in item for item in result.report.limitations))

    def test_missing_weather_data_preserves_null_and_caps_confidence(self) -> None:
        payload = make_synthetic_evidence()
        payload["weather"] = {
            "status": "UNAVAILABLE",
            "provider": None,
            "rainfall_mm": None,
            "retrieved_at": None,
            "limitations": [],
        }
        result = run_agent_pipeline(payload)
        self.assertEqual(result.status, "COMPLETED")
        assert result.report is not None
        self.assertEqual(result.report.confidence, "MEDIUM")
        weather_finding = next(f for f in result.report.findings if f.indicator == "weather")
        self.assertIn("unavailable", weather_finding.observation.lower())

    def test_null_values_are_preserved_not_zeroed(self) -> None:
        payload = make_synthetic_evidence()
        payload["imagery_quality"]["valid_pixel_percent"] = None
        payload["weather"] = {"status": "UNAVAILABLE", "provider": None, "rainfall_mm": None}
        payload["ndvi"]["observations"] = [
            {"date": "2026-10-15", "mean": None, "median": None, "source_id": "SYNTHETIC-S2-B"}
        ]
        payload["ndvi"]["change"] = {"absolute": None, "percent": None, "method": None}

        evidence = normalise_evidence(payload)
        self.assertIsNone(evidence.imagery_quality.valid_pixel_percent)
        self.assertIsNone(evidence.weather.rainfall_mm)
        self.assertIsNone(evidence.ndvi.observations[0].mean)
        self.assertIsNone(evidence.ndvi.change.absolute)

        result = run_agent_pipeline(payload)
        self.assertEqual(result.status, "PARTIAL")
        assert result.report is not None
        self.assertEqual(result.report.confidence, "INSUFFICIENT")

    def test_cloudy_imagery_produces_low_confidence(self) -> None:
        payload = make_synthetic_evidence()
        payload["imagery_quality"]["status"] = "CLOUDY"
        payload["imagery_quality"]["valid_pixel_percent"] = 22.0
        result = run_agent_pipeline(payload)
        self.assertEqual(result.status, "COMPLETED")
        assert result.report is not None
        self.assertEqual(result.report.confidence, "LOW")
        self.assertTrue(any("CLOUDY" in item for item in result.report.limitations))

    def test_malformed_and_invalid_inputs_are_rejected(self) -> None:
        non_dict_result = run_agent_pipeline(["not", "a", "dict"])  # type: ignore[arg-type]
        self.assertEqual(non_dict_result.status, "FAILED")
        self.assertIsNone(non_dict_result.report)

        missing_keys_check = validate_raw_evidence({"job_id": ""})
        self.assertFalse(missing_keys_check.is_valid)
        self.assertGreaterEqual(len(missing_keys_check.errors), 5)

        bad_payload = make_synthetic_evidence(language="fr")
        bad_payload["ndvi"]["observations"][0]["mean"] = 1.8
        bad_payload["ndvi"]["observations"][1]["date"] = "15-10-2026"
        bad_payload["ndvi"]["change"]["absolute"] = math.nan
        bad_payload["weather"]["rainfall_mm"] = True
        bad_payload["provenance"]["sources"] = "not-a-list"

        check = validate_raw_evidence(bad_payload)
        self.assertFalse(check.is_valid)
        self.assertGreaterEqual(len(check.errors), 5)

        result = run_agent_pipeline(bad_payload)
        self.assertEqual(result.status, "FAILED")
        self.assertIsNone(result.report)

    def test_invalid_confidence_and_wrong_language_llm_fallback(self) -> None:
        bad_conf = run_agent_pipeline(make_synthetic_evidence(), llm_provider=_InvalidConfidenceLLM())
        self.assertEqual(bad_conf.status, "COMPLETED")
        assert bad_conf.report is not None
        self.assertEqual(bad_conf.report.generation_mode, "deterministic")
        self.assertTrue(any("Invalid report confidence" in w for w in bad_conf.validation_warnings))

        wrong_lang = run_agent_pipeline(make_synthetic_evidence(), llm_provider=_WrongLanguageLLM())
        self.assertEqual(wrong_lang.status, "COMPLETED")
        assert wrong_lang.report is not None
        self.assertEqual(wrong_lang.report.generation_mode, "deterministic")
        self.assertTrue(any("does not match requested" in w for w in wrong_lang.validation_warnings))

    def test_hallucinated_llm_numbers_trigger_deterministic_fallback(self) -> None:
        result = run_agent_pipeline(make_synthetic_evidence(), llm_provider=_HallucinatingNumberLLM())
        self.assertEqual(result.status, "COMPLETED")
        assert result.report is not None
        self.assertEqual(result.report.generation_mode, "deterministic")
        self.assertTrue(any("failed safety/grounding validation" in w for w in result.validation_warnings))

    def test_unsafe_diagnosis_llm_triggers_deterministic_fallback(self) -> None:
        result = run_agent_pipeline(make_synthetic_evidence(), llm_provider=_UnsafeDiagnosisLLM())
        self.assertEqual(result.status, "COMPLETED")
        assert result.report is not None
        self.assertEqual(result.report.generation_mode, "deterministic")
        self.assertTrue(any("Forbidden diagnostic or prescriptive phrase" in w for w in result.validation_warnings))

    def test_valid_grounded_llm_is_accepted(self) -> None:
        evidence = normalise_evidence(make_synthetic_evidence())
        llm_report = _ValidGroundedLLM().generate_report(evidence)
        check = validate_report_output(llm_report, evidence)
        self.assertTrue(check.is_valid, msg=f"Unexpected violations: {check.violations}")

        result = run_agent_pipeline(make_synthetic_evidence(), llm_provider=_ValidGroundedLLM())
        self.assertEqual(result.status, "COMPLETED")
        assert result.report is not None
        self.assertEqual(result.report.generation_mode, "llm")

    def test_smoke_check_helper_passes_on_synthetic_fixture(self) -> None:
        decoded = run_smoke_check(make_synthetic_evidence())
        self.assertEqual(decoded["status"], "COMPLETED")

    def test_production_mode_rejects_synthetic_data_and_missing_provenance(self) -> None:
        syn_result = run_agent_pipeline(make_synthetic_evidence(), production_mode=True)
        self.assertEqual(syn_result.status, "FAILED")
        self.assertIsNone(syn_result.report)
        self.assertTrue(any("production_mode" in e for e in syn_result.validation_errors))

        real_looking = make_synthetic_evidence(job_id="real-job-001")
        real_looking["ndvi"]["observations"] = [
            {"date": "2026-10-15", "mean": 0.62, "median": 0.64, "source_id": "S2B_MSIL2A_20261015"}
        ]
        real_looking["weather"]["provider"] = "open-meteo"
        real_looking["provenance"] = {"generated_at": "2026-10-16T06:00:00Z", "processing_version": "0.1.0", "sources": []}
        no_prov_result = run_agent_pipeline(real_looking, production_mode=True)
        self.assertEqual(no_prov_result.status, "FAILED")
        self.assertTrue(any("Provenance sources" in e for e in no_prov_result.validation_errors))

        real_looking["provenance"]["sources"] = ["S2B_MSIL2A_20261015", "open-meteo"]
        ok_result = run_agent_pipeline(real_looking, production_mode=True)
        self.assertEqual(ok_result.status, "COMPLETED")

    def test_non_production_mode_labels_synthetic_data_explicitly(self) -> None:
        result = run_agent_pipeline(make_synthetic_evidence(), production_mode=False)
        self.assertEqual(result.status, "COMPLETED")
        assert result.report is not None
        self.assertTrue(any("Synthetic/test data detected" in w for w in result.validation_warnings))
        self.assertTrue(any("Synthetic/test data detected" in lim for lim in result.report.limitations))


if __name__ == "__main__":
    unittest.main()

import hashlib
import tempfile
import unittest
from pathlib import Path

from sharpicks_contracts import (
    CONTRACT_VERSION,
    ContractError,
    InputArtifact,
    PublicPrediction,
    RunRequest,
    RunResult,
    dump_json,
    load_json,
    verify_artifact,
)


def artifact_payload(name="matches", data=b"sample"):
    return {
        "name": name,
        "version": "1.2.3",
        "sha256": hashlib.sha256(data).hexdigest(),
        "size_bytes": len(data),
        "classification": "private",
    }


def request_payload():
    return {
        "contract_version": CONTRACT_VERSION,
        "run_id": "00000000-0000-4000-8000-000000000001",
        "as_of_utc": "2026-10-30T12:00:00Z",
        "sport_scope": ["soccer"],
        "window_start_utc": "2026-10-30T00:00:00Z",
        "window_end_utc": "2026-10-31T00:00:00Z",
        "input_manifest": [artifact_payload()],
        "parameters": {"mode": "shadow", "limit": 20},
        "requested_outputs": ["predictions", "public_web_export"],
    }


def prediction_payload():
    return {
        "event_id": "evt-001",
        "sport": "soccer",
        "league": "liga-mx",
        "market": "1x2",
        "selection": "home",
        "probability": 0.61,
        "decimal_odds": 1.9,
        "tier": "public",
        "as_of_utc": "2026-10-30T12:00:00Z",
    }


def result_payload(status="success", predictions=None):
    return {
        "contract_version": CONTRACT_VERSION,
        "run_id": "00000000-0000-4000-8000-000000000001",
        "status": status,
        "started_at_utc": "2026-10-30T12:01:00Z",
        "completed_at_utc": "2026-10-30T12:02:00Z",
        "core_version": "1.0.0",
        "core_commit": "a" * 40,
        "input_manifest": [artifact_payload()],
        "output_manifest": [],
        "public_predictions": predictions or [],
        "warnings": [],
    }


class ContractTests(unittest.TestCase):
    def test_request_round_trip_and_utc_normalization(self):
        request = RunRequest.from_dict(request_payload())
        self.assertEqual(request.as_of_utc, "2026-10-30T12:00:00Z")
        self.assertEqual(RunRequest.from_dict(load_json(dump_json(request))), request)

    def test_request_rejects_unknown_fields_and_future_version(self):
        payload = request_payload()
        payload["private_path"] = "C:/private/model.joblib"
        with self.assertRaises(ContractError):
            RunRequest.from_dict(payload)
        payload = request_payload()
        payload["contract_version"] = "2.0.0"
        with self.assertRaises(ContractError):
            RunRequest.from_dict(payload)

    def test_request_rejects_non_utc_or_non_rfc3339(self):
        payload = request_payload()
        payload["as_of_utc"] = "2026-10-30T12:00:00-06:00"
        with self.assertRaises(ContractError):
            RunRequest.from_dict(payload)
        payload = request_payload()
        payload["as_of_utc"] = "2026-10-30 12:00:00Z"
        with self.assertRaises(ContractError):
            RunRequest.from_dict(payload)

    def test_request_rejects_secrets_in_parameters(self):
        payload = request_payload()
        payload["parameters"] = {"nested": {"api_key": "never-accepted"}}
        with self.assertRaises(ContractError):
            RunRequest.from_dict(payload)

    def test_request_rejects_duplicate_artifact_names(self):
        payload = request_payload()
        payload["input_manifest"].append(artifact_payload())
        with self.assertRaises(ContractError):
            RunRequest.from_dict(payload)

    def test_request_rejects_inverted_window(self):
        payload = request_payload()
        payload["window_start_utc"], payload["window_end_utc"] = payload["window_end_utc"], payload["window_start_utc"]
        with self.assertRaises(ContractError):
            RunRequest.from_dict(payload)

    def test_duplicate_json_keys_are_rejected(self):
        with self.assertRaises(ContractError):
            load_json('{"contract_version":"1.0.0","contract_version":"2.0.0"}')

    def test_prediction_allowlist_and_probability_bounds(self):
        prediction = PublicPrediction.from_dict(prediction_payload())
        self.assertEqual(set(prediction.to_dict()), set(prediction_payload()))
        bad = prediction_payload()
        bad["probability"] = 1.01
        with self.assertRaises(ContractError):
            PublicPrediction.from_dict(bad)
        bad = prediction_payload()
        bad["internal_score"] = 0.99
        with self.assertRaises(ContractError):
            PublicPrediction.from_dict(bad)

    def test_partial_or_failed_result_cannot_contain_predictions(self):
        self.assertTrue(RunResult.from_dict(result_payload()).publishable)
        self.assertFalse(RunResult.from_dict(result_payload(status="partial")).publishable)
        with self.assertRaises(ContractError):
            RunResult.from_dict(result_payload(status="partial", predictions=[prediction_payload()]))

    def test_serializer_validates_direct_dataclass_construction(self):
        request = RunRequest.from_dict(request_payload())
        invalid = RunRequest(**{**request.__dict__, "contract_version": "2.0.0"})
        with self.assertRaises(ContractError):
            dump_json(invalid)

    def test_artifact_checksum_and_size_are_verified(self):
        data = b"sample"
        artifact = InputArtifact.from_dict(artifact_payload(data=data))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.bin"
            path.write_bytes(data)
            verify_artifact(path, artifact, chunk_size=2)
            path.write_bytes(b"changed")
            with self.assertRaises(ContractError):
                verify_artifact(path, artifact)


if __name__ == "__main__":
    unittest.main()

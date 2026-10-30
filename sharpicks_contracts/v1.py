"""Version 1 JSON contract between the public orchestrator and private core.

This module uses only the Python standard library. Unknown fields are rejected
to keep the public payload allowlisted and make incompatible changes explicit.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from uuid import UUID

CONTRACT_VERSION = "1.0.0"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
_OUTPUTS = frozenset({"predictions", "public_web_export", "metrics"})
_CLASSIFICATIONS = frozenset({"public", "private"})
_TIERS = frozenset({"public", "premium", "vip"})


class ContractError(ValueError):
    """Raised when a payload is invalid or incompatible with this contract."""


def _require_object(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ContractError(f"{name} must be an object")
    return value


def _fields(value: Mapping[str, Any], name: str, required: set[str], optional: set[str]) -> None:
    missing = required - value.keys()
    unknown = value.keys() - required - optional
    if missing:
        raise ContractError(f"{name} missing required fields: {', '.join(sorted(missing))}")
    if unknown:
        raise ContractError(f"{name} contains unsupported fields: {', '.join(sorted(unknown))}")


def _string(value: Any, name: str, *, nonempty: bool = True) -> str:
    if not isinstance(value, str) or (nonempty and not value.strip()):
        raise ContractError(f"{name} must be a {'non-empty ' if nonempty else ''}string")
    return value


def _utc(value: Any, name: str) -> str:
    text = _string(value, name)
    if "T" not in text or not (text.endswith("Z") or text.endswith("+00:00")):
        raise ContractError(f"{name} must use ISO-8601 UTC notation")
    try:
        stamp = datetime.fromisoformat(text[:-1] + "+00:00" if text.endswith("Z") else text)
    except ValueError as exc:
        raise ContractError(f"{name} must be an ISO-8601 timestamp") from exc
    if stamp.tzinfo is None or stamp.utcoffset() != timezone.utc.utcoffset(stamp):
        raise ContractError(f"{name} must have UTC timezone")
    return stamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _uuid(value: Any, name: str) -> str:
    text = _string(value, name)
    try:
        parsed = UUID(text)
    except ValueError as exc:
        raise ContractError(f"{name} must be a UUID") from exc
    if str(parsed) != text:
        raise ContractError(f"{name} must use canonical UUID format")
    return str(parsed)


def _string_tuple(value: Any, name: str, allowed: frozenset[str] | None = None) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise ContractError(f"{name} must be a non-empty array")
    items = tuple(_string(item, name) for item in value)
    if len(set(items)) != len(items):
        raise ContractError(f"{name} must not contain duplicates")
    if allowed is not None and not set(items) <= allowed:
        raise ContractError(f"{name} contains unsupported values")
    return items


def _json_mapping(value: Any, name: str) -> dict[str, Any]:
    mapping = dict(_require_object(value, name))
    if any(not isinstance(key, str) for key in mapping):
        raise ContractError(f"{name} keys must be strings")
    try:
        json.dumps(mapping, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ContractError(f"{name} must contain finite JSON values") from exc
    forbidden = {"token", "secret", "password", "credential", "authorization", "api_key"}

    def check_keys(item: Any) -> None:
        if isinstance(item, dict):
            for key, child in item.items():
                lowered = str(key).lower()
                if any(part in lowered for part in forbidden):
                    raise ContractError(f"{name} must not contain secret-bearing fields")
                check_keys(child)
        elif isinstance(item, list):
            for child in item:
                check_keys(child)

    check_keys(mapping)
    return mapping


@dataclass(frozen=True)
class InputArtifact:
    """Immutable reference to an input file; no filesystem path is shared."""

    name: str
    version: str
    sha256: str
    size_bytes: int
    classification: str

    @classmethod
    def from_dict(cls, raw: Any) -> "InputArtifact":
        value = _require_object(raw, "input_manifest item")
        fields = {"name", "version", "sha256", "size_bytes", "classification"}
        _fields(value, "input_manifest item", fields, set())
        name = _string(value["name"], "name")
        version = _string(value["version"], "version")
        if not _SEMVER.fullmatch(version):
            raise ContractError("artifact version must be semantic version text")
        digest = _string(value["sha256"], "sha256")
        if not _SHA256.fullmatch(digest):
            raise ContractError("sha256 must be 64 lowercase hexadecimal characters")
        size = value["size_bytes"]
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            raise ContractError("size_bytes must be a non-negative integer")
        classification = _string(value["classification"], "classification")
        if classification not in _CLASSIFICATIONS:
            raise ContractError("classification must be public or private")
        return cls(name, version, digest, size, classification)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "classification": self.classification,
        }


@dataclass(frozen=True)
class RunRequest:
    """Versioned, path-free request from orchestrator to private core."""

    run_id: str
    as_of_utc: str
    sport_scope: tuple[str, ...]
    window_start_utc: str
    window_end_utc: str
    input_manifest: tuple[InputArtifact, ...]
    parameters: Mapping[str, Any]
    requested_outputs: tuple[str, ...]
    contract_version: str = CONTRACT_VERSION

    @classmethod
    def from_dict(cls, raw: Any) -> "RunRequest":
        value = _require_object(raw, "RunRequest")
        required = {
            "contract_version", "run_id", "as_of_utc", "sport_scope",
            "window_start_utc", "window_end_utc", "input_manifest",
            "parameters", "requested_outputs",
        }
        _fields(value, "RunRequest", required, set())
        if value["contract_version"] != CONTRACT_VERSION:
            raise ContractError(f"unsupported contract_version: {value['contract_version']!r}")
        run_id = _uuid(value["run_id"], "run_id")
        as_of = _utc(value["as_of_utc"], "as_of_utc")
        start = _utc(value["window_start_utc"], "window_start_utc")
        end = _utc(value["window_end_utc"], "window_end_utc")
        if start > end:
            raise ContractError("window_start_utc must not be after window_end_utc")
        manifest_raw = value["input_manifest"]
        if not isinstance(manifest_raw, list):
            raise ContractError("input_manifest must be an array")
        manifest = tuple(InputArtifact.from_dict(item) for item in manifest_raw)
        if len({item.name for item in manifest}) != len(manifest):
            raise ContractError("input_manifest names must be unique")
        outputs = _string_tuple(value["requested_outputs"], "requested_outputs", _OUTPUTS)
        return cls(
            run_id=run_id,
            as_of_utc=as_of,
            sport_scope=_string_tuple(value["sport_scope"], "sport_scope"),
            window_start_utc=start,
            window_end_utc=end,
            input_manifest=manifest,
            parameters=_json_mapping(value["parameters"], "parameters"),
            requested_outputs=outputs,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "run_id": self.run_id,
            "as_of_utc": self.as_of_utc,
            "sport_scope": list(self.sport_scope),
            "window_start_utc": self.window_start_utc,
            "window_end_utc": self.window_end_utc,
            "input_manifest": [item.to_dict() for item in self.input_manifest],
            "parameters": dict(self.parameters),
            "requested_outputs": list(self.requested_outputs),
        }


@dataclass(frozen=True)
class PublicPrediction:
    """Allowlisted prediction fields that may be considered for publication."""

    event_id: str
    sport: str
    league: str
    market: str
    selection: str
    probability: float
    decimal_odds: float
    tier: str
    as_of_utc: str

    @classmethod
    def from_dict(cls, raw: Any) -> "PublicPrediction":
        value = _require_object(raw, "public_predictions item")
        fields = {
            "event_id", "sport", "league", "market", "selection",
            "probability", "decimal_odds", "tier", "as_of_utc",
        }
        _fields(value, "public_predictions item", fields, set())
        numbers: dict[str, float] = {}
        for name in ("probability", "decimal_odds"):
            number = value[name]
            if isinstance(number, bool) or not isinstance(number, (int, float)) or not math.isfinite(number):
                raise ContractError(f"{name} must be a finite number")
            numbers[name] = float(number)
        if not 0 <= numbers["probability"] <= 1:
            raise ContractError("probability must be between 0 and 1")
        if numbers["decimal_odds"] <= 1:
            raise ContractError("decimal_odds must be greater than 1")
        tier = _string(value["tier"], "tier")
        if tier not in _TIERS:
            raise ContractError("tier must be public, premium, or vip")
        return cls(
            event_id=_string(value["event_id"], "event_id"),
            sport=_string(value["sport"], "sport"),
            league=_string(value["league"], "league"),
            market=_string(value["market"], "market"),
            selection=_string(value["selection"], "selection"),
            probability=numbers["probability"],
            decimal_odds=numbers["decimal_odds"],
            tier=tier,
            as_of_utc=_utc(value["as_of_utc"], "as_of_utc"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "sport": self.sport,
            "league": self.league,
            "market": self.market,
            "selection": self.selection,
            "probability": self.probability,
            "decimal_odds": self.decimal_odds,
            "tier": self.tier,
            "as_of_utc": self.as_of_utc,
        }


@dataclass(frozen=True)
class RunResult:
    """Core result plus reproducibility metadata and public-output allowlist."""

    run_id: str
    status: str
    started_at_utc: str
    completed_at_utc: str
    core_version: str
    core_commit: str
    input_manifest: tuple[InputArtifact, ...]
    output_manifest: tuple[InputArtifact, ...]
    public_predictions: tuple[PublicPrediction, ...]
    warnings: tuple[str, ...]
    error_code: str | None = None
    contract_version: str = CONTRACT_VERSION

    @property
    def publishable(self) -> bool:
        """Partial/failed runs must not be published by the public orchestrator."""
        return self.status == "success"

    @classmethod
    def from_dict(cls, raw: Any) -> "RunResult":
        value = _require_object(raw, "RunResult")
        required = {
            "contract_version", "run_id", "status", "started_at_utc",
            "completed_at_utc", "core_version", "core_commit", "input_manifest",
            "output_manifest", "public_predictions", "warnings",
        }
        _fields(value, "RunResult", required, {"error_code"})
        if value["contract_version"] != CONTRACT_VERSION:
            raise ContractError(f"unsupported contract_version: {value['contract_version']!r}")
        status = _string(value["status"], "status")
        if status not in {"success", "partial", "failed"}:
            raise ContractError("status must be success, partial, or failed")
        started = _utc(value["started_at_utc"], "started_at_utc")
        completed = _utc(value["completed_at_utc"], "completed_at_utc")
        if started > completed:
            raise ContractError("completed_at_utc must not precede started_at_utc")
        version = _string(value["core_version"], "core_version")
        if not _SEMVER.fullmatch(version):
            raise ContractError("core_version must be semantic version text")
        commit = _string(value["core_commit"], "core_commit")
        if not _COMMIT.fullmatch(commit):
            raise ContractError("core_commit must be a full lowercase Git SHA")
        input_raw, output_raw = value["input_manifest"], value["output_manifest"]
        prediction_raw = value["public_predictions"]
        if not all(isinstance(items, list) for items in (input_raw, output_raw, prediction_raw)):
            raise ContractError("manifests and public_predictions must be arrays")
        warnings_raw = value["warnings"]
        if not isinstance(warnings_raw, list):
            raise ContractError("warnings must be an array")
        warnings = tuple(_string(item, "warnings item") for item in warnings_raw)
        error_code = value.get("error_code")
        if error_code is not None:
            error_code = _string(error_code, "error_code")
        predictions = tuple(PublicPrediction.from_dict(item) for item in prediction_raw)
        if status != "success" and predictions:
            raise ContractError("partial/failed results must not contain publishable predictions")
        input_manifest = tuple(InputArtifact.from_dict(item) for item in input_raw)
        output_manifest = tuple(InputArtifact.from_dict(item) for item in output_raw)
        if len({item.name for item in input_manifest}) != len(input_manifest):
            raise ContractError("input_manifest names must be unique")
        if len({item.name for item in output_manifest}) != len(output_manifest):
            raise ContractError("output_manifest names must be unique")
        return cls(
            run_id=_uuid(value["run_id"], "run_id"),
            status=status,
            started_at_utc=started,
            completed_at_utc=completed,
            core_version=version,
            core_commit=commit,
            input_manifest=input_manifest,
            output_manifest=output_manifest,
            public_predictions=predictions,
            warnings=warnings,
            error_code=error_code,
        )

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "contract_version": self.contract_version,
            "run_id": self.run_id,
            "status": self.status,
            "started_at_utc": self.started_at_utc,
            "completed_at_utc": self.completed_at_utc,
            "core_version": self.core_version,
            "core_commit": self.core_commit,
            "input_manifest": [item.to_dict() for item in self.input_manifest],
            "output_manifest": [item.to_dict() for item in self.output_manifest],
            "public_predictions": [item.to_dict() for item in self.public_predictions],
            "warnings": list(self.warnings),
        }
        if self.error_code is not None:
            result["error_code"] = self.error_code
        return result


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ContractError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(payload: str) -> Any:
    """Decode JSON while rejecting duplicate keys and non-standard NaN values."""
    try:
        return json.loads(
            payload,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=lambda value: (_ for _ in ()).throw(ContractError(f"invalid JSON number: {value}")),
        )
    except json.JSONDecodeError as exc:
        raise ContractError("invalid JSON") from exc


def dump_json(value: RunRequest | RunResult) -> str:
    """Serialize a DTO in deterministic compact UTF-8-compatible JSON."""
    if not isinstance(value, (RunRequest, RunResult)):
        raise ContractError("only RunRequest and RunResult can be serialized")
    # Validate again so direct dataclass construction cannot bypass the contract.
    validated = type(value).from_dict(value.to_dict())
    return json.dumps(validated.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def validate_result(
    request: RunRequest,
    result: RunResult,
    expected_core_commit: str | None = None,
) -> RunResult:
    """Bind a result to its request and optionally to the pinned core commit."""
    request = RunRequest.from_dict(request.to_dict())
    result = RunResult.from_dict(result.to_dict())
    if result.run_id != request.run_id:
        raise ContractError("result run_id does not match request")
    if result.input_manifest != request.input_manifest:
        raise ContractError("result input_manifest does not match request")
    if expected_core_commit is not None:
        if not _COMMIT.fullmatch(expected_core_commit):
            raise ContractError("expected_core_commit must be a full lowercase Git SHA")
        if result.core_commit != expected_core_commit:
            raise ContractError("result core_commit does not match pinned core commit")
    return result


def verify_artifact(path: str | Path, artifact: InputArtifact, chunk_size: int = 1024 * 1024) -> None:
    """Verify an artifact's byte length and SHA-256 before a consumer loads it."""
    if isinstance(chunk_size, bool) or not isinstance(chunk_size, int) or chunk_size <= 0:
        raise ContractError("chunk_size must be a positive integer")
    digest = hashlib.sha256()
    size = 0
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            size += len(chunk)
            digest.update(chunk)
    if size != artifact.size_bytes:
        raise ContractError("artifact size does not match manifest")
    if digest.hexdigest() != artifact.sha256:
        raise ContractError("artifact SHA-256 does not match manifest")

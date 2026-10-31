"""Allowlisted v1 DTO for the public static website export.

This preserves the existing JSON envelope for browser compatibility while
projecting each pick onto fields consumed by the public site. VIP-only player
and line data is served through the separately protected picks_vip table.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
import math
from typing import Any

from .v1 import ContractError

WEB_EXPORT_VERSION = "1.0.0"

PUBLIC_PICK_FIELDS = frozenset({
    "partido", "inicio", "fecha", "deporte", "liga", "apuesta", "cuota", "prob",
    "elige", "porque", "resultado_c1", "marcador", "espn", "logo_h", "logo_a",
    "girado", "premium", "tipo", "casa", "ventaja", "gratis", "ctx", "vip_hay",
    "estado", "id", "solo_analisis",
})

_CONTEXT_FIELDS = frozenset({"fl", "fv", "ul", "uv", "sl", "sv", "h2h", "bl", "bv"})
_STAT_FIELDS = frozenset({"n", "gf", "gc", "o25", "btts", "tir", "cor", "tap", "tar", "pos"})
_TEXT_FIELDS = frozenset({
    "partido", "inicio", "fecha", "deporte", "liga", "apuesta", "porque", "resultado_c1",
    "marcador", "espn", "logo_h", "logo_a", "tipo", "casa", "id",
})
_BOOL_FIELDS = frozenset({"elige", "girado", "premium", "gratis", "vip_hay", "solo_analisis"})
_NUMBER_FIELDS = frozenset({"cuota", "prob", "ventaja"})


def _utc_timestamp(value: Any, name: str, *, optional: bool = False) -> str | None:
    if value is None and optional:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{name} must be a non-empty UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    except ValueError as exc:
        raise ContractError(f"{name} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ContractError(f"{name} must use UTC timezone")
    return value


def _context(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ContractError("public pick ctx must be an object or null")
    result: dict[str, Any] = {}
    for key in _CONTEXT_FIELDS & value.keys():
        item = value[key]
        if key in {"sl", "sv"} and item is not None:
            if not isinstance(item, Mapping):
                raise ContractError(f"public pick ctx.{key} must be an object or null")
            result[key] = {name: stat for name, stat in item.items() if name in _STAT_FIELDS}
        elif key == "h2h" and item is not None:
            if not isinstance(item, list) or any(
                not isinstance(row, list) or len(row) != 4
                or any(not isinstance(cell, str) for cell in row)
                for row in item
            ):
                raise ContractError("public pick ctx.h2h must be an array of four-string rows")
            result[key] = item
        else:
            result[key] = item
    return result


def public_pick(value: Any) -> dict[str, Any]:
    """Return a JSON-safe public projection, rejecting malformed context."""
    if not isinstance(value, Mapping):
        raise ContractError("public pick must be an object")
    result = {key: item for key, item in value.items() if key in PUBLIC_PICK_FIELDS and key != "ctx"}
    for key in _TEXT_FIELDS & result.keys():
        if result[key] is not None and not isinstance(result[key], str):
            raise ContractError(f"public pick {key} must be a string or null")
    for key in _BOOL_FIELDS & result.keys():
        if key == "girado" and result[key] is None:
            continue
        if not isinstance(result[key], bool):
            raise ContractError(f"public pick {key} must be a boolean")
    for key in _NUMBER_FIELDS & result.keys():
        item = result[key]
        if item is not None and (isinstance(item, bool) or not isinstance(item, (int, float))
                                 or not math.isfinite(item)):
            raise ContractError(f"public pick {key} must be a finite number or null")
        if key == "prob" and item is not None and not 0 <= item <= 1:
            raise ContractError("public pick prob must be a fraction in [0, 1]")
    if "ctx" in value:
        result["ctx"] = _context(value["ctx"])
    return result


def public_export(value: Any) -> dict[str, Any]:
    """Project the legacy public envelope without changing its field names."""
    if not isinstance(value, Mapping):
        raise ContractError("public export must be an object")
    picks = value.get("picks")
    if not isinstance(picks, list):
        raise ContractError("public export picks must be an array")
    generado = _utc_timestamp(value.get("generado"), "public export generado")
    precalculo = _utc_timestamp(value.get("precalculo"), "public export precalculo", optional=True)
    return {
        "contract_version": WEB_EXPORT_VERSION,
        "generado": generado,
        "precalculo": precalculo,
        "picks": [public_pick(pick) for pick in picks],
    }


def public_analysis(value: Any) -> dict[str, Any]:
    """Project the legacy analysis envelope used by the public web client."""
    if not isinstance(value, Mapping):
        raise ContractError("public analysis must be an object")
    rows = value.get("analisis")
    if not isinstance(rows, list):
        raise ContractError("public analysis rows must be an array")
    return {
        "contract_version": WEB_EXPORT_VERSION,
        "generado": _utc_timestamp(value.get("generado"), "public analysis generado"),
        "analisis": [public_pick(row) for row in rows],
    }

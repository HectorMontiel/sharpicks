"""Allowlisted v1 DTO for the public static website export.

This preserves the existing JSON envelope for browser compatibility while
projecting each pick onto fields consumed by the public site. VIP-only player
and line data is served through the separately protected picks_vip table.
"""

from __future__ import annotations

from collections.abc import Mapping
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
    return {
        "contract_version": WEB_EXPORT_VERSION,
        "generado": value.get("generado"),
        "precalculo": value.get("precalculo"),
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
        "generado": value.get("generado"),
        "analisis": [public_pick(row) for row in rows],
    }

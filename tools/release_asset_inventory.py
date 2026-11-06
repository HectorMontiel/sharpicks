#!/usr/bin/env python3
"""Snapshot GitHub Release asset metadata without downloading assets."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
from collections import Counter
from typing import Any


def _asset_record(asset: dict[str, Any]) -> dict[str, Any]:
    name = str(asset["name"])
    lower = name.lower()
    candidates = ["review_required"]
    evidence = []
    if lower.startswith("modelos-") and lower.endswith((".tar.gz", ".tgz")):
        candidates.extend(["private_candidate", "generated_model_archive"])
        evidence.append("model archive name and extension")
    elif "modelo" in lower and lower.endswith(".json"):
        candidates.extend(["private_candidate", "model_registry_metadata"])
        evidence.append("model registry/manifest name")
    if not evidence:
        evidence.append("no specific asset-name rule matched")

    digest = asset.get("digest")
    return {
        "name": name,
        "size_bytes": int(asset["size"]),
        "content_type": asset.get("content_type"),
        "digest": digest if isinstance(digest, str) else None,
        "state": asset.get("state"),
        "created_at": asset.get("created_at"),
        "updated_at": asset.get("updated_at"),
        "download_count_at_snapshot": int(asset.get("download_count", 0)),
        "classification_candidates": sorted(candidates),
        "evidence": "; ".join(evidence),
        "decision_state": "review_required",
    }


def build_snapshot(
    payload: dict[str, Any], repository: str, checked_at: str | None = None
) -> dict[str, Any]:
    assets = [_asset_record(asset) for asset in payload.get("assets", [])]
    types = Counter(asset["content_type"] or "unknown" for asset in assets)
    return {
        "schema_version": 1,
        "repository": repository,
        "tag_name": payload.get("tag_name"),
        "release_name": payload.get("name"),
        "release_published_at": payload.get("published_at"),
        "checked_at": checked_at or datetime.now(timezone.utc).isoformat(),
        "method": "GitHub Release metadata through gh API; assets are not downloaded",
        "scope": "asset names and metadata only; archive contents, owners and consumers are not verified",
        "summary": {
            "asset_count": len(assets),
            "total_size_bytes": sum(asset["size_bytes"] for asset in assets),
            "assets_without_digest": sum(asset["digest"] is None for asset in assets),
            "content_type_counts": dict(sorted(types.items())),
        },
        "assets": assets,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", default="HectorMontiel/sharpicks")
    parser.add_argument("--tag", default="modelos-latest")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    endpoint = f"repos/{args.repository}/releases/tags/{args.tag}"
    try:
        proc = subprocess.run(
            ["gh", "api", endpoint],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
        )
        payload = json.loads(proc.stdout)
        data = build_snapshot(payload, args.repository)
        rendered = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8", newline="\n")
        else:
            sys.stdout.write(rendered)
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError, KeyError, ValueError) as exc:
        print(f"release inventory failed: {type(exc).__name__}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Classify tracked Git assets by path/metadata without reading file contents.

The output is a review queue, not an automated intellectual-property decision.
It includes every blob in a selected Git tree, even when sparse checkout omits
the worktree file. Release assets and untracked/ignored files are out of scope.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any


def _classify(path: str) -> tuple[list[str], str]:
    """Return heuristic classification candidates and their path evidence."""
    normalized = path.replace("\\", "/").lower()
    name = normalized.rsplit("/", 1)[-1]
    suffix = Path(name).suffix
    parts = set(normalized.split("/"))
    candidates: set[str] = {"review_required"}
    evidence: list[str] = []

    if name.startswith(".env") or suffix in {".pem", ".key", ".p12", ".pfx"} or re.search(
        r"(^|[._-])(secret|credential|private_key)([._-]|$)", name
    ):
        candidates.add("sensitive")
        evidence.append("secret-like filename or extension")

    if suffix in {".joblib", ".pkl", ".pickle", ".onnx", ".pt", ".pth", ".h5"} \
            or parts.intersection({"models", "modelos", "weights", "checkpoints"}):
        candidates.update({"private_candidate", "generated"})
        evidence.append("model artifact extension or directory")

    if suffix in {".csv", ".parquet", ".feather", ".jsonl", ".ndjson"} \
            or re.search(r"(^|[/_.-])(historico|history|snapshot|ledger|dataset|training)([/_.-]|$)", normalized):
        candidates.update({"historical", "private_candidate"})
        evidence.append("data/history extension or path marker")

    if parts.intersection({"contracts", "contract", "dtos", "schemas"}) \
            or "sharpicks_contracts" in parts:
        candidates.add("shareable_contract_candidate")
        evidence.append("contract/schema directory")

    if parts.intersection({"web", "public", "site", "website"}):
        candidates.add("public_candidate")
        evidence.append("presentation/public directory")

    if parts.intersection({"docs", "documentation", ".github"}) \
            or suffix in {".md", ".rst"}:
        candidates.add("public_candidate")
        evidence.append("documentation or workflow directory")

    if not evidence:
        evidence.append("no specific path rule matched")

    return sorted(candidates), "; ".join(evidence)


def _git_tree(root: Path, revision: str) -> list[dict[str, Any]]:
    """Read tracked blob metadata from Git; do not open worktree files."""
    proc = subprocess.run(
        ["git", "ls-tree", "-r", "-l", "-z", revision],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    rows: list[dict[str, Any]] = []
    for record in proc.stdout.split(b"\0"):
        if not record:
            continue
        header, raw_path = record.split(b"\t", 1)
        mode, object_type, oid, size = header.decode("ascii").split(" ", 3)
        if object_type != "blob":
            continue
        path = raw_path.decode("utf-8", errors="surrogateescape")
        candidates, evidence = _classify(path)
        rows.append({
            "path": path,
            "mode": mode,
            "git_blob_oid": oid,
            "size_bytes": int(size),
            "classification_candidates": candidates,
            "evidence": evidence,
            "decision_state": "review_required",
        })
    return rows


def build_inventory(root: Path, revision: str) -> dict[str, Any]:
    rows = _git_tree(root.resolve(), revision)
    totals = Counter(candidate for row in rows for candidate in row["classification_candidates"])
    return {
        "schema_version": 1,
        "revision": revision,
        "method": "Git tree metadata and path heuristics; file contents are not read",
        "scope": "tracked blobs in the selected Git tree; excludes release assets, untracked files, and Git history",
        "summary": {
            "tracked_blobs": len(rows),
            "tracked_bytes": sum(row["size_bytes"] for row in rows),
            "candidate_counts_including_overlaps": dict(sorted(totals.items())),
        },
        "assets": rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--revision", default="HEAD", help="Git tree-ish, default: HEAD")
    parser.add_argument("--output", type=Path, help="JSON destination; stdout when omitted")
    args = parser.parse_args(argv)
    try:
        data = build_inventory(args.root, args.revision)
        rendered = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8", newline="\n")
        else:
            sys.stdout.write(rendered)
    except (OSError, subprocess.CalledProcessError, ValueError) as exc:
        print(f"asset inventory failed: {type(exc).__name__}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

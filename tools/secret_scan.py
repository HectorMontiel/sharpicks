#!/usr/bin/env python3
"""Redacted, heuristic secret scan for the current working tree.

This is an interim detector, not a substitute for Gitleaks/TruffleHog or a
history-aware scan. Findings contain paths, line numbers and detector names;
matched values are never serialized.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable


DETECTORS = {
    "github_token": re.compile(rb"(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})"),
    "aws_access_key": re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
    "stripe_live_key": re.compile(rb"\b(?:sk|rk)_live_[A-Za-z0-9]{16,}\b"),
    "slack_token": re.compile(rb"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    "telegram_bot_token": re.compile(rb"\b[0-9]{8,10}:[A-Za-z0-9_-]{35,}\b"),
    "jwt": re.compile(rb"\beyJ[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{8,}\b"),
    "private_key_header": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "secret_assignment": re.compile(
        rb"(?i)\b(?:api[_-]?key|access[_-]?token|client[_-]?secret|password|passwd|secret)"
        rb"\b\s*[:=]\s*(?:[\"']([A-Za-z0-9/+=_.:-]{24,})[\"']|([A-Za-z0-9/+=_-]{24,}))"
    ),
}

IGNORED_DIRS = {
    ".git", ".hg", ".svn", ".venv", "venv", "node_modules", "__pycache__",
    ".mypy_cache", ".pytest_cache", ".ruff_cache",
}
IGNORED_SUFFIXES = {
    ".7z", ".bz2", ".dll", ".exe", ".gz", ".joblib", ".jpg", ".jpeg",
    ".pdf", ".png", ".so", ".tar", ".tgz", ".whl", ".zip",
}


def iter_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in IGNORED_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in IGNORED_SUFFIXES:
            continue
        yield path


def scan(root: Path) -> dict:
    root = root.resolve()
    hits: list[dict[str, object]] = []
    scanned_files = 0
    unreadable_files = 0
    for path in iter_files(root):
        rel = path.relative_to(root).as_posix()
        try:
            with path.open("rb") as stream:
                line_number = 0
                while line := stream.readline():
                    line_number += 1
                    if b"\0" in line:
                        break
                    for detector, pattern in DETECTORS.items():
                        if pattern.search(line):
                            hits.append({"path": rel, "line": line_number, "kind": detector})
            scanned_files += 1
        except OSError:
            unreadable_files += 1
    counts: dict[str, int] = {}
    for hit in hits:
        kind = str(hit["kind"])
        counts[kind] = counts.get(kind, 0) + 1
    return {
        "scope": "working_tree_only_heuristic",
        "scanned_files": scanned_files,
        "unreadable_files": unreadable_files,
        "finding_count": len(hits),
        "counts_by_detector": dict(sorted(counts.items())),
        "findings": hits,
        "values_redacted": True,
        "history_scanned": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path.cwd())
    args = parser.parse_args()
    print(json.dumps(scan(args.root), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

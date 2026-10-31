"""Authenticate and safely restore a v497 encrypted backup artifact locally."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from typing import BinaryIO


_SIGNATURE = re.compile(r"^[0-9a-f]{64}$")


def _hmac_key(passphrase: str) -> bytes:
    return hashlib.sha256(b"firma|" + passphrase.encode("utf-8")).digest()


def _verify_signature(archive: Path, signature: Path, passphrase: str) -> None:
    try:
        expected = signature.read_text(encoding="ascii").strip()
    except (OSError, UnicodeError) as exc:
        raise ValueError("backup signature is unavailable or malformed") from exc
    if not _SIGNATURE.fullmatch(expected):
        raise ValueError("backup signature is unavailable or malformed")
    digest = hmac.new(_hmac_key(passphrase), digestmod=hashlib.sha256)
    with archive.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    if not hmac.compare_digest(expected, digest.hexdigest()):
        raise ValueError("backup authentication failed")


def _member_path(member: tarfile.TarInfo) -> PurePosixPath:
    name = member.name
    path = PurePosixPath(name)
    if "\\" in name or path.is_absolute() or not path.parts or ".." in path.parts:
        raise ValueError("backup contains an unsafe path")
    if path.parts[0] != "respaldo":
        raise ValueError("backup contains an unexpected top-level path")
    if not (member.isdir() or member.isfile()):
        raise ValueError("backup contains a link or special file")
    return path


def _extract_stream(stream: BinaryIO, stage: Path) -> None:
    found_root = False
    with tarfile.open(fileobj=stream, mode="r|gz") as archive:
        for member in archive:
            relative = _member_path(member)
            destination = stage.joinpath(*relative.parts)
            if member.isdir():
                destination.mkdir(parents=True, exist_ok=True)
                if relative == PurePosixPath("respaldo"):
                    found_root = True
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            source = archive.extractfile(member)
            if source is None:
                raise ValueError("backup contains an unreadable file")
            with source, destination.open("xb") as output:
                shutil.copyfileobj(source, output)
            if relative.parts == ("respaldo",) or len(relative.parts) > 1:
                found_root = True
    if not found_root or not (stage / "respaldo").is_dir():
        raise ValueError("backup does not contain the expected respaldo directory")


def restore(archive: Path, signature: Path, destination: Path, passphrase: str) -> Path:
    """Verify HMAC before decrypting; extract only regular files into a new directory."""
    archive, signature, destination = archive.resolve(), signature.resolve(), destination.resolve()
    if not archive.is_file() or not signature.is_file():
        raise ValueError("backup archive or signature is unavailable")
    if destination.exists():
        raise ValueError("restore destination already exists")
    if not destination.parent.is_dir():
        raise ValueError("restore destination parent must exist")
    if not passphrase:
        raise ValueError("RESPALDO_CLAVE is required")

    _verify_signature(archive, signature, passphrase)
    stage = Path(tempfile.mkdtemp(prefix=".sharpicks-restore-", dir=destination.parent))
    try:
        environment = os.environ.copy()
        environment["RESPALDO_CLAVE"] = passphrase
        try:
            process = subprocess.Popen(
                ["openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2", "-iter", "200000",
                 "-salt", "-in", str(archive), "-pass", "env:RESPALDO_CLAVE"],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=environment,
            )
        except OSError as exc:
            raise RuntimeError("OpenSSL is required to decrypt this backup") from exc
        try:
            if process.stdout is None:
                raise RuntimeError("OpenSSL did not provide a decrypted stream")
            with process.stdout:
                _extract_stream(process.stdout, stage)
            if process.wait(timeout=60) != 0:
                raise RuntimeError("backup decryption failed")
        except BaseException:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            raise
        os.replace(stage / "respaldo", destination)
        return destination
    finally:
        shutil.rmtree(stage, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="encrypted .tgz.enc artifact")
    parser.add_argument("signature", type=Path, help="matching .tgz.enc.hmac sidecar")
    parser.add_argument("destination", type=Path, help="new, empty restore directory")
    args = parser.parse_args(argv)
    passphrase = os.environ.get("RESPALDO_CLAVE", "")
    try:
        restored = restore(args.archive, args.signature, args.destination, passphrase)
    except (OSError, ValueError, RuntimeError, tarfile.TarError, subprocess.SubprocessError):
        print("backup restore failed; no data was written to the requested destination", file=sys.stderr)
        return 1
    print(f"backup restored to {restored}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

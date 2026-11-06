import hashlib
import hmac
import io
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch

from tools.restore_backup_artifact import _hmac_key, restore


PASSPHRASE = "synthetic-test-passphrase-not-a-secret"


def tar_bytes(name="respaldo/picks.json", content=b"[]"):
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w:gz") as archive:
        info = tarfile.TarInfo(name)
        info.size = len(content)
        archive.addfile(info, io.BytesIO(content))
    return output.getvalue()


def write_signed_artifact(folder, encrypted=b"synthetic encrypted backup"):
    archive = Path(folder, "backup.tgz.enc")
    sidecar = Path(str(archive) + ".hmac")
    archive.write_bytes(encrypted)
    digest = hmac.new(_hmac_key(PASSPHRASE), encrypted, hashlib.sha256).hexdigest()
    sidecar.write_text(digest + "\n", encoding="ascii")
    return archive, sidecar


class FakeProcess:
    def __init__(self, payload):
        self.stdout = io.BytesIO(payload)
        self.returncode = 0

    def wait(self, timeout=None):
        return self.returncode

    def poll(self):
        return self.returncode


class BackupArtifactRestoreTests(unittest.TestCase):
    def test_bad_hmac_is_rejected_before_openssl_or_extraction(self):
        with tempfile.TemporaryDirectory() as temp:
            archive, signature = write_signed_artifact(temp)
            signature.write_text("0" * 64, encoding="ascii")
            destination = Path(temp, "restored")
            with patch("tools.restore_backup_artifact.subprocess.Popen") as popen:
                with self.assertRaisesRegex(ValueError, "authentication failed"):
                    restore(archive, signature, destination, PASSPHRASE)
            popen.assert_not_called()
            self.assertFalse(destination.exists())

    def test_traversal_member_is_rejected_and_destination_stays_absent(self):
        with tempfile.TemporaryDirectory() as temp:
            archive, signature = write_signed_artifact(temp)
            destination = Path(temp, "restored")
            with patch("tools.restore_backup_artifact.subprocess.Popen",
                       return_value=FakeProcess(tar_bytes("respaldo/../escape"))) as popen:
                with self.assertRaisesRegex(ValueError, "unsafe path"):
                    restore(archive, signature, destination, PASSPHRASE)
            self.assertEqual(popen.call_count, 1)
            self.assertFalse(destination.exists())
            self.assertFalse(Path(temp, "escape").exists())

    def test_symlink_member_is_rejected(self):
        payload = io.BytesIO()
        with tarfile.open(fileobj=payload, mode="w:gz") as archive:
            link = tarfile.TarInfo("respaldo/link")
            link.type = tarfile.SYMTYPE
            link.linkname = "../../outside"
            archive.addfile(link)
        with tempfile.TemporaryDirectory() as temp:
            encrypted, signature = write_signed_artifact(temp)
            with patch("tools.restore_backup_artifact.subprocess.Popen",
                       return_value=FakeProcess(payload.getvalue())):
                with self.assertRaisesRegex(ValueError, "link or special file"):
                    restore(encrypted, signature, Path(temp, "restored"), PASSPHRASE)

    @unittest.skipUnless(shutil.which("openssl"), "OpenSSL is not installed in this local environment")
    def test_legacy_openssl_artifact_restores_after_hmac_verification(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp, "source")
            (source / "respaldo").mkdir(parents=True)
            (source / "respaldo" / "picks.json").write_text('[{"id":"synthetic"}]', encoding="utf-8")
            plaintext = Path(temp, "backup.tgz")
            with tarfile.open(plaintext, "w:gz") as archive:
                archive.add(source / "respaldo", arcname="respaldo")
            encrypted = Path(temp, "backup.tgz.enc")
            environment = os.environ.copy()
            environment["RESPALDO_CLAVE"] = PASSPHRASE
            subprocess.run([
                "openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-iter", "200000", "-salt",
                "-in", str(plaintext), "-out", str(encrypted), "-pass", "env:RESPALDO_CLAVE",
            ], env=environment, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            archive, signature = write_signed_artifact(temp, encrypted.read_bytes())
            destination = Path(temp, "restored")

            result = restore(archive, signature, destination, PASSPHRASE)

            self.assertEqual(result, destination.resolve())
            self.assertEqual((destination / "picks.json").read_text(encoding="utf-8"), '[{"id":"synthetic"}]')
            self.assertTrue(archive.exists())


if __name__ == "__main__":
    unittest.main()

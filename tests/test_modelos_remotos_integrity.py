import hashlib
import io
import os
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch

import modelos_remotos as models


def _tar_bytes(name="modelo.json", body=b"{}", kind=tarfile.REGTYPE, linkname=""):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as archive:
        info = tarfile.TarInfo(name)
        info.type = kind
        info.linkname = linkname
        info.size = len(body) if kind == tarfile.REGTYPE else 0
        archive.addfile(info, io.BytesIO(body) if info.size else None)
    return buf.getvalue()


class _Response:
    status_code = 200

    def __init__(self, data, digest):
        self.data = data
        self.sharpicks_expected_digest = digest

    def iter_content(self, chunk_size):
        yield self.data


class RemoteModelIntegrityTests(unittest.TestCase):
    def test_read_only_core_token_takes_precedence(self):
        models._TOKEN.clear()
        try:
            with patch.dict(os.environ, {
                "CORE_MODELS_READ_TOKEN": "read-only",
                "GH_TOKEN": "workflow-token",
                "GITHUB_TOKEN": "default-token",
            }):
                self.assertEqual(models._token(), "read-only")
        finally:
            models._TOKEN.clear()

    def test_sha256_digest_is_strict_and_checked(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"asset")
            path = f.name
        try:
            correct = "sha256:" + hashlib.sha256(b"asset").hexdigest()
            self.assertTrue(models._verificar_sha256(path, correct))
            self.assertFalse(models._verificar_sha256(path, "sha256:" + "0" * 64))
            self.assertFalse(models._verificar_sha256(path, None))
            self.assertFalse(models._verificar_sha256(path, "sha1:" + "0" * 40))
        finally:
            os.unlink(path)

    def test_rejects_traversal_windows_absolute_symlink_and_special_files(self):
        for name in ("../escape", "nested/../../escape", "C:\\escape", "/escape"):
            with self.subTest(name=name):
                item = tarfile.TarInfo(name)
                with self.assertRaisesRegex(ValueError, "ruta insegura"):
                    models._validar_miembro_tar(item)
        symlink = tarfile.TarInfo("link")
        symlink.type = tarfile.SYMTYPE
        symlink.linkname = "../../outside"
        with self.assertRaisesRegex(ValueError, "enlace"):
            models._validar_miembro_tar(symlink)
        device = tarfile.TarInfo("device")
        device.type = tarfile.CHRTYPE
        with self.assertRaisesRegex(ValueError, "especial"):
            models._validar_miembro_tar(device)

    def test_download_rejects_digest_mismatch_without_installing(self):
        data = _tar_bytes()
        wrong_digest = "sha256:" + "0" * 64
        with tempfile.TemporaryDirectory() as root, \
                patch.object(models, "RAIZ", root), \
                patch.object(models, "_pedir_asset", return_value=_Response(data, wrong_digest)):
            self.assertFalse(models._descargar("test_liga"))
            self.assertFalse(Path(root, "test_liga").exists())

    def test_valid_digest_installs_regular_model_file(self):
        data = _tar_bytes(body=b'{"ready":true}')
        digest = "sha256:" + hashlib.sha256(data).hexdigest()
        with tempfile.TemporaryDirectory() as root, \
                patch.object(models, "RAIZ", root), \
                patch.object(models, "_pedir_asset", return_value=_Response(data, digest)):
            self.assertTrue(models._descargar("test_liga"))
            self.assertEqual(Path(root, "test_liga", "modelo.json").read_bytes(), b'{"ready":true}')

    def test_valid_digest_does_not_allow_symlink_tar_member(self):
        data = _tar_bytes("link", kind=tarfile.SYMTYPE, linkname="../../outside")
        digest = "sha256:" + hashlib.sha256(data).hexdigest()
        with tempfile.TemporaryDirectory() as root, \
                patch.object(models, "RAIZ", root), \
                patch.object(models, "_pedir_asset", return_value=_Response(data, digest)):
            self.assertFalse(models._descargar("test_liga"))
            self.assertFalse(Path(root, "test_liga").exists())

    def test_asset_download_uses_digest_from_release_api_metadata(self):
        digest = "sha256:" + "a" * 64
        metadata = Mock(status_code=200)
        metadata.json.return_value = {"assets": [{
            "name": "modelos-premier.tar.gz",
            "url": "https://api.github.com/assets/1",
            "digest": digest,
        }]}
        download = _Response(b"archive", digest)
        calls = []

        def fake_get(url, **kwargs):
            calls.append((url, kwargs))
            return metadata if "api.github.com/repos/" in url else download

        models._ASSETS.clear()
        try:
            with patch("requests.get", side_effect=fake_get), patch.object(models, "_token", return_value="read-token"):
                response = models._pedir_asset("premier")
            self.assertEqual(response.sharpicks_expected_digest, digest)
            self.assertEqual(len(calls), 2)
            self.assertIn("Bearer read-token", calls[0][1]["headers"]["Authorization"])
            self.assertEqual(calls[1][1]["headers"]["Accept"], "application/octet-stream")
        finally:
            models._ASSETS.clear()

    def test_asset_without_github_digest_is_not_downloaded(self):
        metadata = Mock(status_code=200)
        metadata.json.return_value = {"assets": [{
            "name": "modelos-premier.tar.gz",
            "url": "https://api.github.com/assets/1",
            "digest": None,
        }]}
        calls = []
        models._ASSETS.clear()
        try:
            with patch("requests.get", side_effect=lambda url, **kwargs: calls.append(url) or metadata), \
                    patch.object(models, "_token", return_value="read-token"):
                response = models._pedir_asset("premier")
            self.assertEqual(response.status_code, 422)
            self.assertEqual(len(calls), 1)
        finally:
            models._ASSETS.clear()


if __name__ == "__main__":
    unittest.main()

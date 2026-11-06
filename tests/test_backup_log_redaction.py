import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import respaldo_base


class Response:
    def __init__(self, status_code, payload=None, text=""):
        self.status_code = status_code
        self.ok = status_code < 400
        self.payload = payload
        self.text = text

    def json(self):
        return self.payload


class BackupErrorRedactionTests(unittest.TestCase):
    def test_backup_page_error_does_not_include_response_body(self):
        with patch("requests.get", return_value=Response(503, text="private database canary")):
            with self.assertRaisesRegex(RuntimeError, "picks: HTTP 503") as caught:
                respaldo_base.bajar("https://example.supabase.co", "fake-key", "picks")
        self.assertNotIn("private database canary", str(caught.exception))

    def test_auth_backup_error_does_not_include_response_body(self):
        with tempfile.TemporaryDirectory() as temp, \
             patch("respaldo_base.tablas", return_value=[]), \
             patch("requests.post", return_value=Response(500, text="private auth canary")):
            with self.assertRaisesRegex(RuntimeError, "respaldo_auth: HTTP 500") as caught:
                respaldo_base.respaldar("https://example.supabase.co", "fake-key", temp)
        self.assertNotIn("private auth canary", str(caught.exception))

    def test_restore_error_does_not_include_response_body(self):
        with tempfile.TemporaryDirectory() as temp:
            Path(temp, "picks.json").write_text('[{"id": 1}]', encoding="utf-8")
            with patch("requests.post", return_value=Response(400, text="private row canary")):
                with self.assertRaisesRegex(RuntimeError, "picks: HTTP 400") as caught:
                    respaldo_base.restaurar("https://example.supabase.co", "fake-key", temp)
        self.assertNotIn("private row canary", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
